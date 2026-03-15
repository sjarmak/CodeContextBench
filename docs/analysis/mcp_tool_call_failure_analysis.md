# MCP Tool Call Failure Analysis

**Date**: 2026-03-12
**Scope**: All traces in `runs/official/` and `runs/analysis/`
**Dataset**: 85,820 MCP tool calls across 8,184 trajectories

---

## Executive Summary

Out of 85,820 MCP tool calls (excluding `tools/list`), **1,382 resulted in hard errors** (is_error=true), a **1.6% error rate**. Of these, **744 (54%) are schema violations** where the agent passed incorrect arguments — these are directly fixable via prompt or schema improvements.

A separate analysis of customer MCP usage over 7 days found similar patterns at much higher volume. This document cross-references both datasets to identify shared failure modes and additional edge cases.

---

## Benchmark Tool-Level Failure Rates

| Tool | Errors | Total Calls | Error Rate | Customer Error Rate |
|------|-------:|------------:|-----------:|--------------------:|
| `sg_read_file` | 1,031 | 36,864 | 2.8% | 7.2% (27,461 / 380,872) |
| `sg_list_files` | 167 | 10,928 | 1.5% | — |
| `sg_keyword_search` | 103 | 31,594 | 0.3% | — |
| `sg_compare_revisions` | 15 | 113 | 13.3% | 26.4% (1,019 / 3,866) |
| `sg_nls_search` | 29 | 3,561 | 0.8% | — |
| `sg_commit_search` | 11 | 239 | 4.6% | — |
| `sg_go_to_definition` | 0 | 64 | 0.0% | 52.5% (1,682 / 3,203) |
| `sg_find_references` | 2 | 260 | 0.8% | 7.8% (171 / 2,185) |
| `sg_grep` (hallucinated) | 11 | 11 | 100% | — |
| `sg_diff_search` | 3 | 95 | 3.2% | — |
| `sg_list_repos` | 2 | 1,919 | 0.1% | — |

---

## Cross-Reference with Customer Failure Analysis

### GoToDefinition — Customer: 52.5% failure, Benchmark: 0.0%

**Customer finding**: 1,682 failures out of 3,203 calls. Failures are extremely fast (~181ms), indicating validation/lookup errors. One instance (chime.sourcegraph.com) had a 98% failure rate, suggesting repo/path naming convention issues.

**Benchmark finding**: Zero failures across 64 calls. However, our sample size is very small (64 calls total), so we cannot rule out the same issue. All 64 successful calls used well-formed arguments:

```json
{"repo": "github.com/sg-evals/gcc--96dfb333", "path": "gcc/toplev.cc", "symbol": "dwarf2_debug_hooks"}
{"repo": "github.com/sg-evals/kafka--0753c489", "path": "clients/.../RecordAccumulator.java", "symbol": "append"}
```

**Gap**: Our agents rarely use `GoToDefinition` (64 calls vs 31,594 for `keyword_search`). This could mean: (a) our preamble doesn't encourage its use, or (b) agents prefer keyword search for the same task. Either way, we don't have enough data to validate the customer's pattern.

**Edge case to watch**: The customer noted the `path` param is ambiguous — agents think it means "the file where the definition lives" rather than "the file where the reference appears." This distinction doesn't surface in our data because we don't have enough usage, but it's a schema description issue that likely affects all deployments.

---

### CompareRevisions — Customer: 26.4% failure, Benchmark: 13.3%

**Customer finding**: 26% failure rate, avg failure duration ~119ms. Agent provides branch names or commit SHAs that don't exist.

**Benchmark finding**: 15 errors out of 113 calls (13.3%). Every single failure is a revision resolution error. The patterns confirm the customer's analysis:

