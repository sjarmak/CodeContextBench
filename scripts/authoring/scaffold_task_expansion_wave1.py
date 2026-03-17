#!/usr/bin/env python3
"""Scaffold the first task-expansion wave from docs/ops/handoff_task_expansion_92.md.

Wave 1 covers the highest-priority Quality-category gap:
  - csb_org_incident: +16 tasks
  - csb_org_security: +16 tasks

The script:
  1. Writes any missing repo-set fixtures.
  2. Appends use cases to configs/use_case_registry.json.
  3. Generates task skeletons with scripts/generate_csb_org_tasks.py.
  4. Applies the standard org-task MCP customization layer.
  5. Registers the new tasks in configs/selected_benchmark_tasks.json.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = ROOT / "fixtures" / "repo_sets"
REGISTRY_PATH = ROOT / "configs" / "use_case_registry.json"
SELECTED_TASKS_PATH = ROOT / "configs" / "selected_benchmark_tasks.json"

sys.path.insert(0, str(ROOT / "scripts"))
from customize_mcp_skeletons import (  # type: ignore[E402]
    copy_sgonly_wrapper,
    create_test_sh,
    fix_instruction_template_bugs,
    generate_artifact_only_dockerfile,
    generate_instruction_mcp,
    update_sg_only_dockerfile,
)
from generate_csb_org_tasks import derive_task_id, derive_task_slug  # type: ignore[E402]


FIXTURE_DEFS = {
    "fastapi-web-framework": {
        "id": "fastapi-web-framework",
        "primary_language": "Python",
        "description": "FastAPI core framework for validation, routing, security, and ASGI request handling tasks",
        "repos": [
            {
                "full_name": "fastapi/fastapi",
                "logical_name": "fastapi/fastapi",
                "revision": "11614be9021aa4ac078d4d0693a8b5250a1010d8",
                "language": "Python",
                "loc_estimate": 150000,
            }
        ],
        "local_checkout_repos": ["fastapi/fastapi"],
        "mcp_only_repos": ["fastapi/fastapi"],
    },
    "fastapi-requests": {
        "id": "fastapi-requests",
        "primary_language": "Python",
        "description": "FastAPI server plus requests client paths for small multi-repo incident tracing",
        "repos": [
            {
                "full_name": "fastapi/fastapi",
                "logical_name": "fastapi/fastapi",
                "revision": "11614be9021aa4ac078d4d0693a8b5250a1010d8",
                "language": "Python",
                "loc_estimate": 150000,
            },
            {
                "full_name": "psf/requests",
                "logical_name": "psf/requests",
                "revision": "0e4ae38f0c93d4f92a96c774bd52c069d12a4798",
                "language": "Python",
                "loc_estimate": 50000,
            },
        ],
        "local_checkout_repos": ["fastapi/fastapi", "psf/requests"],
        "mcp_only_repos": ["fastapi/fastapi", "psf/requests"],
    },
    "gin-web-framework": {
        "id": "gin-web-framework",
        "primary_language": "Go",
        "description": "Gin HTTP framework for routing, middleware, and request binding tasks",
        "repos": [
            {
                "full_name": "gin-gonic/gin",
                "logical_name": "gin-gonic/gin",
                "revision": "3e44fdc4d1636a2b1599c6688a76e13216a413dd",
                "language": "Go",
                "loc_estimate": 120000,
            }
        ],
        "local_checkout_repos": ["gin-gonic/gin"],
        "mcp_only_repos": ["gin-gonic/gin"],
    },
    "gin-testify": {
        "id": "gin-testify",
        "primary_language": "Go",
        "description": "Gin plus testify for lightweight multi-repo incident tracing and assertion flow tasks",
        "repos": [
            {
                "full_name": "gin-gonic/gin",
                "logical_name": "gin-gonic/gin",
                "revision": "3e44fdc4d1636a2b1599c6688a76e13216a413dd",
                "language": "Go",
                "loc_estimate": 120000,
            },
            {
                "full_name": "stretchr/testify",
                "logical_name": "stretchr/testify",
                "revision": "5f80e4aef7bee125b7e9c0b620edf25f6fc93350",
                "language": "Go",
                "loc_estimate": 45000,
            },
        ],
        "local_checkout_repos": ["gin-gonic/gin", "stretchr/testify"],
        "mcp_only_repos": ["gin-gonic/gin", "stretchr/testify"],
    },
    "flask-web-framework": {
        "id": "flask-web-framework",
        "primary_language": "Python",
        "description": "Flask core framework for cookie, host validation, and request lifecycle audits",
        "repos": [
            {
                "full_name": "pallets/flask",
                "logical_name": "pallets/flask",
                "revision": "3a9d54f3da1de540adfdf6f1e2dea6fc0006e15d",
                "language": "Python",
                "loc_estimate": 90000,
            }
        ],
        "local_checkout_repos": ["pallets/flask"],
        "mcp_only_repos": ["pallets/flask"],
    },
    "hashicorp-consul": {
        "id": "hashicorp-consul",
        "primary_language": "Go",
        "description": "Consul service discovery, ACL, and mesh control plane codepaths",
        "repos": [
            {
                "full_name": "hashicorp/consul",
                "logical_name": "hashicorp/consul",
                "revision": "554b4ba24f8680308afa7bbbdcc7494cedff7ea1",
                "language": "Go",
                "loc_estimate": 700000,
            }
        ],
        "local_checkout_repos": ["hashicorp/consul"],
        "mcp_only_repos": ["hashicorp/consul"],
    },
    "hashicorp-vault": {
        "id": "hashicorp-vault",
        "primary_language": "Go",
        "description": "Vault auth, lease management, and seal lifecycle implementation",
        "repos": [
            {
                "full_name": "hashicorp/vault",
                "logical_name": "hashicorp/vault",
                "revision": "9f398e95cabbdc28d65f68633cb10a9328d1332a",
                "language": "Go",
                "loc_estimate": 900000,
            }
        ],
        "local_checkout_repos": ["hashicorp/vault"],
        "mcp_only_repos": ["hashicorp/vault"],
    },
    "linux-kernel": {
        "id": "linux-kernel",
        "primary_language": "C",
        "description": "Linux kernel subsystems for production incident tracing and hardening audits",
        "repos": [
            {
                "full_name": "torvalds/linux",
                "logical_name": "torvalds/linux",
                "revision": "4ae12d8bd9a830799db335ee661d6cbc6597f838",
                "language": "C",
                "loc_estimate": 28000000,
            }
        ],
        "local_checkout_repos": ["torvalds/linux"],
        "mcp_only_repos": ["torvalds/linux"],
    },
    "redis-database": {
        "id": "redis-database",
        "primary_language": "C",
        "description": "Redis authentication, ACL, and protected-mode configuration paths",
        "repos": [
            {
                "full_name": "redis/redis",
                "logical_name": "redis/redis",
                "revision": "b3ce4c28ca733529d4456b504616c1b408962a67",
                "language": "C",
                "loc_estimate": 350000,
            }
        ],
        "local_checkout_repos": ["redis/redis"],
        "mcp_only_repos": ["redis/redis"],
    },
    "spark-analytics": {
        "id": "spark-analytics",
        "primary_language": "Java",
        "description": "Apache Spark driver, UI auth, executor secret, and RPC security paths",
        "repos": [
            {
                "full_name": "apache/spark",
                "logical_name": "apache/spark",
                "revision": "8b3e3458346abb457288f9d6e6bed7ec25ed1f1e",
                "language": "Java",
                "loc_estimate": 2200000,
            }
        ],
        "local_checkout_repos": ["apache/spark"],
        "mcp_only_repos": ["apache/spark"],
    },
}


def _incident(
    use_case_id: int,
    title: str,
    prompt: str,
    repo_set_id: str,
    estimated_repos: int,
    search_pattern: str,
    curation_queries: list[str] | None = None,
) -> dict:
    use_case = {
        "use_case_id": use_case_id,
        "category": "D",
        "title": title,
        "customer_prompt": prompt,
        "mcp_suite": "csb_org_incident",
        "task_family": "incident-debug",
        "mcp_unique": True,
        "oracle_type": "deterministic_json",
        "oracle_check_types": ["file_set_match"],
        "repo_set_id": repo_set_id,
        "difficulty": "hard",
        "estimated_repos_needed": estimated_repos,
        "deepsearch_relevant": False,
        "mcp_capabilities_required": ["keyword_search", "read_file", "find_references"],
        "verification_modes": ["artifact"],
        "search_pattern": search_pattern,
    }
    if curation_queries:
        use_case["curation_queries"] = curation_queries
    return use_case


def _security(
    use_case_id: int,
    title: str,
    prompt: str,
    repo_set_id: str,
    estimated_repos: int,
    search_pattern: str,
    curation_queries: list[str] | None = None,
) -> dict:
    use_case = {
        "use_case_id": use_case_id,
        "category": "B",
        "title": title,
        "customer_prompt": prompt,
        "mcp_suite": "csb_org_security",
        "task_family": "vuln-remediation",
        "mcp_unique": True,
        "oracle_type": "deterministic_json",
        "oracle_check_types": ["file_set_match"],
        "repo_set_id": repo_set_id,
        "difficulty": "hard",
        "estimated_repos_needed": estimated_repos,
        "deepsearch_relevant": False,
        "mcp_capabilities_required": ["keyword_search", "read_file", "find_references"],
        "verification_modes": ["artifact"],
        "search_pattern": search_pattern,
    }
    if curation_queries:
        use_case["curation_queries"] = curation_queries
    return use_case


WAVE1_USE_CASES = [
    _incident(
        297,
        "FastAPI 422 Validation Error Trace Across Client and Server",
        "A POST request sent with requests returns HTTP 422 from a FastAPI service. Find the Python source files across fastapi/fastapi and psf/requests that (1) serialize and send the request body on the client side, (2) parse request bodies and trigger validation in FastAPI, and (3) construct the validation error response returned to the caller.",
        "fastapi-requests",
        2,
        "422 OR validation error OR request body OR requests",
    ),
    _incident(
        298,
        "FastAPI Streaming Upload Timeout Trace",
        "A large upload made with requests times out against a FastAPI endpoint. Find the Python source files across psf/requests and fastapi/fastapi that (1) stream request bodies on the client side, (2) consume the ASGI request body on the server side, and (3) raise or surface timeout and disconnect handling during request processing.",
        "fastapi-requests",
        2,
        "stream upload OR timeout OR disconnect OR request body",
    ),
    _incident(
        299,
        "Gin Middleware Panic Trace With Test Harness",
        "A Gin service panics after a middleware is added and the regression is reproduced in a testify-backed test. Find the Go source files across gin-gonic/gin and stretchr/testify that (1) compose the Gin handler chain, (2) dispatch handlers through Gin's request pipeline, and (3) implement the testify panic assertions used by the reproducer.",
        "gin-testify",
        2,
        "combineHandlers OR handleHTTPRequest OR Panics OR NotPanics",
        [
            "combineHandlers",
            "handleHTTPRequest",
            "Panics OR NotPanics",
        ],
    ),
    _incident(
        300,
        "Gin Request Binding Failure Trace With Assertions",
        "A Gin handler starts returning 400 after a binding change and the failure is checked in a testify suite. Find the Go source files across gin-gonic/gin and stretchr/testify that (1) invoke Gin's request-binding entry points, (2) attach the 400/ErrorTypeBind response for invalid input, and (3) provide the testify error assertions used to verify the failure.",
        "gin-testify",
        2,
        "ShouldBind OR MustBindWith OR ErrorTypeBind OR EqualError",
        [
            "ShouldBind OR ShouldBindWith",
            "MustBindWith OR ErrorTypeBind",
            "EqualError OR NoError",
        ],
    ),
    _incident(
        301,
        "Consul Service Mesh Timeout Trace",
        "Consul service mesh traffic starts timing out between sidecars. Find the Go source files in hashicorp/consul that (1) build or propagate upstream proxy configuration, (2) manage Connect sidecar or proxy timeouts, and (3) surface timeout failures during request forwarding or service resolution.",
        "hashicorp-consul",
        1,
        "Connect OR proxy timeout OR service mesh OR upstream",
    ),
    _incident(
        302,
        "Consul Anti-Entropy Sync Failure Root Cause",
        "Consul reports anti-entropy sync failures and stale catalog state. Find the Go source files in hashicorp/consul that (1) schedule anti-entropy reconciliation, (2) compare local and remote service/catalog state, and (3) apply or log sync failure handling when reconciliation cannot complete.",
        "hashicorp-consul",
        1,
        "anti entropy OR reconcile OR catalog sync",
    ),
    _incident(
        303,
        "Consul ACL Deny Incident Trace",
        "A Consul API call unexpectedly returns permission denied. Find the Go source files in hashicorp/consul that (1) parse or attach ACL tokens to the request context, (2) enforce ACL policy decisions for the request path, and (3) generate the deny response or audit log entry that surfaces the incident.",
        "hashicorp-consul",
        1,
        "ACL OR permission denied OR authorize OR token",
    ),
    _incident(
        304,
        "Vault Secret Lease Expiry Trace",
        "A Vault client loses access because a dynamic secret lease expires unexpectedly. Find the Go source files in hashicorp/vault that (1) issue and renew leases, (2) revoke or expire leases in the expiration manager, and (3) surface lease-expiry errors back through the request path.",
        "hashicorp-vault",
        1,
        "lease OR expiration OR renew OR revoke",
    ),
    _incident(
        305,
        "Vault Auth Method Failure Trace",
        "A Vault login flow begins failing after an auth backend change. Find the Go source files in hashicorp/vault that (1) dispatch login requests to auth backends, (2) validate the auth method response and token creation path, and (3) propagate authentication failures to the API caller or audit logs.",
        "hashicorp-vault",
        1,
        "auth backend OR login OR token OR authenticate",
    ),
    _incident(
        306,
        "Vault Seal-Unseal Error Trace",
        "Vault fails to unseal after a restart and operators see a seal-related error. Find the Go source files in hashicorp/vault that (1) coordinate seal and unseal state, (2) process recovery or unseal key shares, and (3) emit the error path when unseal initialization fails.",
        "hashicorp-vault",
        1,
        "seal OR unseal OR recovery key OR barrier",
    ),
    _incident(
        307,
        "Linux Kernel Oops Driver Trace",
        "A kernel oops points at a driver path after a device event. Find the C source files in torvalds/linux that (1) register the relevant driver probe or interrupt path, (2) report kernel oops or BUG diagnostics for that subsystem, and (3) unwind or log the fault from the crashing code path.",
        "linux-kernel",
        1,
        "oops OR BUG OR driver probe OR interrupt",
    ),
    _incident(
        308,
        "Linux OOM Kill Path Trace",
        "A production node is killing processes because it is out of memory. Find the C source files in torvalds/linux that (1) detect global or cgroup memory pressure, (2) select a victim for the OOM killer, and (3) log or notify the final kill decision.",
        "linux-kernel",
        1,
        "oom OR out of memory OR victim OR cgroup",
    ),
    _incident(
        309,
        "Linux IRQ Storm Incident Trace",
        "A system enters an IRQ storm and stops making forward progress. Find the C source files in torvalds/linux that (1) dispatch hard IRQ handling, (2) detect interrupt flood or stuck-interrupt conditions, and (3) disable, throttle, or log the problematic IRQ line.",
        "linux-kernel",
        1,
        "IRQ OR interrupt storm OR disable_irq OR flood",
    ),
    _incident(
        310,
        "Chromium Renderer Crash Trace",
        "Chromium starts crashing in the renderer process after a navigation event. Find the C++ source files in chromium/chromium that (1) bootstrap renderer process startup, (2) dispatch the failing navigation or document lifecycle work inside the renderer, and (3) surface the crash or fatal termination back to browser-side crash handling.",
        "chromium-browser",
        1,
        "renderer crash OR navigation OR RenderProcessHost",
    ),
    _incident(
        311,
        "Chromium IPC Channel Failure Trace",
        "Chromium reports an IPC channel error between browser and renderer processes. Find the C++ source files in chromium/chromium that (1) create or bind the IPC/Mojo channel, (2) handle channel disconnect or pipe closure, and (3) propagate the resulting error to process teardown or recovery code.",
        "chromium-browser",
        1,
        "IPC OR Mojo OR channel error OR disconnect",
    ),
    _incident(
        312,
        "Chromium GPU Process Abort Trace",
        "The Chromium GPU process aborts during graphics initialization. Find the C++ source files in chromium/chromium that (1) launch and initialize the GPU process, (2) set up the graphics or command-buffer path that can fail, and (3) handle or report the GPU-process crash back to the browser process.",
        "chromium-browser",
        1,
        "GPU process OR command buffer OR graphics init OR crash",
    ),
    _security(
        313,
        "FastAPI CORS Middleware Audit",
        "Audit FastAPI's CORS handling. Find the Python source files in fastapi/fastapi that (1) configure allowed origins, methods, and headers for CORS, (2) process preflight OPTIONS requests, and (3) attach the final CORS response headers to application responses.",
        "fastapi-web-framework",
        1,
        "CORS OR preflight OR allow origins OR response headers",
    ),
    _security(
        314,
        "FastAPI OAuth2 and JWT Scope Resolution Audit",
        "Audit FastAPI's security dependency flow for bearer-token-protected routes. Find the Python source files in fastapi/fastapi that (1) define OAuth2 bearer helpers and security scopes, (2) resolve security dependencies for a request, and (3) raise the authentication or authorization errors returned when token validation fails.",
        "fastapi-web-framework",
        1,
        "OAuth2 OR JWT OR security scopes OR bearer",
    ),
    _security(
        315,
        "FastAPI API Key Security Dependency Audit",
        "Audit FastAPI's API-key authentication path. Find the Python source files in fastapi/fastapi that (1) define APIKeyHeader/APIKeyCookie/APIKeyQuery and reject missing credentials, (2) thread security dependencies and scopes through dependency resolution, and (3) raise the authentication errors or headers returned to callers when credentials are absent or invalid.",
        "fastapi-web-framework",
        1,
        "APIKeyHeader OR APIKeyCookie OR APIKeyQuery OR check_api_key OR solve_dependencies",
        [
            "APIKeyHeader OR APIKeyCookie OR APIKeyQuery",
            "check_api_key OR WWW-Authenticate",
            "solve_dependencies OR SecurityScopes",
        ],
    ),
    _security(
        316,
        "Flask Session Cookie Security Audit",
        "Audit Flask's session-cookie handling. Find the Python source files in pallets/flask that (1) create and load the secure cookie session, (2) configure cookie security attributes such as HttpOnly, Secure, SameSite, and domain/path settings, and (3) sign or verify session data before it is trusted.",
        "flask-web-framework",
        1,
        "session cookie OR SameSite OR HttpOnly OR Secure",
    ),
    _security(
        317,
        "Flask Host Validation and Trusted Routing Audit",
        "Audit Flask's host and URL security boundaries. Find the Python source files in pallets/flask that (1) validate trusted hosts or server names, (2) bind request routing to the incoming host header, and (3) reject or normalize unsafe host information before URL matching proceeds.",
        "flask-web-framework",
        1,
        "trusted hosts OR SERVER_NAME OR host header OR routing",
    ),
    _security(
        318,
        "Vault TLS Certificate Rotation Audit",
        "Audit Vault's TLS certificate lifecycle. Find the Go source files in hashicorp/vault that (1) load TLS certificates and key material, (2) watch for or apply certificate rotation and reload events, and (3) rebuild listener or client TLS configuration after the rotation occurs.",
        "hashicorp-vault",
        1,
        "TLS OR certificate reload OR listener OR rotate",
    ),
    _security(
        319,
        "Vault Auth Boundary Enforcement Audit",
        "Audit Vault's authentication and authorization boundary. Find the Go source files in hashicorp/vault that (1) authenticate a request into an identity or token, (2) resolve attached policies and capabilities, and (3) enforce the final authorization decision for a protected path.",
        "hashicorp-vault",
        1,
        "token OR identity OR policy OR capability",
    ),
    _security(
        320,
        "Vault Secret Engine Access Control Audit",
        "Audit Vault secret-engine access control. Find the Go source files in hashicorp/vault that (1) register or dispatch secret-engine backends, (2) gate secret-engine operations on capabilities or path policy checks, and (3) emit the deny path when a caller crosses an auth boundary.",
        "hashicorp-vault",
        1,
        "secret engine OR capability OR authorize OR deny",
    ),
    _security(
        321,
        "Redis AUTH and ACL Enforcement Audit",
        "Audit Redis authentication and ACL enforcement. Find the C source files in redis/redis that (1) parse AUTH or ACL commands, (2) attach authenticated user state to the client connection, and (3) enforce command-level permissions before an operation is executed.",
        "redis-database",
        1,
        "AUTH OR ACL OR authenticated user OR permissions",
    ),
    _security(
        322,
        "Redis Protected Mode Configuration Audit",
        "Audit Redis protected-mode behavior. Find the C source files in redis/redis that (1) load and validate bind/protected-mode configuration, (2) decide whether a remote client should be rejected before authentication, and (3) return the protected-mode error sent to disallowed connections.",
        "redis-database",
        1,
        "protected mode OR bind OR reject OR remote client",
    ),
    _security(
        323,
        "Elasticsearch Transport TLS Audit",
        "Audit Elasticsearch transport-layer TLS. Find the Java source files in elastic/elasticsearch that (1) load transport SSL/TLS settings and certificates, (2) build the transport-layer SSL context or channel handlers, and (3) enforce certificate validation for inter-node transport connections.",
        "elasticsearch-search",
        1,
        "transport TLS OR SSL context OR certificate validation",
    ),
    _security(
        324,
        "Elasticsearch API Key Scope Validation Audit",
        "Audit Elasticsearch API key authorization. Find the Java source files in elastic/elasticsearch that (1) parse or authenticate API keys, (2) resolve the privileges and scopes attached to an API key, and (3) enforce those scopes when a request reaches a protected REST or transport action.",
        "elasticsearch-search",
        1,
        "API key OR privileges OR scopes OR authenticate",
    ),
    _security(
        325,
        "Elasticsearch RBAC Resolution Audit",
        "Audit Elasticsearch role-based access control. Find the Java source files in elastic/elasticsearch that (1) resolve user roles and role descriptors, (2) map those roles into cluster or index privileges, and (3) apply the final allow-or-deny authorization decision for an incoming action.",
        "elasticsearch-search",
        1,
        "role descriptor OR privileges OR authorization OR allow deny",
    ),
    _security(
        326,
        "Spark UI Authentication Audit",
        "Audit Spark's web UI authentication path. Find the Java or Scala source files in apache/spark that (1) configure UI authentication filters or servlet handlers, (2) attach authenticated user identity to UI requests, and (3) reject unauthenticated access to protected UI routes.",
        "spark-analytics",
        1,
        "UI auth OR filter OR servlet OR unauthenticated",
    ),
    _security(
        327,
        "Spark Executor Secret Handling Audit",
        "Audit Spark's executor secret and credential handling. Find the Java or Scala source files in apache/spark that (1) generate or distribute secrets from the driver to executors, (2) store or redact those secrets in runtime configuration, and (3) validate the secret on executor startup or RPC authentication.",
        "spark-analytics",
        1,
        "executor secret OR token OR redact OR authenticate",
    ),
    _security(
        328,
        "Spark Network Encryption and Auth Audit",
        "Audit Spark's encrypted RPC and shuffle authentication path. Find the Java or Scala source files in apache/spark that (1) configure network encryption or SASL/auth settings, (2) build the secure transport or shuffle-service connection, and (3) enforce handshake failure handling when authentication or encryption negotiation breaks.",
        "spark-analytics",
        1,
        "network encryption OR SASL OR shuffle OR handshake",
    ),
]


FILE_EXTENSIONS = {
    "python": ".py",
    "go": ".go",
    "java": ".java",
    "c": ".c",
    "c++": ".cpp",
}


def write_fixtures() -> None:
    for fixture_id, data in FIXTURE_DEFS.items():
        path = FIXTURES_DIR / f"{fixture_id}.json"
        path.write_text(json.dumps(data, indent=2) + "\n")


def merge_registry(use_cases: list[dict]) -> None:
    registry = json.loads(REGISTRY_PATH.read_text())
    by_id = {entry["use_case_id"]: entry for entry in registry["use_cases"]}
    for use_case in use_cases:
        by_id[use_case["use_case_id"]] = use_case
    registry["use_cases"] = [by_id[key] for key in sorted(by_id)]
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2) + "\n")


def _run_generate(use_case_ids: list[int]) -> None:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "generate_csb_org_tasks.py"),
        "--use-case-ids",
        *[str(use_case_id) for use_case_id in use_case_ids],
    ]
    subprocess.run(cmd, check=True, cwd=ROOT, env=_build_env())


def _fixture_for_use_case(use_case: dict) -> dict:
    fixture_id = use_case["repo_set_id"]
    if fixture_id in FIXTURE_DEFS:
        return FIXTURE_DEFS[fixture_id]
    return json.loads((FIXTURES_DIR / f"{fixture_id}.json").read_text())


def _language_for_fixture(fixture: dict) -> str:
    primary = fixture.get("primary_language", "unknown").lower()
    return primary.replace("/", "/")


def _file_ext_for_fixture(fixture: dict) -> str:
    language = fixture.get("primary_language", "unknown").lower()
    if language.startswith("c++"):
        return ".cpp"
    return FILE_EXTENSIONS.get(language.split("/", 1)[0], ".txt")


def _build_repo_customization(fixture: dict) -> tuple[list[str], list[dict]]:
    sg_repos = [repo["full_name"] for repo in fixture["repos"]]
    clone_repos = []
    for repo in fixture["repos"]:
        target_dir = repo["full_name"].split("/")[-1]
        clone_repos.append({"mirror": repo["full_name"], "target_dir": target_dir})
    return sg_repos, clone_repos


def customize_generated_tasks(use_cases: list[dict]) -> None:
    for use_case in use_cases:
        task_id = derive_task_id(use_case)
        task_slug = derive_task_slug(task_id)
        task_dir = ROOT / "benchmarks" / use_case["mcp_suite"] / task_slug
        fixture = _fixture_for_use_case(use_case)
        sg_repos, clone_repos = _build_repo_customization(fixture)
        file_ext = _file_ext_for_fixture(fixture)
        language = _language_for_fixture(fixture)

        generate_artifact_only_dockerfile(str(task_dir), sg_repos)
        update_sg_only_dockerfile(str(task_dir), sg_repos, clone_repos)
        create_test_sh(str(task_dir))
        copy_sgonly_wrapper(str(task_dir))
        generate_instruction_mcp(str(task_dir), sg_repos, use_case)
        fix_instruction_template_bugs(str(task_dir), file_ext, language)
        inject_curation_params(task_dir, use_case, file_ext)


def inject_curation_params(task_dir: Path, use_case: dict, file_ext: str) -> None:
    task_spec_path = task_dir / "tests" / "task_spec.json"
    task_spec = json.loads(task_spec_path.read_text())
    for check in task_spec.get("evaluation", {}).get("checks", []):
        if check.get("type") != "file_set_match":
            continue
        params = check.setdefault("params", {})
        params["search_pattern"] = use_case["search_pattern"]
        params["file_filter"] = f".*\\{file_ext}$"
        if use_case.get("curation_queries"):
            params["curation_queries"] = list(use_case["curation_queries"])
    task_spec_path.write_text(json.dumps(task_spec, indent=2) + "\n")


def register_selected_tasks(use_cases: list[dict]) -> None:
    selected = json.loads(SELECTED_TASKS_PATH.read_text())
    wave1_ids = {derive_task_id(use_case).lower() for use_case in use_cases}
    existing_entries_by_id = {
        entry.get("task_id", "").lower(): dict(entry)
        for entry in selected["tasks"]
        if entry.get("task_id")
    }
    preserved_entries = [entry for entry in selected["tasks"] if entry.get("task_id", "").lower() not in wave1_ids]
    existing_ids = {entry["task_id"].lower() for entry in preserved_entries}
    new_entries = []

    for use_case in use_cases:
        task_id = derive_task_id(use_case)
        task_slug = derive_task_slug(task_id)
        fixture = _fixture_for_use_case(use_case)
        language = _language_for_fixture(fixture)
        primary_repo = fixture["repos"][0]["logical_name"]
        entry = {
            "task_id": task_id,
            "benchmark": use_case["mcp_suite"],
            "sdlc_phase": use_case["task_family"],
            "language": language,
            "difficulty": use_case["difficulty"],
            "category": use_case["task_family"],
            "repo": primary_repo,
            "mcp_benefit_score": 0.9,
            "mcp_breakdown": {
                "context_complexity": 0.9,
                "cross_file_deps": 0.9,
                "semantic_search_potential": 0.9,
                "task_category_weight": 0.9,
            },
            "selection_rationale": use_case["title"],
            "task_dir": f"{use_case['mcp_suite']}/{task_slug}",
            "context_length": 0,
            "context_length_source": "task_expansion_wave1",
            "files_count": 0,
            "files_count_source": "task_expansion_wave1",
            "repo_set_id": use_case["repo_set_id"],
            "mcp_unique": True,
            "verification_modes": use_case["verification_modes"],
        }
        existing_entry = existing_entries_by_id.get(task_id.lower(), {})
        if existing_entry:
            merged_entry = dict(existing_entry)
            merged_entry.update(entry)
            entry = merged_entry
        if task_id.lower() not in existing_ids:
            new_entries.append(entry)
            existing_ids.add(task_id.lower())

    selected["tasks"] = preserved_entries + new_entries

    per_suite = {}
    unique_total = 0
    seen = set()
    for entry in selected["tasks"]:
        task_id_lower = entry.get("task_id", "").lower()
        if task_id_lower in seen:
            continue
        seen.add(task_id_lower)
        unique_total += 1
        benchmark = entry.get("benchmark", "unknown")
        per_suite[benchmark] = per_suite.get(benchmark, 0) + 1

    metadata = selected.setdefault("metadata", {})
    metadata["last_updated"] = "2026-03-07"
    metadata["total_selected"] = unique_total
    if isinstance(metadata.get("total_available"), int):
        metadata["total_available"] = max(metadata["total_available"], unique_total)
    metadata["per_suite"] = dict(sorted(per_suite.items()))
    metadata["note"] = (
        "DOE-driven rebalance plus wave-1 expansion: added 32 new Quality-category org tasks "
        "(16 incident, 16 security) anchored in fastapi, gin, consul, vault, linux, flask, "
        "redis, spark, and existing chromium/elasticsearch coverage."
    )

    statistics_block = selected.setdefault("statistics", {})
    statistics_block["tasks_per_benchmark"] = dict(sorted(per_suite.items()))
    statistics_block["total_tasks"] = unique_total

    SELECTED_TASKS_PATH.write_text(json.dumps(selected, indent=2) + "\n")


def _load_dotenv(dotenv_path: Path) -> dict[str, str]:
    loaded: dict[str, str] = {}
    if not dotenv_path.exists():
        return loaded

    for raw_line in dotenv_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        loaded[key] = value

    return loaded


def _build_env() -> dict[str, str]:
    env = os.environ.copy()
    for key, value in _load_dotenv(ROOT / ".env.local").items():
        env.setdefault(key, value)
    return env


def curate_tasks(use_cases: list[dict], mode: str, verify: bool) -> None:
    env = _build_env()
    for use_case in use_cases:
        task_id = derive_task_id(use_case)
        task_slug = derive_task_slug(task_id)
        task_dir = ROOT / "benchmarks" / use_case["mcp_suite"] / task_slug
        cmd = [
            sys.executable,
            str(ROOT / "scripts" / "curate_oracle.py"),
            "--task-dir",
            str(task_dir),
            "--mode",
            mode,
        ]
        if verify:
            cmd.append("--verify")
        subprocess.run(cmd, check=False, cwd=ROOT, env=env)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold and optionally curate the wave-1 org task expansion.")
    parser.add_argument("--curate", action="store_true", help="Run curate_oracle.py for the generated wave-1 tasks.")
    parser.add_argument("--mode", default="deep", choices=["deep", "nls", "keyword"], help="Oracle curation mode.")
    parser.add_argument("--verify", action="store_true", help="Run validate_org_task_instance via curate_oracle.py --verify.")
    args = parser.parse_args()

    use_case_ids = [use_case["use_case_id"] for use_case in WAVE1_USE_CASES]
    write_fixtures()
    merge_registry(WAVE1_USE_CASES)
    _run_generate(use_case_ids)
    customize_generated_tasks(WAVE1_USE_CASES)
    register_selected_tasks(WAVE1_USE_CASES)
    if args.curate:
        curate_tasks(WAVE1_USE_CASES, mode=args.mode, verify=args.verify)
    print(f"Scaffolded {len(WAVE1_USE_CASES)} wave-1 tasks: {use_case_ids[0]}-{use_case_ids[-1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
