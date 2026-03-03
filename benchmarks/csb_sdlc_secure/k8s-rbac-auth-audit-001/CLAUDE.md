# k8s-rbac-auth-audit-001: Kubernetes RBAC Authorization Flow

This repository is very large (~4M+ LOC Go). Use targeted search to trace the authorization flow.

## Task Type: Security Analysis

Your goal is to trace the RBAC authorization flow from API request to permission decision.

## Search Strategy

- Start at `staging/src/k8s.io/apiserver/pkg/endpoints/filters/authorization.go` — this is the authorization middleware
- Trace to `staging/src/k8s.io/apiserver/pkg/authorization/authorizer/interfaces.go` — the Authorizer interface
- Find the RBAC implementation at `plugin/pkg/auth/authorizer/rbac/rbac.go`
- Look at bootstrap policies in `plugin/pkg/auth/authorizer/rbac/bootstrappolicy/`
- Check authorization config at `staging/src/k8s.io/apiserver/pkg/server/options/authorization.go`
- Trace RBAC resource storage at `pkg/registry/rbac/`
- Look at the authorizer union (chain) at `staging/src/k8s.io/apiserver/pkg/authorization/union/union.go`

## Output Format

Write your analysis to `/logs/agent/solution.md` with the sections specified in the instruction.