| Error Pattern | Count | Example Args |
|--------------|------:|-------------|
| Version tag doesn't exist on mirror | 3 | `"base": "v1.40.1"` on a stripped mirror repo |
| Truncated/invalid commit SHA | 2 | `"head": "76f3eff8f1edebb98ad57f625dc9c3b7058a07b"` (39 chars, should be 40) |
| Git-style relative refs not supported | 2 | `"base": "HEAD~1"`, `"base": "4c8ebdaac...~1"` |
| `master` branch doesn't exist | 3 | `"head": "master"` on repos that use `main` |
| Full URL as revision | 1 | `"base": "github.com/envoyproxy/envoy:main"` |
| Invalid cursor pagination | 1 | `"after": "AjE0MA=="` (base64 cursor passed as revision) |
| Wrong param names | 1 | `"base_revision"` / `"head_revision"` instead of `"base"` / `"head"` |

**Additional edge cases not in customer analysis**:

- **Git relative refs** (`HEAD~1`, `commit~1`): The agent uses Git-native syntax that the SG API doesn't resolve. This likely affects customer deployments too.
- **`master` vs `main` confusion**: 3 failures from the agent assuming `master` exists. Mirror repos may strip branch metadata.
- **Cross-repo revision syntax**: Agent tried `"github.com/envoyproxy/envoy:main"` as a revision — mixing repo URL format with revision.

---

### FindReferences — Customer: 7.8% failure, Benchmark: 0.8%

**Customer finding**: 171 failures out of 2,185 calls. Similar to GoToDefinition — path/symbol validation issues.

**Benchmark finding**: Only 2 errors out of 260 calls (0.8%):

1. **Symbol not found via text search**: `"symbol": "Curl_cf_setup_socket"` in `lib/connect.c` — the symbol exists but the text-based fallback search couldn't locate it (possibly a macro or complex C definition).
2. **Upstream repo name**: `"repo": "github.com/prometheus/common"` — agent used the upstream name instead of the mirror, causing "repository not found."

**Gap**: Like GoToDefinition, our sample is small (260 calls). The customer's 7.8% rate at higher volume likely reflects the same path/symbol confusion identified in the GoToDefinition analysis. The customer recommendation to "use the path where the reference appears, not where the definition lives" applies equally here.

---

### ReadFile — Customer: 7.2% failure, Benchmark: 2.8%

**Customer finding**: 27,461 failures per week. Avg failure duration ~69ms, pointing to "file not found" from guessed paths.

**Benchmark finding**: 1,031 errors out of 36,864 calls (2.8%). Full breakdown:

| Error Type | Count | % of ReadFile Errors |
|-----------|------:|--------------------:|
| `limit`/`offset` schema violation | 644 | 62% |
| File not found | 134 | 13% |
| `startLine` type errors | 62 | 6% |
| Connection/transport errors | 28 | 3% |
| Sibling cascade | 67 | 7% |
| File too large | 45 | 4% |
| Repo not found | 20 | 2% |
| Missing required params | 5 | <1% |
| Other | 26 | 3% |

**Key difference**: Our #1 ReadFile error (62% of failures) is the `limit`/`offset` schema violation, which the customer analysis doesn't mention — possibly because their schema is more lenient, or because customer agents use a different model/preamble that doesn't trigger this confusion as often.

**Shared pattern — file not found (134 errors)**: Confirms the customer finding. Agent guesses paths that don't exist:

