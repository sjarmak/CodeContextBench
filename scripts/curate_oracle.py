#!/usr/bin/env python3
"""Oracle curation tool for MCP-unique benchmark tasks.

Uses the Sourcegraph search API to generate oracle_answer.json files.

Curation modes:
  deep      Multi-query NLS with rev-pinning, min-hits threshold, content
            validation, tier annotation, and LLM query expansion (default)
  nls       Single NLS query with rev-pinning and tier annotation
  keyword   Legacy plain keyword search (fastest, most gameable)

"deep" mode mitigations against tool-affinity bias:
  1. LLM query expansion — Claude generates N semantically diverse queries
     from the seed_prompt so no single keyword_search call recovers the oracle
  2. patternType:keyword (NLS) — linguistic matching instead of exact string
  3. rev-pinning — every query carries `rev:<ref>` from the fixture revision
  4. min-hits threshold — file must appear in >= K of N queries to be included
  5. Content validation — line_matches data classifies hits as definition /
     usage / comment / string; only code-context hits qualify as "required"
  6. Two-tier annotation — oracle files tagged "required" (defines concept) or
     "sufficient" (references/tests it); drives weighted F1 in oracle_checks.py
  7. curation_queries field — explicit query list in task_spec overrides all
     generation; decouples curator intent from agent-visible search_pattern

Note: LLM-powered Cody Deep Search (mcp__sourcegraph__deepsearch) is not
available via HTTP. Use the MCP batch agent approach for that capability.

Reads:  task_spec.json + repo-set fixture
Writes: oracle_answer.json, oracle_curation_log.json

Environment variables:
    SOURCEGRAPH_URL          SG instance URL (default: https://sourcegraph.sourcegraph.com)
    SOURCEGRAPH_ACCESS_TOKEN SG API token
    SRC_ENDPOINT             Fallback for SOURCEGRAPH_URL
    SRC_ACCESS_TOKEN         Fallback for SOURCEGRAPH_ACCESS_TOKEN
    ANTHROPIC_API_KEY        Enables LLM query expansion (optional)

Usage:
    python3 scripts/curate_oracle.py --task-dir benchmarks/ccb_mcp_incident/ccx-incident-142
    python3 scripts/curate_oracle.py --task-dir <dir> --mode deep --num-runs 4 --min-hits 2
    python3 scripts/curate_oracle.py --task-dir <dir> --mode keyword  # legacy
    python3 scripts/curate_oracle.py --task-dir <dir> --no-llm        # skip LLM expansion
    python3 scripts/curate_oracle.py --task-dir <dir> --dry-run       # plan without calling APIs
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import anthropic as _anthropic_mod
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


# ---------------------------------------------------------------------------
# Line-context classification
# ---------------------------------------------------------------------------

_COMMENT_PREFIXES = ("//", "#", "--", "/*", "*", "<!--", "!", ";;", "%")

_DEFINITION_PATTERNS = [
    re.compile(r"^\s*(func|def|class|interface|struct|type|enum|trait|impl|fn)\s+\w"),
    re.compile(r"^\s*(public|private|protected|static|final|abstract|override)\s+.*\w+\s*\("),
    re.compile(r"^\s*[A-Z]\w+\s*[=:{(]"),          # UpperCamelCase assignment/def
    re.compile(r"^\s*(const|val|var|let)\s+[A-Z]"), # const/val uppercase
    re.compile(r"\bfunc\b[^(]*\(.*\).*\{$"),        # Go func signature
]

_TEST_PATH_PARTS = ("_test.", "test_", "/test/", "/tests/", "mock", "stub",
                    "fixture", "example", "spec.", "fake", "dummy")


def _classify_line_context(preview: str) -> str:
    """Return 'comment', 'string', or 'code' for a line of source text."""
    stripped = preview.strip()
    for prefix in _COMMENT_PREFIXES:
        if stripped.startswith(prefix):
            return "comment"
    # Simple string-assignment heuristic: entire RHS is a quoted value
    if re.match(r'^[a-zA-Z_]\w*\s*[=:]\s*["\']', stripped):
        return "string"
    return "code"


def _infer_file_tier(path: str, line_matches: List[Dict]) -> str:
    """Classify a matched file as 'required' (defines concept) or 'sufficient'.

    Rules:
      - Test / mock / fixture paths → always 'sufficient'
      - All line matches in comments or string literals → 'sufficient'
      - Any line match that looks like a definition in code context → 'required'
      - Otherwise (usage in code context) → 'sufficient'
    """
    path_lower = path.lower()
    if any(part in path_lower for part in _TEST_PATH_PARTS):
        return "sufficient"

    if not line_matches:
        return "sufficient"

    for match in line_matches:
        ctx = _classify_line_context(match.get("preview", ""))
        if ctx == "code":
            preview = match.get("preview", "")
            for pat in _DEFINITION_PATTERNS:
                if pat.search(preview):
                    return "required"
            # Usage in code (not a definition) → keep looking
    # Reached here: either no code-context hits, or only usage hits
    # Promote to required if any code hit exists (usage still matters)
    has_code = any(_classify_line_context(m.get("preview", "")) == "code" for m in line_matches)
    return "required" if has_code else "sufficient"


# ---------------------------------------------------------------------------
# Sourcegraph API client (stdlib-only: urllib)
# ---------------------------------------------------------------------------

class SourcegraphClient:
    """Thin wrapper around the Sourcegraph GraphQL search API."""

    DEFAULT_URL = "https://sourcegraph.sourcegraph.com"
    GRAPHQL_PATH = "/.api/graphql"

    def __init__(self, url: str, token: str, verbose: bool = False):
        self.url = url.rstrip("/")
        self.token = token
        self.verbose = verbose
        self.queries_made = 0
        self._request_log: List[Dict] = []
        self._rate_limit_delay = 1.0

    def graphql(self, query: str, variables: Optional[Dict] = None, timeout: int = 30) -> Dict:
        """Execute a GraphQL query with retry/backoff."""
        endpoint = f"{self.url}{self.GRAPHQL_PATH}"
        payload = json.dumps({"query": query, "variables": variables or {}}).encode()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"token {self.token}",
        }
        req = urllib.request.Request(endpoint, data=payload, headers=headers, method="POST")

        if self.queries_made > 0:
            time.sleep(self._rate_limit_delay)
        self.queries_made += 1

        log_entry: Dict[str, Any] = {
            "query_index": self.queries_made,
            "variables": variables or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        last_exc: Optional[Exception] = None
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = json.loads(resp.read())
                if "errors" in data and data["errors"]:
                    logging.warning("GraphQL errors: %s", data["errors"])
                result = data.get("data", {})
                log_entry["status"] = "ok"
                self._request_log.append(log_entry)
                return result
            except urllib.error.HTTPError as exc:
                last_exc = exc
                if exc.code == 429:
                    wait = min(2 ** (attempt + 1), 120)
                    logging.warning("Rate limited (429), waiting %ds", wait)
                    time.sleep(wait)
                else:
                    logging.error("HTTP %d from SG API", exc.code)
                    break
            except urllib.error.URLError as exc:
                last_exc = exc
                logging.warning("URLError (attempt %d): %s", attempt, exc)
                time.sleep(1)

        log_entry["status"] = "error"
        log_entry["error"] = str(last_exc)
        self._request_log.append(log_entry)
        return {}

    def search_files(self, sg_query: str, max_results: int = 200, mode: str = "deep") -> List[Dict]:
        """Return list of {repo, path, line_matches} from a file search.

        mode="deep" or "nls": appends patternType:keyword for NLS matching.
        mode="keyword": plain SG search.
        """
        gql = """
        query CurateFiles($query: String!) {
          search(query: $query, version: V2) {
            results {
              results {
                ... on FileMatch {
                  repository { name }
                  file { path }
                  lineMatches { lineNumber preview }
                }
              }
            }
          }
        }
        """
        full_query = f"{sg_query} count:{max_results}"
        if mode in ("deep", "nls"):
            full_query += " patternType:keyword"

        resp = self.graphql(gql, {"query": full_query})
        items = []
        for r in (resp.get("search") or {}).get("results", {}).get("results", []):
            repo = (r.get("repository") or {}).get("name", "")
            path = (r.get("file") or {}).get("path", "")
            if repo and path:
                items.append({
                    "repo": repo,
                    "path": path,
                    "line_matches": r.get("lineMatches", []),
                })
        return items

    def search_symbols(self, sg_query: str, max_results: int = 100) -> List[Dict]:
        """Return list of {repo, path, symbol, kind} from a symbol search."""
        gql = """
        query CurateSymbols($query: String!) {
          search(query: $query, version: V2) {
            results {
              results {
                ... on FileMatch {
                  repository { name }
                  file { path }
                  symbols {
                    name
                    kind
                    location {
                      resource { path }
                      range { start { line character } }
                    }
                  }
                }
              }
            }
          }
        }
        """
        full_query = f"type:symbol {sg_query} count:{max_results}"
        resp = self.graphql(gql, {"query": full_query})
        symbols = []
        for r in (resp.get("search") or {}).get("results", {}).get("results", []):
            repo = (r.get("repository") or {}).get("name", "")
            path = (r.get("file") or {}).get("path", "")
            for sym in r.get("symbols", []):
                symbols.append({
                    "repo": repo,
                    "path": path,
                    "symbol": sym.get("name", ""),
                    "kind": sym.get("kind", ""),
                    "line": (sym.get("location") or {}).get("range", {}).get("start", {}).get("line", 0),
                })
        return symbols

    def get_request_log(self) -> List[Dict]:
        return list(self._request_log)


# ---------------------------------------------------------------------------
# Fixture loading
# ---------------------------------------------------------------------------

def _find_project_root(start: Path) -> Path:
    for root_candidate in [start.resolve(), Path.cwd().resolve()]:
        current = root_candidate
        for _ in range(10):
            if (current / "fixtures").is_dir() or (current / "benchmarks").is_dir():
                return current
            current = current.parent
    return start.resolve()


def load_fixture(repo_set_id: str, project_root: Path) -> Optional[Dict]:
    fixture_path = project_root / "fixtures" / "repo_sets" / f"{repo_set_id}.json"
    if not fixture_path.exists():
        logging.error("Fixture not found: %s", fixture_path)
        return None
    with open(fixture_path) as f:
        return json.load(f)


def get_repos_from_fixture(fixture: Dict) -> List[str]:
    return [r.get("full_name", "") for r in fixture.get("repos", []) if r.get("full_name")]


def get_repos_with_revisions(fixture: Dict) -> List[Tuple[str, str]]:
    """Return (full_name, revision) pairs. revision may be hash, tag, or 'HEAD'."""
    return [
        (r.get("full_name", ""), r.get("revision", "HEAD"))
        for r in fixture.get("repos", [])
        if r.get("full_name")
    ]


def _repo_sg_name(full_name: str) -> str:
    if full_name.startswith("github.com/"):
        return full_name
    return f"github.com/{full_name}"


# ---------------------------------------------------------------------------
# Query generation
# ---------------------------------------------------------------------------

def generate_query_variations(
    search_pattern: str, seed_prompt: str = "", num_runs: int = 3
) -> List[str]:
    """Generate diverse query formulations by splitting the search_pattern and
    mining CamelCase identifiers from seed_prompt. Used as fallback when LLM
    expansion is unavailable or disabled.
    """
    variations: List[str] = [search_pattern]

    raw_terms = re.split(r"\s+OR\s+|\s+AND\s+", search_pattern, flags=re.IGNORECASE)
    for term in raw_terms:
        term = term.strip().strip("\"'")
        if term and term != search_pattern and term not in variations:
            variations.append(term)
        if len(variations) >= num_runs:
            return variations[:num_runs]

    if seed_prompt and len(variations) < num_runs:
        technical = re.findall(
            r"\b(?:[A-Z][a-z]+(?:[A-Z][a-z]+)+|[a-z]+(?:[A-Z][a-z]+)+)\b", seed_prompt
        )
        seen_lower = {v.lower() for v in variations}
        for term in technical:
            if term.lower() not in seen_lower:
                variations.append(term)
                seen_lower.add(term.lower())
            if len(variations) >= num_runs:
                break

    return variations[:num_runs]


def expand_queries_via_llm(
    seed_prompt: str,
    search_pattern: str,
    num_runs: int,
    api_key: Optional[str] = None,
) -> List[str]:
    """Use Claude Haiku to generate semantically diverse SG keyword queries.

    Each query targets a different aspect of the concept (definition, config,
    error handling, related types) so no single keyword_search call can replay
    the full oracle. Returns [] on any failure so callers can fall back.
    """
    if not HAS_ANTHROPIC:
        logging.debug("anthropic package not installed — skipping LLM expansion")
        return []

    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        logging.debug("ANTHROPIC_API_KEY not set — skipping LLM expansion")
        return []

    prompt = (
        f"Generate {num_runs} semantically diverse Sourcegraph keyword search queries "
        f"to find source code files relevant to this task.\n\n"
        f"Task description: {seed_prompt}\n"
        f"Base search pattern: {search_pattern}\n\n"
        f"Requirements:\n"
        f"- Each query must target a DIFFERENT ASPECT: e.g. the definition, the config, "
        f"the error path, related types, test helpers\n"
        f"- Use short technical identifiers that appear in source code, not prose\n"
        f"- Do not repeat terms across queries\n"
        f"- Avoid overly broad single words (prefer compound identifiers)\n\n"
        f"Return ONLY a JSON array of {num_runs} query strings, e.g.:\n"
        f'["HeartbeatTimeout", "sessionTimeoutExpired", "heartbeatInterval config"]'
    )

    try:
        client = _anthropic_mod.Anthropic(api_key=key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text.strip()
        m = re.search(r"\[.*?\]", text, re.DOTALL)
        if m:
            queries = json.loads(m.group())
            if isinstance(queries, list) and all(isinstance(q, str) for q in queries):
                logging.info("LLM expansion: %s", queries)
                return [q for q in queries if q.strip()][:num_runs]
    except Exception as exc:
        logging.warning("LLM query expansion failed: %s", exc)

    return []


def get_curation_queries(
    params: Dict,
    seed_prompt: str,
    num_runs: int,
    use_llm: bool = True,
    api_key: Optional[str] = None,
) -> Tuple[List[str], str]:
    """Return (queries, source) where source describes how queries were obtained.

    Priority:
      1. params["curation_queries"] — explicit override in task_spec (decoupled)
      2. LLM expansion via Claude — when use_llm=True and key available
      3. Pattern-based variation — CamelCase mining + OR-splitting (fallback)
    """
    # 1. Explicit curation_queries in task spec
    explicit = params.get("curation_queries", [])
    if explicit:
        return list(explicit)[:num_runs], "task_spec_curation_queries"

    search_pattern = params.get("search_pattern", "")
    seed = seed_prompt or ""

    # 2. LLM expansion
    if use_llm:
        llm_queries = expand_queries_via_llm(seed, search_pattern, num_runs, api_key)
        if llm_queries:
            # Always include the original pattern as run 0
            if search_pattern and search_pattern not in llm_queries:
                llm_queries = [search_pattern] + llm_queries
            return llm_queries[:num_runs], "llm_expanded"

    # 3. Pattern-based fallback
    return generate_query_variations(search_pattern, seed, num_runs), "pattern_variation"


# ---------------------------------------------------------------------------
# Oracle quality gate
# ---------------------------------------------------------------------------

def validate_oracle_quality(
    oracle_files: List[Dict],
    search_pattern: str,
    repos: List[str],
    log: List[Dict],
) -> None:
    """Emit structured warnings when the oracle looks over-populated or weak.

    Does NOT block curation — warnings are logged and recorded in the log for
    downstream review. Tasks with warnings should be manually re-curated with
    more specific patterns or explicit curation_queries.
    """
    n_files = len(oracle_files)
    n_repos = max(len(repos), 1)
    n_terms = len(re.split(r"\s+OR\s+|\s+AND\s+", search_pattern, flags=re.IGNORECASE)) if search_pattern else 0
    required_count = sum(1 for f in oracle_files if f.get("tier") == "required")
    sufficient_count = n_files - required_count

    warnings = []

    if n_files > 15:
        warnings.append(
            f"large oracle: {n_files} files (threshold 15) — consider tightening search_pattern "
            f"or adding explicit curation_queries"
        )

    if n_terms <= 1 and n_files > 0 and (n_files / n_repos) > 5:
        warnings.append(
            f"single-term pattern {search_pattern!r} returned {n_files / n_repos:.1f} files/repo "
            f"— high risk of over-population; add more specific terms"
        )

    if n_files > 5 and required_count == 0:
        warnings.append(
            "no 'required' tier files — all files classified as 'sufficient'; "
            "oracle may lack definition-level anchors"
        )

    if required_count > 0 and sufficient_count > required_count * 4:
        warnings.append(
            f"tier imbalance: {required_count} required vs {sufficient_count} sufficient "
            f"— sufficient files may be diluting weighted F1"
        )

    for w in warnings:
        logging.warning("ORACLE QUALITY: %s", w)

    log.append({
        "event": "oracle_quality_gate",
        "n_files": n_files,
        "n_repos": n_repos,
        "n_terms": n_terms,
        "required_count": required_count,
        "sufficient_count": sufficient_count,
        "warnings": warnings,
    })


# ---------------------------------------------------------------------------
# Oracle curation strategies
# ---------------------------------------------------------------------------

def curate_file_set_match(
    client: SourcegraphClient,
    check_params: Dict,
    repos: List[str],
    log: List[Dict],
    mode: str = "deep",
    num_runs: int = 3,
    min_hits: int = 2,
    seed_prompt: str = "",
    repos_with_revisions: Optional[List[Tuple[str, str]]] = None,
    use_llm: bool = True,
    api_key: Optional[str] = None,
) -> List[Dict]:
    """Search repos for files matching a pattern.

    Returns oracle file dicts with {"repo", "path", "tier"}.

    In "deep" / "nls" mode:
      - Uses get_curation_queries (LLM → pattern fallback) to build N queries
      - Pins each query to the repo's revision via `rev:<ref>`
      - Aggregates line_matches across all runs per file
      - Annotates tier via _infer_file_tier using aggregated line_matches
      - Returns only files found in >= min_hits queries

    In "keyword" mode (legacy):
      - Single query per repo, no rev-pinning, tier still annotated
    """
    search_pattern = check_params.get("search_pattern", "")
    file_filter = check_params.get("file_filter", "")

    if not search_pattern and not check_params.get("curation_queries"):
        logging.warning("file_set_match: no search_pattern or curation_queries — skipping")
        return []

    rev_map: Dict[str, str] = dict(repos_with_revisions) if repos_with_revisions else {}

    if mode == "keyword":
        oracle_files: List[Dict] = []
        seen: set = set()
        for repo in repos:
            sg_repo = _repo_sg_name(repo)
            query = f"repo:^{sg_repo}$ {search_pattern}"
            if file_filter:
                query += f" file:{file_filter}"
            log.append({"type": "file_set_match", "repo": repo, "query": query, "mode": mode})
            results = client.search_files(query, mode=mode)
            logging.info("  %s: %d file matches", repo, len(results))
            for r in results:
                key = (r["repo"], r["path"])
                if key not in seen:
                    seen.add(key)
                    tier = _infer_file_tier(r["path"], r.get("line_matches", []))
                    oracle_files.append({"repo": r["repo"], "path": r["path"], "tier": tier})
        return oracle_files

    # Deep / NLS: multi-query with rev-pinning, aggregation, and min-hits
    queries, query_source = get_curation_queries(
        check_params, seed_prompt, num_runs, use_llm=use_llm, api_key=api_key
    )
    log.append({
        "event": "query_plan",
        "search_pattern": search_pattern,
        "query_source": query_source,
        "queries": queries,
        "num_runs": len(queries),
        "min_hits": min_hits,
        "mode": mode,
    })

    # Aggregate: {(repo, path): {"hits": int, "line_matches": List}}
    file_data: Dict[Tuple[str, str], Dict] = {}

    for repo in repos:
        sg_repo = _repo_sg_name(repo)
        rev = rev_map.get(repo, "HEAD")
        rev_clause = "" if rev == "HEAD" else f" rev:{rev}"

        for run_i, query_term in enumerate(queries):
            query = f"repo:^{sg_repo}${rev_clause} {query_term}"
            if file_filter:
                query += f" file:{file_filter}"

            log.append({
                "type": "file_set_match",
                "repo": repo,
                "revision": rev,
                "query": query,
                "run": run_i,
                "query_term": query_term,
                "mode": mode,
            })
            results = client.search_files(query, mode=mode)
            logging.info(
                "  %s rev=%s run %d/%d [%s]: %d matches",
                repo, rev, run_i + 1, len(queries), query_term[:50], len(results),
            )
            for r in results:
                key = (r["repo"], r["path"])
                if key not in file_data:
                    file_data[key] = {"hits": 0, "line_matches": []}
                file_data[key]["hits"] += 1
                file_data[key]["line_matches"].extend(r.get("line_matches", []))

    effective_min = min(min_hits, len(queries))
    oracle_files = []
    for (repo, path), data in sorted(file_data.items()):
        if data["hits"] >= effective_min:
            tier = _infer_file_tier(path, data["line_matches"])
            oracle_files.append({"repo": repo, "path": path, "tier": tier})

    log.append({
        "event": "multiquery_complete",
        "query_source": query_source,
        "total_candidates": len(file_data),
        "passing_min_hits": len(oracle_files),
        "min_hits_threshold": effective_min,
        "num_queries": len(queries),
        "repos_searched": repos,
    })

    return oracle_files


def curate_symbol_resolution(
    client: SourcegraphClient,
    check_params: Dict,
    repos: List[str],
    log: List[Dict],
) -> List[Dict]:
    symbol_pattern = check_params.get("symbol_name", check_params.get("search_pattern", ""))
    kind_filter = check_params.get("kind_filter", "")

    if not symbol_pattern:
        logging.warning("symbol_resolution: no symbol_name/search_pattern — skipping")
        return []

    oracle_symbols: List[Dict] = []
    seen: set = set()

    for repo in repos:
        sg_repo = _repo_sg_name(repo)
        query = f"repo:^{sg_repo}$ {symbol_pattern}"
        if kind_filter:
            query += " type:symbol"
        log.append({"type": "symbol_resolution", "repo": repo, "query": query})
        results = client.search_symbols(query)
        logging.info("  %s: %d symbol matches", repo, len(results))
        for sym in results:
            key = (sym["repo"], sym["path"], sym["symbol"])
            if key not in seen:
                seen.add(key)
                oracle_symbols.append({
                    "repo": sym["repo"],
                    "path": sym["path"],
                    "symbol": sym["symbol"],
                    "kind": sym.get("kind", ""),
                })

    return oracle_symbols


def curate_dependency_chain(
    client: SourcegraphClient,
    check_params: Dict,
    repos: List[str],
    log: List[Dict],
) -> List[Dict]:
    chain_steps = check_params.get("chain_steps", [])
    if not chain_steps:
        logging.warning("dependency_chain: no chain_steps — skipping")
        return []

    chain: List[Dict] = []
    for step in chain_steps:
        pattern = step.get("search_pattern", "")
        repo_hint = step.get("repo_hint", "")
        symbol_hint = step.get("symbol_hint", "")
        search_repos = [repo_hint] if repo_hint else repos
        for repo in search_repos:
            sg_repo = _repo_sg_name(repo)
            query = f"repo:^{sg_repo}$ {pattern}"
            log.append({"type": "dependency_chain_step", "repo": repo, "query": query})
            results = client.search_files(query)
            if results:
                r = results[0]
                chain.append({"repo": r["repo"], "path": r["path"], "symbol": symbol_hint or pattern})
                break

    return chain


def curate_provenance(check_params: Dict, repos: List[str], oracle_files: List[Dict]) -> Dict:
    must_cite_paths = check_params.get("must_cite_paths", [])
    must_cite_repos = check_params.get("must_cite_repos", [])
    if not must_cite_paths and oracle_files:
        must_cite_paths = [f["path"] for f in oracle_files[:5]]
    if not must_cite_repos and repos:
        must_cite_repos = repos[:3]
    return {"must_cite_paths": must_cite_paths, "must_cite_repos": must_cite_repos}


def curate_keyword_presence(check_params: Dict) -> List[str]:
    return check_params.get("required_keywords", [])


# ---------------------------------------------------------------------------
# Main curation orchestrator
# ---------------------------------------------------------------------------

def curate_oracle(
    task_spec: Dict,
    client: SourcegraphClient,
    fixture: Optional[Dict],
    project_root: Path,
    mode: str = "deep",
    num_runs: int = 3,
    min_hits: int = 2,
    use_llm: bool = True,
    api_key: Optional[str] = None,
    verbose: bool = False,
) -> Tuple[Dict, List[Dict]]:
    """Curate oracle_answer.json content by searching SG for each check type."""
    log: List[Dict] = []
    oracle_answer: Dict[str, Any] = {}

    oracle_def = task_spec.get("artifacts", {}).get("oracle", {})
    eval_checks = task_spec.get("evaluation", {}).get("checks", [])
    seed_prompt = task_spec.get("prd", {}).get("seed_prompt", "")

    repos: List[str] = []
    repos_with_revisions: List[Tuple[str, str]] = []
    if fixture:
        repos = get_repos_from_fixture(fixture)
        repos_with_revisions = get_repos_with_revisions(fixture)
        log.append({
            "event": "repos_from_fixture",
            "repos": repos,
            "revisions": dict(repos_with_revisions),
        })
    else:
        logging.warning("No fixture loaded")

    all_oracle_files: List[Dict] = list(oracle_def.get("required_files", []))
    all_oracle_symbols: List[Dict] = list(oracle_def.get("required_symbols", []))
    all_chains: List[Dict] = list(oracle_def.get("dependency_chains", []))

    for check in eval_checks:
        check_type = check.get("type", "")
        params = check.get("params", {})
        logging.info("Curating check: %s", check_type)

        if check_type == "file_set_match" and repos:
            new_files = curate_file_set_match(
                client=client,
                check_params=params,
                repos=repos,
                log=log,
                mode=mode,
                num_runs=num_runs,
                min_hits=min_hits,
                seed_prompt=seed_prompt,
                repos_with_revisions=repos_with_revisions,
                use_llm=use_llm,
                api_key=api_key,
            )
            seen = {(f["repo"], f["path"]) for f in all_oracle_files}
            for f in new_files:
                key = (f["repo"], f["path"])
                if key not in seen:
                    all_oracle_files.append(f)
                    seen.add(key)
            log.append({
                "event": "file_set_match_complete",
                "new_items": len(new_files),
                "total_items": len(all_oracle_files),
            })
            # Quality gate — runs after tier annotation is available
            validate_oracle_quality(all_oracle_files, params.get("search_pattern", ""), repos, log)

        elif check_type == "symbol_resolution" and repos:
            new_syms = curate_symbol_resolution(client, params, repos, log)
            seen_sym = {(s["repo"], s["path"], s["symbol"]) for s in all_oracle_symbols}
            for s in new_syms:
                key = (s["repo"], s["path"], s["symbol"])
                if key not in seen_sym:
                    all_oracle_symbols.append(s)
                    seen_sym.add(key)
            log.append({
                "event": "symbol_resolution_complete",
                "new_items": len(new_syms),
                "total_items": len(all_oracle_symbols),
            })

        elif check_type == "dependency_chain" and repos:
            chain_steps = curate_dependency_chain(client, params, repos, log)
            if chain_steps:
                chain_id = params.get("chain_id", f"chain_{len(all_chains)}")
                all_chains.append({"chain_id": chain_id, "steps": chain_steps})
            log.append({"event": "dependency_chain_complete", "steps_found": len(chain_steps)})

        elif check_type == "provenance":
            prov = curate_provenance(params, repos, all_oracle_files)
            oracle_answer["provenance"] = prov
            log.append({"event": "provenance_oracle", "result": prov})

        elif check_type == "keyword_presence":
            kws = curate_keyword_presence(params)
            oracle_answer["required_keywords"] = kws
            log.append({"event": "keyword_presence_oracle", "keywords": kws})

        elif check_type in ("json_schema_match", "test_ratio"):
            log.append({"event": f"{check_type}_no_curation_needed"})

        else:
            logging.warning("Unknown or uncuratable check type: %s", check_type)

    if all_oracle_files:
        oracle_answer["files"] = all_oracle_files
    if all_oracle_symbols:
        oracle_answer["symbols"] = all_oracle_symbols
    else:
        oracle_answer["symbols"] = []
    if all_chains:
        oracle_answer["chains"] = all_chains
        if len(all_chains) == 1:
            oracle_answer["chain"] = all_chains[0]["steps"]

    text_parts = [f"{f['repo']} at {f['path']}" for f in all_oracle_files[:10]]
    text_parts += [f"{s['symbol']} in {s['repo']}/{s['path']}" for s in all_oracle_symbols[:5]]
    if text_parts:
        oracle_answer["text"] = " | ".join(text_parts)

    oracle_answer["repo_set_id"] = task_spec.get("artifacts", {}).get("repo_set_id", "")

    discovery = "sourcegraph_nls_multiquery" if mode in ("deep", "nls") else "sourcegraph_api"
    oracle_answer["_metadata"] = {
        "discovery_method": discovery,
        "curation_mode": mode,
        "num_runs": num_runs if mode != "keyword" else 1,
        "min_hits": min_hits if mode != "keyword" else 1,
        "llm_expansion_enabled": use_llm and HAS_ANTHROPIC,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repos_searched": repos,
        "sg_queries_made": client.queries_made,
    }

    return oracle_answer, log


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def find_task_spec(task_dir: Path) -> Optional[Path]:
    for p in [task_dir / "task_spec.json", task_dir / "tests" / "task_spec.json"]:
        if p.exists():
            return p
    return None


def find_oracle_answer(task_dir: Path) -> Optional[Path]:
    for p in [task_dir / "tests" / "oracle_answer.json", task_dir / "oracle_answer.json"]:
        if p.exists():
            return p
    return None


def oracle_answer_path(task_dir: Path) -> Path:
    tests_dir = task_dir / "tests"
    if tests_dir.is_dir():
        return tests_dir / "oracle_answer.json"
    return task_dir / "oracle_answer.json"


def oracle_log_path(task_dir: Path) -> Path:
    tests_dir = task_dir / "tests"
    if tests_dir.is_dir():
        return tests_dir / "oracle_curation_log.json"
    return task_dir / "oracle_curation_log.json"


def merge_oracle_answers(existing: Dict, new: Dict) -> Dict:
    merged = dict(existing)

    existing_files = {(f["repo"], f["path"]) for f in merged.get("files", [])}
    for f in new.get("files", []):
        key = (f["repo"], f["path"])
        if key not in existing_files:
            merged.setdefault("files", []).append(f)
            existing_files.add(key)

    existing_syms = {(s["repo"], s["path"], s["symbol"]) for s in merged.get("symbols", [])}
    for s in new.get("symbols", []):
        key = (s["repo"], s["path"], s["symbol"])
        if key not in existing_syms:
            merged.setdefault("symbols", []).append(s)
            existing_syms.add(key)

    if "chains" in new:
        merged["chains"] = new["chains"]
    if "chain" in new:
        merged["chain"] = new["chain"]

    for k in ("provenance", "required_keywords"):
        if k in new:
            merged[k] = new[k]

    if "text" in new:
        merged["text"] = new["text"]

    merged["_metadata"] = new.get("_metadata", merged.get("_metadata", {}))
    return merged


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _get_sg_credentials() -> Tuple[str, str]:
    url = (
        os.environ.get("SOURCEGRAPH_URL")
        or os.environ.get("SRC_ENDPOINT")
        or SourcegraphClient.DEFAULT_URL
    )
    token = (
        os.environ.get("SOURCEGRAPH_ACCESS_TOKEN")
        or os.environ.get("SRC_ACCESS_TOKEN")
        or ""
    )
    return url, token


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Curate oracle_answer.json for MCP-unique benchmark tasks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--task-dir", metavar="DIR")
    parser.add_argument("--task-spec", metavar="PATH")
    parser.add_argument(
        "--mode", choices=["deep", "nls", "keyword"], default="deep",
        help="deep: NLS + multi-query + rev-pin + tier (default). "
             "nls: single NLS + rev-pin. keyword: legacy.",
    )
    parser.add_argument(
        "--num-runs", type=int, default=3,
        help="Query variations per repo in deep/nls mode (default: 3).",
    )
    parser.add_argument(
        "--min-hits", type=int, default=2,
        help="Minimum queries a file must appear in to be included (default: 2).",
    )
    parser.add_argument(
        "--no-llm", action="store_true",
        help="Disable LLM query expansion (use pattern-based variation fallback).",
    )
    parser.add_argument(
        "--anthropic-api-key", metavar="KEY",
        help="Anthropic API key for LLM expansion (defaults to ANTHROPIC_API_KEY env var).",
    )
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--max-results", type=int, default=200)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if not args.task_dir and not args.task_spec:
        parser.error("One of --task-dir or --task-spec is required.")

    task_dir: Optional[Path] = Path(args.task_dir).resolve() if args.task_dir else None
    spec_path: Optional[Path] = Path(args.task_spec).resolve() if args.task_spec else None

    if task_dir and not spec_path:
        spec_path = find_task_spec(task_dir)
        if not spec_path:
            logging.error("task_spec.json not found in %s", task_dir)
            return 1
    if not task_dir and spec_path:
        task_dir = spec_path.parent

    assert task_dir is not None and spec_path is not None

    try:
        with open(spec_path) as f:
            task_spec = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logging.error("Cannot load task_spec.json: %s", exc)
        return 1

    project_root = _find_project_root(task_dir)
    logging.info("Project root: %s", project_root)

    repo_set_id = task_spec.get("artifacts", {}).get("repo_set_id", "")
    fixture = None
    if repo_set_id:
        fixture = load_fixture(repo_set_id, project_root)
        if fixture:
            revisions = {r["full_name"]: r.get("revision", "HEAD") for r in fixture.get("repos", [])}
            logging.info("Fixture: %s  repos=%d  revisions=%s", repo_set_id, len(fixture.get("repos", [])), revisions)

    existing_oracle: Dict = {}
    existing_path = find_oracle_answer(task_dir)
    if existing_path:
        try:
            with open(existing_path) as f:
                existing_oracle = json.load(f)
            logging.info("Existing oracle: %d files", len(existing_oracle.get("files", [])))
        except (json.JSONDecodeError, OSError):
            pass

    use_llm = not args.no_llm
    api_key = args.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    if args.dry_run:
        checks = task_spec.get("evaluation", {}).get("checks", [])
        seed_prompt = task_spec.get("prd", {}).get("seed_prompt", "")
        repos_with_revisions = get_repos_with_revisions(fixture) if fixture else []

        logging.info("[DRY RUN] mode=%s  num_runs=%d  min_hits=%d  llm=%s",
                     args.mode, args.num_runs, args.min_hits, use_llm and HAS_ANTHROPIC and bool(api_key))
        for check in checks:
            if check.get("type") == "file_set_match":
                params = check.get("params", {})
                queries, source = get_curation_queries(
                    params, seed_prompt, args.num_runs, use_llm=use_llm, api_key=api_key
                )
                logging.info("[DRY RUN] query_source=%s  queries=%s", source, queries)
        for name, rev in repos_with_revisions:
            rc = "" if rev == "HEAD" else f" rev:{rev}"
            logging.info("[DRY RUN] %s%s", _repo_sg_name(name), rc)
        return 0

    sg_url, sg_token = _get_sg_credentials()
    if not sg_token:
        logging.warning("No SOURCEGRAPH_ACCESS_TOKEN — API calls may fail")

    client = SourcegraphClient(sg_url, sg_token, verbose=args.verbose)
    logging.info("SG: %s  mode=%s  num_runs=%d  min_hits=%d  llm=%s",
                 sg_url, args.mode, args.num_runs, args.min_hits,
                 use_llm and HAS_ANTHROPIC and bool(api_key))

    oracle_answer, curation_log = curate_oracle(
        task_spec=task_spec,
        client=client,
        fixture=fixture,
        project_root=project_root,
        mode=args.mode,
        num_runs=args.num_runs,
        min_hits=args.min_hits,
        use_llm=use_llm,
        api_key=api_key or None,
        verbose=args.verbose,
    )

    if existing_oracle:
        oracle_answer = merge_oracle_answers(existing_oracle, oracle_answer)

    out_oracle = oracle_answer_path(task_dir)
    out_oracle.parent.mkdir(parents=True, exist_ok=True)
    with open(out_oracle, "w") as f:
        json.dump(oracle_answer, f, indent=2)
        f.write("\n")
    logging.info("Wrote %s: %d files, %d symbols",
                 out_oracle, len(oracle_answer.get("files", [])), len(oracle_answer.get("symbols", [])))

    log_data = {
        "task_id": task_spec.get("id", ""),
        "task_spec_path": str(spec_path),
        "curated_at": datetime.now(timezone.utc).isoformat(),
        "sg_url": sg_url,
        "curation_mode": args.mode,
        "num_runs": args.num_runs,
        "min_hits": args.min_hits,
        "llm_expansion": use_llm and HAS_ANTHROPIC and bool(api_key),
        "sg_queries_made": client.queries_made,
        "repos_searched": get_repos_from_fixture(fixture) if fixture else [],
        "curation_entries": curation_log,
        "sg_request_log": client.get_request_log(),
    }
    with open(oracle_log_path(task_dir), "w") as f:
        json.dump(log_data, f, indent=2)

    if args.verify:
        validator = project_root / "scripts" / "validate_mcp_task_instance.py"
        if validator.exists():
            result = subprocess.run(
                [sys.executable, str(validator), "--task-dir", str(task_dir), "--verbose"],
                capture_output=True, text=True,
            )
            print(result.stdout, end="")
            if result.returncode != 0:
                return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
