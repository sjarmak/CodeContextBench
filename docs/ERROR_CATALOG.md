# Error Catalog

Known errors, their fingerprints, and fixes. Referenced by `scripts/status_fingerprints.py` and the `/triage-failure` skill.

## Token Refresh Errors {#token-refresh}

**Fingerprint ID**: `token_refresh_403`
**Pattern**: `403|Forbidden|token.*refresh|refresh.*token|credentials.*expired`
**Severity**: infrastructure
**Cause**: OAuth access token expired mid-run. The agent's `ensure_fresh_token` call either wasn't invoked between batches or the token expired faster than the 30-minute margin.
**Fix**:
```bash
# Refresh manually
source configs/_common.sh && refresh_claude_token

# Or re-authenticate
claude auth
```
**Auto-retry?**: Yes, safe to retry after refreshing credentials.
**Notes**: Fixed via per-batch `ensure_fresh_token` in all config scripts. If still occurring, check if the refresh token itself has expired (requires full re-auth).

## Verifier Parse Error {#verifier-parse}

**Fingerprint ID**: `verifier_parse_error`
**Pattern**: `verifier.*(?:parse|json|decode|invalid)|JSONDecodeError.*verifier|reward.*parse`
**Severity**: verifier
**Cause**: The verifier/scorer script produced output that couldn't be parsed. Common causes:
- `test.sh` wrote non-JSON to reward.txt
- Verifier exited with error before writing reward
- Extra output (warnings, print statements) mixed with reward output
**Fix**: Check the task's `tests/test.sh` or verifier script. Ensure it writes a clean numeric value to reward.txt or valid JSON to reward.json.
**Auto-retry?**: No, needs code fix.
**Example files affected**: `benchmarks/ccb_*/*/tests/test.sh`

## API 500 Server Error {#api-500}

**Fingerprint ID**: `api_500`
**Pattern**: `500\s*Internal Server Error|api.*500|server.*error.*5\d{2}`
**Severity**: api
**Cause**: Anthropic API or Sourcegraph API returned a 500 error. Usually transient.
**Fix**: Retry the task. If persistent on Sourcegraph, check Sourcegraph instance health.
**Auto-retry?**: Yes, with backoff.
**Known instance**: K8s Docs SG_full regression — API 500 on `applyconfig-doc-001` (Sourcegraph-specific, not MCP code issue).

## API Rate Limit {#rate-limit}

**Fingerprint ID**: `api_rate_limit`
**Pattern**: `rate.?limit|429|too many requests|throttl|overloaded`
**Severity**: api
**Cause**: Hit Anthropic API rate limits or Sourcegraph rate limits.
**Fix**: Reduce parallelism (`--parallel 2` instead of `--parallel 4`) or wait before retrying.
**Auto-retry?**: Yes, with exponential backoff.

## Timeout {#timeout}

**Fingerprint ID**: `timeout`
**Pattern**: `timeout|timed?\s*out|deadline exceeded|SIGTERM|killed.*signal`
**Severity**: task (varies)
**Cause**: Task exceeded the configured time limit. Could be:
- Agent stuck in a loop (check transcript for repetitive tool calls)
- Task is inherently slow (large repo checkout, compilation)
- Docker container took too long to start
**Fix**: Check agent transcript to determine if stuck or legitimately slow. For stuck agents, the task may need a simpler prompt. For slow tasks, increase `--timeout-multiplier`.
**Auto-retry?**: Maybe — check logs first.

## MCP Connection Failure {#mcp-connection}

**Fingerprint ID**: `mcp_connection`
**Pattern**: `mcp.*(?:connect|refused|unavailable|error)|sourcegraph.*(?:connect|error|fail)`
**Severity**: mcp
**Cause**: MCP server (Sourcegraph) was unreachable or returned connection errors.
**Fix**: Check that the Sourcegraph instance is running and the access token is valid. Verify `SOURCEGRAPH_ACCESS_TOKEN` in `~/evals/.env.local`.
**Auto-retry?**: Yes, after verifying connectivity.

## Python Import Error {#import-error}

**Fingerprint ID**: `import_error`
**Pattern**: `ImportError|ModuleNotFoundError|No module named|cannot import`
**Severity**: setup
**Cause**: Missing Python dependency in the Docker image or task environment.
**Fix**: Update the Dockerfile or requirements.txt for the affected benchmark. For SWE-Perf, ensure numpy/sklearn/pandas are in the Docker image.
**Auto-retry?**: No, needs dependency fix.

## Docker/Container Failure {#docker-fail}

**Fingerprint ID**: `docker_compose_fail`
**Pattern**: `docker.*(?:compose|build|pull).*fail|container.*(?:exit|crash|fail)|OOMKill`
**Severity**: setup
**Cause**: Docker container failed to start, build, or was killed (OOM). Common causes:
- Docker image not found or pull failed
- Insufficient disk space
- Container exceeded memory limit
- `docker compose` config error in task setup
**Fix**: Check `docker ps -a` for crashed containers. Check disk space with `df -h`. For OOMKill, increase Docker memory limit.
**Auto-retry?**: Depends — fix the underlying issue first.

## Permission Denied {#permission-denied}

**Fingerprint ID**: `permission_denied`
**Pattern**: `permission denied|EACCES|Operation not permitted`
**Severity**: infrastructure
**Cause**: File or directory permission issue in the task workspace. Often caused by Docker volume mount permissions.
**Fix**: Check ownership of the task directory and workspace files. May need `chmod` or `chown` on the mounted volume.
**Auto-retry?**: No, needs permission fix.

## Git Operation Failure {#git-error}

**Fingerprint ID**: `git_error`
**Pattern**: `fatal:.*git|git.*(?:clone|checkout|pull).*fail|repository not found`
**Severity**: setup
**Cause**: Git clone/checkout failed. Could be network issue, private repo without credentials, or invalid commit hash.
**Fix**: Verify the repository URL is accessible. For private repos, ensure SSH keys or tokens are configured in the Docker environment.
**Auto-retry?**: Yes, if network issue. No, if credentials issue.

---

## Adding New Error Patterns

When you encounter a new recurring error:

1. Add the pattern to `scripts/status_fingerprints.py` in the `ERROR_FINGERPRINTS` list
2. Add a section to this catalog with the same fingerprint ID
3. Include: pattern, severity, cause, fix, and whether safe to auto-retry
4. Place more specific patterns before more general ones in the fingerprints list