| Guess Pattern | Count | Example |
|--------------|------:|---------|
| Source file path slightly wrong | 102 | `pkg/endpoint/manager.go` (doesn't exist, actual is `pkg/endpoint/endpoint_manager.go`) |
| Config/manifest file guessed | 20 | `package.json` on a Go repo, `.proto` file in wrong directory |
| Test file guessed | 9 | `tests/requests/test_data_upload_settings.py` (path invented) |
| Absolute path used | 3 | `/workspace/src/...` instead of relative `src/...` |

**Additional edge cases not in customer analysis**:

- **File too large without line range (45 errors)**: Agent requests entire files >100KB. The error message says "please specify a smaller line range" — this is recoverable if the agent retries with `startLine`/`endLine`, but it wastes a turn.
- **`startLine` > `endLine` (3 errors)**: Agent inverts the range bounds.

---

## Repo Name Resolution — A Cross-Cutting Issue

Repo name errors affect multiple tools. Across all MCP calls in our benchmark:

| Repo Format | Usage Count | Notes |
|------------|------------:|-------|
| Mirror names (`sg-evals`/`sg-benchmarks`) | 71,434 | Correct for our setup |
| Upstream names (`github.com/kubernetes/kubernetes`) | 11,651 | Works when SG indexes the upstream |
| Missing `github.com/` prefix | 706 | Always fails |

The 706 calls missing the `github.com/` prefix are spread across multiple tools and cause "repository not found" errors. Top offenders:

| Missing-Prefix Repo | Count |
|---------------------|------:|
| `sg-evals/envoy--v1.31.2` | 17 |
| `sg-evals/kafka--0753c489` | 11 |
| `sg-evals/rust--01f6ddf7` | 6 |
| `mozilla-firefox/firefox` | 6 |
| `sg-evals/django--674eda1c` | 5 |
| `numpy/numpy` | 4 |

Beyond the prefix issue, there are also **mirror repos that simply don't exist** on the SG instance (repo was renamed, version tag changed, etc.) — these cause errors even with correct formatting. Examples: `sg-evals/NodeBB--8fd8079a` vs `sg-evals/nodebb--76c6e302` (case sensitivity), `sg-evals/OpenHands--latest` (tag format).

**Recommendation (aligns with customer analysis)**: Agents should use `sg_list_repos` to discover exact repo names before making calls, or the prompt should emphasize using the exact repo name from previous tool results.

---

## Benchmark Error Categories (Full Detail)

### 1. Schema Violations (744 errors, 54% of all hard errors)

The agent passes arguments the tool doesn't accept. This is the largest category and the most directly fixable.

#### 1a. Passing `limit` / `offset` to `sg_read_file` (638 errors)

The agent confuses MCP tool schemas with Claude Code's native `Read` tool (which accepts `limit`/`offset`).

| Pattern | Count |
|---------|------:|
| `limit` only | 571 |
| `offset` + `limit` | 39 |
| `offset` only | 28 |

**Example call:**
```json
{
  "function_name": "mcp__sourcegraph__sg_read_file",
  "arguments": {
    "repo": "github.com/sg-evals/envoy--v1.32.1",
    "path": "test/README.md",
    "limit": 100
  }
}
```

**Error:**
```
MCP error -32602: invalid params: validating "arguments": validating root:
unexpected additional properties ["limit"]
```

**Root cause:** The agent's native `Read` tool uses `limit`/`offset` for pagination. The agent transfers this mental model to `sg_read_file`, which uses `startLine`/`endLine` instead.

---

#### 1b. Wrong Type for `startLine` / `endLine` (62 errors)

The agent passes strings instead of integers, often trying to express ranges or anchors.

| Value passed | Intended meaning |
|-------------|-----------------|
| `"1, 100"` | Lines 1 through 100 |
| `"#1338"` | Line 1338 (with anchor syntax) |
| `"[475, 520]"` | Lines 475 to 520 (array syntax) |
| `"[843"` | Line 843 (malformed) |
| `"\\200"` | Line 200 (escaped) |
| `"1, \n1"` | Line 1 (confused formatting) |
| `"1, 50"` | Lines 1 through 50 (comma-separated range) |

**Example call:**
```json
{
  "function_name": "mcp__sourcegraph__sg_read_file",
  "arguments": {
    "repo": "github.com/prometheus/prometheus",
    "path": "config/config.go",
    "startLine": "1, 100",
    "endLine": 100
  }
}
```

**Error:**
```
MCP error -32602: invalid params: validating "arguments": validating root:
validating /properties/startLine: type: 1, 100 has type "string", want "integer"
```

**Root cause:** The schema description doesn't make the integer requirement salient enough. The agent tries creative string formats to express line ranges.

---

#### 1c. Wrong Parameter Names on Other Tools (20 errors)

| Tool | Param passed | Expected param | Count |
|------|-------------|---------------|------:|
| `sg_commit_search` | `query` | (tool-specific param) | 9 |
| `sg_list_files` | `directory` | `path` | 5 |
| `sg_list_files` | `query` | (not supported) | 3 |
| `sg_diff_search` | `query` | (tool-specific param) | 3 |

**Root cause:** The agent generalizes from one tool's parameter names to another. `query` is the natural param name for search tools, but some SG tools use different names.

---

#### 1d. Typos and Misspellings (7 errors)

| Passed | Intended | Count |
|--------|----------|------:|
| `endLevel` | `endLine` | 3 |
| `startLevel` | `startLine` | 2 |
| `edLine` | `endLine` | 1 |
| `command` | (unknown) | 1 |

---

#### 1e. Other Schema Violations (17 errors)

- Missing required parameters (7): Agent omits `repo` or `path` on `sg_read_file`.
- `repos` param on `sg_keyword_search` (1): Agent tries to pass repo filter as a separate argument instead of embedding `repo:^...` in the query string.
- Miscellaneous (9).

---

### 2. Hallucinated (Nonexistent) Tools (17 errors)

The agent invents MCP tool names that don't exist.

| Tool Attempted | Count | Likely Intended Tool |
|---------------|------:|---------------------|
| `mcp__sourcegraph__sg_grep` | 11 | `sg_keyword_search` |
| `mcp__keyword_search` | 2 | `mcp__sourcegraph__sg_keyword_search` |
| `mcp__sourcegraph__sg_finder` | 1 | `sg_list_files` or `sg_keyword_search` |
| `mcp__sourcegraph__sg_bash` | 1 | No equivalent (agent tried to run shell via MCP) |
| `mcp__sourcegraph__nls_search` | 1 | `mcp__sourcegraph__sg_nls_search` |
| `mcp__sourcegraph__list_files` | 1 | `mcp__sourcegraph__sg_list_files` |

**Root cause:** The agent expects a `grep`-like tool to exist (11/17 hallucinations). The remaining cases are prefix/naming errors — the agent drops the `sg_` prefix or the `sourcegraph__` namespace.

---

### 3. NLS Search Boolean Operator Misuse (22 errors)

The agent passes boolean operators (`AND`, `OR`, `NOT`) to `sg_nls_search`, which only accepts natural language queries.

**Example call:**
```json
{
  "function_name": "mcp__sourcegraph__sg_nls_search",
  "arguments": {
    "query": "parseQuery AND boolean operators NOT supported"
  }
}
```

**Error:**
```
failed to execute search: nls.parseQuery does not support boolean operators
```

**Root cause:** The agent treats semantic search like keyword search, applying boolean query syntax that only works with `sg_keyword_search`.

---

### 4. Argument Logic Errors (~50 errors)

#### 4a. File Too Large Without Line Range (~45 errors)

The agent calls `sg_read_file` on very large files (130KB-724KB) without specifying `startLine`/`endLine`. The tool rejects the request.

**Example error:**
```
File content is too large (724KB). Please specify a smaller line range. The file has 21223 lines
```

#### 4b. Inverted Line Range (3 errors)

Agent passes `startLine` > `endLine`.

**Error:**
```
start line must be less than or equal to end line
```

---

### 5. Infrastructure Errors (not argument-related, ~260 errors)

These are included for completeness but are not fixable via prompts.

- **Connection/transport errors** (138): gRPC connection failures, TCP read errors
- **Fetch failures** (6): Generic HTTP errors
- **Sibling tool call cascade** (121): One parallel tool call failed, causing all sibling calls to error

---

## Consolidated Recommendations

Ordered by combined impact across both benchmark and customer data:

### Priority 1: Disambiguate `sg_read_file` from native `Read` tool

**Impact**: 700 benchmark errors + likely contributes to customer's 27K weekly ReadFile errors
**Fix**: Add to the tool description or preamble:
> `sg_read_file` uses `startLine` and `endLine` (integers) to select line ranges. It does NOT support `limit`, `offset`, or any other pagination parameters. `startLine` and `endLine` must be plain integers (e.g., `150`), not strings, arrays, or ranges.

---

### Priority 2: Clarify GoToDefinition `path` semantics

**Impact**: 1,682 customer failures/week (52.5% rate), insufficient benchmark data to confirm
**Fix**: Update `sg_go_to_definition` and `sg_find_references` schema descriptions:
> The `path` parameter is the file where the symbol *reference* appears (the file you are currently reading), NOT the file where you expect the definition to be. The tool will locate the definition for you.

---

### Priority 3: Guide CompareRevisions revision format

**Impact**: 1,019 customer failures/week + 15 benchmark errors (13.3% rate)
**Fix**: Add to tool description:
> - Use full 40-character commit SHAs, not abbreviated ones
> - Git relative refs (`HEAD~1`, `commit~1`) are NOT supported
> - Branch names must exist on the indexed repo — use `main` not `master` unless you've verified the branch exists
> - Do not include repository URLs in revision fields

---

### Priority 4: Reduce ReadFile path guessing

**Impact**: ~27K customer failures/week + 134 benchmark errors (paths that don't exist)
**Fix**: Add to preamble:
> Before calling `sg_read_file`, verify the file exists using `sg_list_files` or `sg_keyword_search`. Do not guess file paths. Use the exact paths returned by previous tool calls.

---

### Priority 5: Warn about large file reads

**Impact**: ~45 benchmark errors + unknown customer impact
**Fix**: Add to `sg_read_file` description:
> For files larger than ~100KB, you MUST specify `startLine` and `endLine`. The tool will reject requests for very large files without a line range.

---

### Priority 6: Clarify NLS search is semantic-only

**Impact**: 22 benchmark errors + unknown customer impact
**Fix**: Add to `sg_nls_search` description:
> Accepts natural language queries only. Do NOT use boolean operators (AND/OR/NOT). For exact symbol or string matching, use `sg_keyword_search` instead.

---

### Priority 7: Clarify repo name format

**Impact**: ~60 benchmark errors (706 calls with wrong prefix) + contributes to customer repo-not-found errors
**Fix**: Add to preamble:
> Repository names must use the full `github.com/org/repo` format. Use `sg_list_repos` to discover exact repo names. Do not assume repository names — always use the exact name from previous search results or `sg_list_repos` output.

---

### Priority 8: Add `sg_grep` as alias or explicit non-tool

**Impact**: 11 benchmark errors
**Fix**: Either:
- Add `sg_grep` as an alias for `sg_keyword_search`, or
- Add to the preamble: *"There is no `sg_grep` tool. Use `sg_keyword_search` for exact/regex matching."*

---

### Priority 9: Standardize parameter names across tools

**Impact**: 20 benchmark errors
**Fix**: Add a quick-reference to the preamble:
> - `sg_list_files`: uses `path` (not `directory` or `query`)
> - `sg_commit_search`: uses `<specific_param>` (not `query`)
> - `sg_diff_search`: uses `<specific_param>` (not `query`)
> - `sg_keyword_search`: repo filter goes IN the query string as `repo:^org/repo$`, not as a separate `repos` argument

---

### Priority 10: Fix tool name prefix consistency

**Impact**: 6 benchmark errors (agents drop `sg_` prefix)
**Fix**: Add to preamble:
> All Sourcegraph MCP tools use the prefix `mcp__sourcegraph__sg_`. For example: `sg_keyword_search`, `sg_nls_search`, `sg_list_files`, `sg_read_file`.

---

## Appendix: Data Sources

- **Benchmark data**: 8,184 trajectories from `runs/official/_raw/` and `runs/analysis/`, collected 2026-02 through 2026-03
- **Customer data**: 7-day aggregation of MCP tool calls across customer Sourcegraph instances (provided separately)
- **Methodology**: Benchmark errors identified by `is_error=true` flag in ATIF-v1.2 trajectory format. Customer errors identified by instrumentation-level failure tracking.
