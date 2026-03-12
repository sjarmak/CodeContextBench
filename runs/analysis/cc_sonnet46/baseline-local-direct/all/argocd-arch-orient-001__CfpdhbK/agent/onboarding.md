# Argo CD Codebase Orientation

## 1. Main Entry Points

All Argo CD binaries share a single compiled Go binary dispatched via `cmd/main.go`. The binary's behavior is determined by its filename (or `ARGOCD_BINARY_NAME` env var) via a switch statement that calls each component's `NewCommand()`.

### API Server (`argocd-server`)
- **Entry point**: `cmd/argocd-server/commands/argocd_server.go` → `NewCommand()`
- **Primary responsibility**: Serves the Argo CD REST/gRPC API that the web UI and CLI consume. Handles authentication (OIDC/Dex), RBAC enforcement, and exposes endpoints for managing Applications, AppProjects, repositories, clusters, etc. It is the main user-facing gateway.

### Application Controller (`argocd-application-controller`)
- **Entry point**: `cmd/argocd-application-controller/commands/argocd_application_controller.go` → `NewCommand()`
- **Primary responsibility**: The core Kubernetes controller. Continuously watches `Application` CRs, compares desired state (from the repo server) against live cluster state, computes health/sync status, triggers sync operations, and performs self-healing. Runs a workqueue with configurable `statusProcessors` and `operationProcessors` goroutines (defaults: 20 and 10 respectively). The main loop is started via `appController.Run(ctx, statusProcessors, operationProcessors)`.

### Repo Server (`argocd-repo-server`)
- **Entry point**: `cmd/argocd-repo-server/commands/argocd_repo_server.go` → `NewCommand()`
- **Primary responsibility**: Stateless gRPC service (port 8081) that handles all repository interactions. Clones and caches Git repos, generates Kubernetes manifests from Helm charts, Kustomize overlays, plain YAML directories, and Config Management Plugins (CMP). It is the only component that accesses source repositories directly.

### ApplicationSet Controller (`argocd-applicationset-controller`)
- **Entry point**: `cmd/argocd-applicationset-controller/commands/applicationset_controller.go` → `NewCommand()`
- **Primary responsibility**: Watches `ApplicationSet` CRs and uses generators (Git, Cluster, List, Matrix, SCM provider, etc.) to dynamically create, update, and delete `Application` CRs at scale. Implements the `Reconcile` method via `controller-runtime` (`applicationset/controllers/applicationset_controller.go`).

---

## 2. Core Packages

### `controller` (`/workspace/controller/`)
Implements the `ApplicationController` (in `appcontroller.go`) and the `AppStateManager` interface (in `state.go` and `sync.go`). Key files:
- `appcontroller.go`: Main controller struct, informer setup, reconciliation workqueues (`processAppRefreshQueueItem`, `processAppOperationQueueItem`)
- `state.go`: `CompareAppState()` — diff between desired and live state, `GetRepoObjs()` to fetch manifests from the repo server
- `sync.go`: `SyncAppState()` — drives the actual sync via `gitops-engine`'s `sync.NewSyncContext` and `syncCtx.Sync()`
- `hook.go`: Handles pre/post-delete hook lifecycle

### `pkg/apis/application/v1alpha1` (`/workspace/pkg/apis/application/v1alpha1/`)
Defines all CRD types used across Argo CD:
- `types.go`: Core structs — `Application`, `ApplicationSpec`, `ApplicationStatus`, `SyncPolicy`, `SyncStrategy`, `SyncStrategyApply`, `SyncStrategyHook`, `SyncOptions`, `RetryStrategy`, `AppProject`, `Repository`, `Cluster`, etc.
- `applicationset_types.go`: `ApplicationSet` and related generator types
- Generated deepcopy code in `zz_generated.deepcopy.go`

### `reposerver/repository` (`/workspace/reposerver/repository/`)
Contains the repo server gRPC service implementation:
- `repository.go`: The `Service` struct implements `RepoServerServiceClient`. Key functions: `GenerateManifest()`, `GenerateManifestWithFiles()`, `GenerateManifests()` (the core function that dispatches to Helm, Kustomize, directory, or CMP based on `ApplicationSourceType`), `ListRefs()`, `ListApps()`
- `types.go`: Internal types for manifest generation options

### `util/settings` (`/workspace/util/settings/`)
Provides centralized configuration management:
- `settings.go`: `ArgoCDSettings` struct holds all runtime config (URL, OIDC, RBAC policy, resource customizations, etc.). `SettingsManager` reads from `argocd-cm` ConfigMap and `argocd-secret` Secret via Kubernetes informers. Key: `NewSettingsManager()`, `GetSettings()`
- `accounts.go`, `filtered_resource.go`, `resources_filter.go`: Sub-domain settings

### `util/db` (`/workspace/util/db/`)
Database abstraction layer backed by Kubernetes Secrets/ConfigMaps:
- `db.go`: `ArgoDB` interface
- `cluster.go`: Stores cluster connection credentials
- `repository.go`, `repository_secrets.go`: Stores repo credentials and secrets
- `certificate.go`: TLS certificate storage

