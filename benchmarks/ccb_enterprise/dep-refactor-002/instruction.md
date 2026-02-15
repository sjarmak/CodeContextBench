# Add FlagExists Method to ReadOnlyFlagStore Interface

**Repository:** flipt-io/flipt
**Access Scope:** You may modify files in `internal/`. You may read any file to understand existing patterns.

## Context

Flipt is a feature flag platform built with Go. The `ReadOnlyFlagStore` interface in `internal/storage/storage.go` defines the contract for reading flag data from storage backends. Multiple concrete types implement this interface across the codebase (filesystem snapshots, SQL backends, etc.).

The evaluation server needs a lightweight way to check if a flag exists without fetching the full flag object. Currently, it must call `GetFlag()` and check for errors, which is inefficient. A dedicated `FlagExists()` method would allow backends to optimize existence checks (e.g., via SQL `EXISTS` or filesystem stat).

## Task

Add a `FlagExists(ctx context.Context, req *flipt.GetFlagRequest) (bool, error)` method to the `ReadOnlyFlagStore` interface and implement it in all concrete types that satisfy this interface.

**YOU MUST IMPLEMENT CODE CHANGES.**

### Requirements

1. **Find the interface definition** — Read `internal/storage/storage.go` to find the `ReadOnlyFlagStore` interface and understand its existing methods (e.g., `GetFlag`, `ListFlags`, `CountFlags`)
2. **Find all implementations** — Search for all types that implement `ReadOnlyFlagStore`. These are types that have methods like `GetFlag(ctx context.Context, req *flipt.GetFlagRequest) (*flipt.Flag, error)` matching the interface
3. **Add the method to the interface** — In `internal/storage/storage.go`, add:
   ```go
   FlagExists(ctx context.Context, req *flipt.GetFlagRequest) (bool, error)
   ```
4. **Implement in each concrete type** — For each implementing type, add a `FlagExists` method that:
   - Takes `(ctx context.Context, req *flipt.GetFlagRequest) (bool, error)`
   - Calls the type's existing `GetFlag()` method
   - Returns `true, nil` if the flag is found
   - Returns `false, nil` if the flag is not found (not-found error)
   - Returns `false, err` for other errors
5. **Handle not-found errors** — Use the existing `errs` package or error patterns in each backend to distinguish "not found" from real errors. Look at how `GetFlag` callers handle the not-found case in each backend.

### Hints

- The `ReadOnlyFlagStore` interface is in `internal/storage/storage.go` — look for existing methods like `CountFlags`
- Key implementations to find:
  - `internal/storage/fs/store.go` — filesystem store
  - `internal/storage/fs/snapshot.go` — filesystem snapshot
  - `internal/storage/sql/common/flag.go` — SQL backend
- Use `find_references("ReadOnlyFlagStore")` to instantly locate all implementations
- The `GetFlag` method in each backend shows the error handling pattern you should follow
- Look at `errs.ErrNotFound` or `ErrNotFoundf` for the standard not-found error type
- The `CountFlags` method already exists in the interface — `FlagExists` is confirmed absent

## Success Criteria

- `ReadOnlyFlagStore` interface includes `FlagExists` method
- All concrete types that implement `ReadOnlyFlagStore` have a `FlagExists` method
- Each implementation correctly handles not-found vs real errors
- `go build ./internal/...` succeeds with zero errors
- No existing tests broken
- Changes are scoped to `internal/` only