### `util/argo` (`/workspace/util/argo/`)
Core Argo CD business logic utilities:
- `argo.go`: `ValidateRepo()`, `ValidateDestination()`, `ValidatePermissions()`, `FilterByProjects()`, `RefreshApp()`
- `resource_tracking.go`: Tracks which app owns which Kubernetes resource (via label or annotation)
- `diff/`: Computes diffs between desired and live resource state
- `normalizers/`: Normalizes resources before diffing (handles `ignoreDifferences`)

---

## 3. Configuration Loading

All components use **`github.com/spf13/cobra`** for CLI flag parsing and **`github.com/spf13/viper`** (indirectly) for env var fallbacks. The pattern is consistent across all components:

### CLI Flags
Each `NewCommand()` function defines local variables and calls `command.Flags().XxxVar(...)` to bind them. Flags typically fall back to environment variables via helpers in `util/env`:
```
command.Flags().Int64Var(&appResyncPeriod, "app-resync",
    env.ParseNumFromEnv("ARGOCD_RECONCILIATION_TIMEOUT", 180, ...))
```
This means every flag has a matching environment variable fallback (e.g., `ARGOCD_APPLICATION_CONTROLLER_STATUS_PROCESSORS` → `--status-processors`).

### Kubernetes ConfigMap/Secret (Runtime Config)
The `util/settings.SettingsManager` is the central runtime config loader:
- **`argocd-cm`** ConfigMap (`common.ArgoCDConfigMapName`): Application-level settings (URL, OIDC config, resource customizations, RBAC policy, etc.)
- **`argocd-secret`** Secret (`common.ArgoCDSecretName`): Sensitive values (admin password hash, OIDC client secret, server secret key)
- **`argocd-cmd-params-cm`** ConfigMap (`common.ArgoCDCmdParamsConfigMapName`): Per-component tuning parameters
- `SettingsManager` uses Kubernetes `ConfigMapLister` and `SecretLister` (from shared informers) to watch for live changes without restart.

### Main Config Structs
- `util/settings.ArgoCDSettings`: Top-level runtime config
- Each component's `NewCommand()` local vars define component-specific settings
- `pkg/apis/application/v1alpha1` types define per-Application config (e.g., `SyncPolicy`, `ApplicationSource`)

### kubectl/kubeconfig
All server-side components accept `--kubeconfig` and `--in-cluster` flags via `util/cli.AddKubectlFlagsToCmd(&command)`, which wraps `k8s.io/client-go/tools/clientcmd`.

---

## 4. Test Structure

### Unit Tests
- **Location**: Co-located with source files (e.g., `controller/appcontroller_test.go`, `controller/state_test.go`, `reposerver/repository/repository_test.go`, `util/settings/settings_test.go`)
- **Framework**: Standard `testing` package + `github.com/stretchr/testify` (`assert`, `require`, `mock`)
- **Pattern**: Use fake Kubernetes clients (`k8s.io/client-go/kubernetes/fake`), in-memory data structures, and `testify/mock` for interfaces. No real cluster or network needed.

### Integration/Component Tests
- **Location**: Also co-located with source (`controller/sync_test.go`, `reposerver/repository/repository_test.go`)
- **Framework**: Same `testing` + `testify` but may spin up lightweight servers or use real filesystem operations (e.g., git clone of local testdata repos in `reposerver/repository/testdata/`)
- **Notable**: Many repo server tests clone local bare Git repos from `testdata/` to test manifest generation end-to-end without external network.

### E2E Tests
- **Location**: `test/e2e/` directory
  - Test files: `app_management_test.go`, `app_autosync_test.go`, `app_sync_options_test.go`, `applicationset_test.go`, etc.
  - Fixtures: `test/e2e/fixture/` — provides `EnsureCleanState()`, ArgoCD API client wrappers, cluster setup helpers
  - App-specific fixture DSL: `test/e2e/fixture/app/` — fluent builder pattern for creating and asserting on apps
- **Framework**: Standard `testing` package + `testify/assert` + `testify/require`. **No Ginkgo or Gomega** — uses plain Go test functions.
- **Requirements**: A running Argo CD installation (real or kind cluster). Tests call the real Argo CD API server and watch actual Kubernetes resources.
- **Pattern**: Tests call `Given().Path("guestbook").When().CreateApp().Sync().Then().Expect(OperationPhaseIs(OperationSucceeded))` via the fixture DSL.

---

## 5. Application Sync Pipeline

The sync pipeline flows through 4 main stages:

### Stage 1: CRD Type Definition
- **Package**: `pkg/apis/application/v1alpha1/`
- **Key files**: `types.go`
- `Application` struct defines `.spec.source` (Git repo, path, revision), `.spec.destination` (cluster server, namespace), `.spec.syncPolicy`, and `.status`
- The `Operation` field on `Application` triggers a sync when set by the user or auto-sync

### Stage 2: Controller Reconciliation (Application Controller)
- **Package**: `controller/`
- **Key files**: `appcontroller.go`, `state.go`
- `processAppRefreshQueueItem()` (`appcontroller.go:1541`) picks apps from the refresh queue
- `CompareAppState()` (`state.go`) is called to determine if a sync is needed:
  - Calls `GetRepoObjs()` which makes a gRPC call to the repo server (`GenerateManifest`)
  - Compares returned manifests against live cluster state (from `controller/cache`)
  - Produces a `comparisonResult` with `syncStatus` and `healthStatus`
- If sync is needed (auto-sync policy or explicit operation), the operation is queued
- `processAppOperationQueueItem()` (`appcontroller.go:934`) picks up pending operations and calls `SyncAppState()`

### Stage 3: Manifest Generation (Repo Server)
- **Package**: `reposerver/repository/`
- **Key files**: `repository.go`
- `GenerateManifest()` (`repository.go:515`) receives a `ManifestRequest` via gRPC
- Internally calls `GenerateManifests()` (`repository.go:1410`) which detects `ApplicationSourceType` and dispatches to:
  - `helmTemplate()` → runs `helm template`
  - `kustomize.NewKustomizeApp().Build()` → runs `kustomize build`
  - `findManifests()` → reads raw YAML/JSON from directory
  - `runConfigManagementPluginSidecars()` → calls CMP plugin over Unix socket
- Results are cached in Redis keyed by repo URL + revision + source config hash

### Stage 4: Kubernetes Apply (Sync Execution)
- **Package**: `controller/`, with `gitops-engine` (`github.com/argoproj/gitops-engine`)
- **Key files**: `controller/sync.go`, external `gitops-engine/pkg/sync/`
- `SyncAppState()` (`sync.go:90`) prepares sync options, then calls `sync.NewSyncContext()` (gitops-engine) to build the sync context
- `syncCtx.Sync()` orchestrates:
  1. Processes resources in wave order (`argocd.argoproj.io/sync-wave` annotation)
  2. Executes PreSync hooks first
  3. Applies main resources using `kubectl apply` (or `replace`/server-side apply based on options)
  4. Executes PostSync hooks
  5. Handles hook cleanup
- The kubectl execution uses `util/kube.Kubectl` (`kubectl.go`) which shells out to `kubectl` or uses the dynamic client
- Results are written back to `app.status.operationState` and `app.status.sync`

---

## 6. Adding a New Sync Strategy

To add a new sync strategy (e.g., a custom hook phase or wave behavior), the following sequence of changes is needed:

### Step 1: Define the new type/option in the CRD
- **File**: `pkg/apis/application/v1alpha1/types.go`
- Add a new field to `SyncStrategy`, `SyncOperation`, or `SyncOptions` (if it's a string-key option) or `SyncPolicy`
- Example: Add a new struct `SyncStrategyMyCustom` and a field to `SyncStrategy`
- Regenerate deepcopy: `zz_generated.deepcopy.go` must be updated (run `make generate-deepcopy` or similar codegen command)

### Step 2: Add the constant (if a SyncOption key)
- If the new strategy is a string-valued sync option (like `Replace=true`, `ServerSideApply=true`), add a constant in `github.com/argoproj/gitops-engine/pkg/sync/common` (upstream), or use an Argo CD-specific constant in `common/common.go` or the gitops-engine package

### Step 3: Wire it in the sync execution
- **File**: `controller/sync.go` → `SyncAppState()`
- Parse the new option from `syncOp.SyncOptions.HasOption(...)` or from the new struct field
- Pass the corresponding option to `sync.NewSyncContext()` via `sync.WithXxx(...)` options (gitops-engine interface)
- If the behavior is not in gitops-engine, implement it directly in `SyncAppState()` before/after `syncCtx.Sync()` is called

### Step 4: If wave/hook behavior changes are needed
- **File**: `controller/sync.go` → `delayBetweenSyncWaves()` (`sync.go:557`) — add logic here for custom inter-wave behavior
- The `SyncWaveHook` function signature is `func(phase common.SyncPhase, wave int, finalWave bool) error` — implement a new hook and pass it to `sync.WithSyncWaveHook()`

### Step 5: Expose via the API
- **File**: `server/application/application.go` — the API server's application service
- Update any validation in `util/argo/argo.go` (`ValidateRepo`, `ValidatePermissions`) if the new option has access implications
- Update the gRPC proto definitions in `pkg/apiclient/application/application.proto` and regenerate (`application.pb.go`) if the new strategy needs to be sent over the wire from the CLI

### Step 6: Expose via CLI
- **File**: `cmd/argocd/commands/app.go`
- Add `--new-strategy` flag to the `app sync` command and populate `SyncOptions` or the `SyncStrategy` struct

### Step 7: Write tests
- **Unit tests**: `controller/sync_test.go` and `controller/state_test.go` for the controller logic
- **E2E tests**: Add a new test in `test/e2e/app_sync_options_test.go` or `test/e2e/app_management_test.go`
