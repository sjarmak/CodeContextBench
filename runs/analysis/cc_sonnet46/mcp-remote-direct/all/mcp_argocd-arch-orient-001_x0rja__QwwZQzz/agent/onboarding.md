# Argo CD Codebase Orientation

## 1. Main Entry Points

Argo CD uses a single multi-call binary pattern. The single entry point at `cmd/main.go` dispatches to the appropriate component based on the binary name (`os.Args[0]` or the `ARGOCD_BINARY_NAME` environment variable). All components use `github.com/spf13/cobra` for CLI wiring.

### API Server (`argocd-server`)
- **Entry**: `cmd/argocd-server/commands/argocd_server.go` → `NewCommand()`
- **Responsibility**: Exposes the Argo CD REST/gRPC API, serves the Web UI static assets, handles SSO (Dex/OIDC), webhook processing, and RBAC enforcement. It connects to the repo server and communicates with the Kubernetes API to read/write Application CRDs.

### Application Controller (`argocd-application-controller`)
- **Entry**: `cmd/argocd-application-controller/commands/argocd_application_controller.go` → `NewCommand()`
- **Responsibility**: The core GitOps reconciliation engine. It is a Kubernetes controller that watches `Application` CRDs, continuously compares the desired state (manifests from git/repo server) against the live cluster state, determines sync status, and executes sync operations (applying, pruning, running hooks). It drives the `appRefreshQueue` and `appOperationQueue` work queues.

### Repo Server (`argocd-repo-server`)
- **Entry**: `cmd/argocd-repo-server/commands/argocd_repo_server.go` → `NewCommand()`
- **Responsibility**: A stateless gRPC service that clones git repositories and generates Kubernetes manifests. It supports Helm templating, Kustomize overlays, raw YAML directories, and Config Management Plugins (CMP). Accessed by the application controller and API server via gRPC. The core logic lives in `reposerver/repository/repository.go`.

### ApplicationSet Controller (`argocd-applicationset-controller`)
- **Entry**: `cmd/argocd-applicationset-controller/commands/applicationset_controller.go` → `NewCommand()`
- **Responsibility**: Manages `ApplicationSet` CRDs, which template multiple `Application` resources using generators (Git, Cluster, List, Matrix, etc.). Built on `controller-runtime`. Generators live in `applicationset/generators/`.

---

## 2. Core Packages

### `controller` — Application Reconciliation
- **Key files**: `controller/appcontroller.go`, `controller/state.go`, `controller/sync.go`
- **Responsibility**: The heart of Argo CD. `appcontroller.go` contains `ApplicationController` which implements the Kubernetes controller loop. `processAppRefreshQueueItem()` (line 1541) handles comparison (calls `CompareAppState`) and auto-sync. `state.go` contains the `AppStateManager` interface with `CompareAppState` (diffs desired vs. live state) and `SyncAppState` (drives `sync.NewSyncContext` from the gitops-engine). `sync.go` builds the `SyncContext` options (waves, hooks, prune policy, server-side apply) and calls `syncCtx.Sync()`.

### `pkg/apis/application/v1alpha1` — API Types / CRDs
- **Key files**: `types.go`, `app_project_types.go`, `applicationset_types.go`, `repository_types.go`
- **Responsibility**: Defines all Argo CD custom resource types: `Application`, `AppProject`, `ApplicationSet`, `Repository`, `RepoCreds`. These are generated with `controller-gen` / `go-to-protobuf`. Key structs include `ApplicationSpec`, `SyncPolicy`, `SyncStrategy`, `SyncPolicyAutomated`, `RetryStrategy`, `SyncStrategyHook`, and `SyncStrategyApply`.

### `reposerver/repository` — Manifest Generation
- **Key files**: `reposerver/repository/repository.go`, `chart.go`, `types.go`
- **Responsibility**: Implements the repo server gRPC service. The top-level function `GenerateManifests()` (line 1409 of `repository.go`) resolves the tool type (Helm, Kustomize, directory, CMP), renders manifests, and returns them. Also handles repository cloning/fetching via `util/git`, chart indexing via `chart.go`, and caching via `reposerver/cache`.

### `util/settings` — Configuration Store
- **Key files**: `util/settings/settings.go`
- **Responsibility**: `SettingsManager` (constructed with `NewSettingsManager()`, line 1801) is the central configuration manager. It reads the `argocd-cm` ConfigMap and `argocd-secret` Secret from Kubernetes, and exposes typed configuration via methods like `GetSettings()` (returns `ArgoCDSettings`), `GetRepositories()`, `GetClusters()`, etc. Used by virtually every component.

### `util/db` — Argo CD Database Layer
- **Key files**: `util/db/` (cluster.go, repository.go, etc.)
- **Responsibility**: A thin abstraction over Kubernetes Secrets and ConfigMaps, providing CRUD operations for clusters, repositories, repo credentials, and GPG keys. `NewDB(namespace, settingsMgr, kubeclientset)` is the constructor. Used by the controller and API server to resolve cluster endpoints and repository credentials at runtime.

### `util/argo` — Argo CD Utilities
- **Key files**: `util/argo/` (argo.go, diff/, normalizers/)
- **Responsibility**: Cross-cutting utilities: diff computation (`argodiff`), resource normalisation, project/permission helpers (`GetAppProject`), resource tracking, and augmenting sync error messages. The `diff/` sub-package wraps `gitops-engine/pkg/diff` for comparing live vs. desired state.

### `applicationset/` — ApplicationSet Controllers & Generators
- **Key dirs**: `applicationset/controllers/`, `applicationset/generators/`, `applicationset/services/`
- **Responsibility**: Implements the ApplicationSet reconciler (built on `controller-runtime`) and all generators (Git file/directory, List, Cluster, Matrix, Merge, Pull Request, etc.). The `ClusterGenerator` uses `SettingsManager` to enumerate registered clusters.

---

## 3. Configuration Loading

All components share the same configuration pipeline:

### CLI Flags (via `github.com/spf13/cobra`)
- Each component's `NewCommand()` function declares local variables and binds them to `command.Flags()` using typed methods: `StringVar`, `IntVar`, `BoolVar`, `DurationVar`, etc.
- Example (application controller, `argocd_application_controller.go:238`):
  ```go
  command.Flags().StringVar(&repoServerAddress, "repo-server",
      env.StringFromEnv("ARGOCD_APPLICATION_CONTROLLER_REPO_SERVER", common.DefaultRepoServerAddr),
      "Repo server address.")
  ```
- The default for every flag is resolved from an environment variable via helpers in `util/env/` (`env.StringFromEnv`, `env.ParseNumFromEnv`, `env.ParseBoolFromEnv`). Environment variables thus act as configuration file alternatives.

### Kubernetes ConfigMap/Secret (via `SettingsManager`)
- At startup, each component constructs a `settings.SettingsManager` by calling `settings.NewSettingsManager(ctx, kubeClient, namespace)`.
- `SettingsManager.GetSettings()` reads the `argocd-cm` ConfigMap (URL, SSO config, OIDC, Kustomize options, resource tracking method, etc.) and the `argocd-secret` Secret (server signature key, webhook secrets, TLS certs).
- Settings are cached in memory and watched via Kubernetes informers; the manager re-reads and calls registered change handlers on updates.
- For the application controller this is done at line 157 of `argocd_application_controller.go`:
  ```go
  settingsMgr := settings.NewSettingsManager(ctx, kubeClient, namespace,
      settings.WithRepoOrClusterChangedHandler(func() {
          appController.InvalidateProjectsCache()
      }))
  ```

### Main Configuration Structs
- `util/settings.ArgoCDSettings` — in-memory runtime config (`URL`, `DexConfig`, `Secrets`, TLS, webhook secrets, etc.)
- `pkg/apis/application/v1alpha1.Application` — the CRD driving per-application configuration
- `pkg/apis/application/v1alpha1.SyncPolicy` / `SyncPolicyAutomated` — auto-sync, prune, self-heal settings

---

## 4. Test Structure

### Unit Tests (co-located `_test.go` files)
- The majority of tests live alongside source files, e.g.:
  - `controller/appcontroller_test.go` — tests for the reconciliation loop
  - `controller/state_test.go` — tests for `CompareAppState`
  - `util/settings/settings_test.go` — tests for `SettingsManager`
  - `reposerver/repository/repository_test.go` — tests for manifest generation
- Framework: `github.com/stretchr/testify` (`assert`, `require`) and the standard `testing` package.
- Kubernetes fake clients: `k8s.io/client-go/kubernetes/fake` and generated fake clients in `pkg/client/clientset/versioned/typed/application/v1alpha1/fake/`.

### Integration-Style Controller Tests
- Controller tests in `controller/appcontroller_test.go` spin up informers and fake clients to test multi-step reconciliation flows without a real cluster.
- ApplicationSet tests in `applicationset/controllers/` similarly use `controller-runtime` fake environments.

### End-to-End (E2E) Tests
- **Location**: `test/e2e/`
- **Framework**: Standard Go `testing`, `testify`, and an in-house fluent fixture DSL defined in `test/e2e/fixture/` and `test/e2e/fixture/app/`. Tests use a `Given().Path(...).When().CreateApp().Sync().Then().Expect(...)` builder chain.
- E2E tests require a running Argo CD installation (typically started via `Procfile` or `make start-e2e`). They exercise the real API server, controller, and repo server.
- Coverage includes: hooks (`hook_test.go`), sync waves (`sync_waves_test.go`), Helm (`helm_test.go`), Kustomize (`kustomize_test.go`), application lifecycle (`app_management_test.go`), ApplicationSets (`applicationset_test.go`), and 40+ more files.

### Test Helpers and Fixture Utilities
- `test/testdata.go` and `test/testutil.go` — shared helpers (fake project listers, fake cluster info, etc.)
- `test/e2e/fixture/` — `Context`, `Expectation`, and `Action` types for the DSL

---

## 5. Application Sync Pipeline

The journey from an `Application` CRD to resources deployed in a Kubernetes cluster goes through four main stages:

### Stage 1: CRD Definition & Kubernetes Persistence
- **Files**: `pkg/apis/application/v1alpha1/types.go`, `pkg/client/clientset/versioned/`
- A user creates an `Application` resource (via `kubectl`, the `argocd` CLI, or the API server). The CRD struct is `Application` with `ApplicationSpec` containing the source (`RepoURL`, `Path`, `TargetRevision`, `Helm`/`Kustomize` config), destination (`Server`, `Namespace`), and `SyncPolicy`.
- The generated typed clientset in `pkg/client/clientset/versioned/` and informers in `pkg/client/informers/` watch these resources and notify the controller.

### Stage 2: Controller Detects Change & Queues Reconciliation
- **Files**: `controller/appcontroller.go`
- The `ApplicationController` runs informers on `Application` and `AppProject` resources. When an app is created/updated or the periodic resync timer fires (default 3 minutes), the key is pushed onto `ctrl.appRefreshQueue`.
- `processAppRefreshQueueItem()` (line 1541) dequeues the key, determines the required `CompareWith` level (`CompareWithLatest`, `CompareWithRecent`, etc.), and calls `ctrl.appStateManager.CompareAppState(...)` (line 1672).

### Stage 3: Repo Server Generates Manifests & State Is Compared
- **Files**: `controller/state.go`, `reposerver/repository/repository.go`
- `CompareAppState()` calls `GetRepoObjs()`, which makes a gRPC call to the repo server (`reposerver/apiclient`) to generate manifests for the target revision.
- The repo server's `GenerateManifests()` (line 1409 of `repository.go`) clones/fetches the git repo, runs the appropriate tool (Helm template, `kustomize build`, or raw YAML), and returns rendered Kubernetes resource manifests.
- Back in the controller, the manifests are diffed against the live cluster state (fetched from `controller/cache.LiveStateCache`) using `gitops-engine/pkg/diff`.
- The resulting `SyncStatus` (`Synced`/`OutOfSync`) and `HealthStatus` are stored on `Application.Status` and persisted via a patch call.

### Stage 4: Sync Operation Executes (kubectl apply + hooks + waves)
- **Files**: `controller/sync.go`, `controller/appcontroller.go`, `gitops-engine/pkg/sync`
- If auto-sync is enabled (or a user triggers sync), `ctrl.autoSync()` (line 1699 of `appcontroller.go`) creates an `Operation` on the `Application`, which is picked up from `appOperationQueue`.
- `SyncAppState()` in `controller/sync.go` (line 90) builds options and calls `sync.NewSyncContext()` from the gitops-engine, wiring in:
  - Hook filtering and ordering (`sync.WithResourcesFilter`)
  - Sync wave delays (`sync.WithSyncWaveHook(delayBetweenSyncWaves)`)
  - Prune policy, dry-run, replace, server-side apply options
- `syncCtx.Sync()` (line 393) executes the sync in ordered phases: **PreSync hooks → Sync wave 0 → Sync wave 1 → ... → PostSync hooks**. Each resource is applied via `kubectl apply` (or server-side apply). Hook Pods are tracked to completion.
- Between waves, `delayBetweenSyncWaves()` (line 557 of `sync.go`) inserts a configurable delay (env var `ARGOCD_SYNC_WAVE_DELAY`, default 2s) to allow controllers to react.
- Results are written to `Application.Status.OperationState` and revision history is persisted.

---

## 6. Adding a New Sync Strategy

To add a new sync strategy — for example, a new hook type or a custom wave behavior — you would need to modify several layers in sequence:

### Step 1: Define the New Option in the API Types
- **File**: `pkg/apis/application/v1alpha1/types.go`
- For a new string-based `SyncOption` flag (like existing `"CreateNamespace=true"`, `"ApplyOutOfSyncOnly=true"`), add a constant in `common/common.go`:
  ```go
  SyncOptionMyNewBehavior = "MyNewBehavior=true"
  ```
- For a structural change (new field on `SyncStrategy`, `SyncPolicy`, etc.), add the typed field with JSON and protobuf tags, then run `make generate` to regenerate deepcopy methods and CRD YAML.

### Step 2: Wire the Option Through the Sync Path
- **File**: `controller/sync.go` — the `SyncAppState()` function (line 90)
- Read the new option from `syncOp.SyncOptions.HasOption(...)` and pass it to the gitops-engine sync context:
  ```go
  sync.WithMyNewBehavior(syncOp.SyncOptions.HasOption(common.SyncOptionMyNewBehavior)),
  ```
- If it requires a new custom sync wave hook, implement the hook function and pass it via `sync.WithSyncWaveHook(myHookFn)`. The existing `delayBetweenSyncWaves` at line 557 is a reference implementation.

### Step 3: Implement the Core Behavior
- **For new hook phases**: Hook lifecycle (`PreSync`, `Sync`, `PostSync`, `SyncFail`, `PostDelete`) is governed by `gitops-engine/pkg/sync/hook`. New hook types require changes there, plus detection logic in `controller/hook.go`.
- **For new wave behaviors**: Modify `delayBetweenSyncWaves()` in `controller/sync.go` or add a new `WithSyncWaveHook` implementation.
- **For new apply strategies**: Implement via a new `sync.With*` option and handler in the gitops-engine `SyncContext`.

### Step 4: Expose the Option in the CLI and API
- **CLI**: `cmd/argocd/commands/app.go` — add the new flag to the `sync` subcommand.
- **API/proto**: If it's a field on `SyncOperation` or `SyncStrategy`, update the protobuf definition in `pkg/apis/application/v1alpha1/` and regenerate with `make protogen`.

### Step 5: Write Tests
- **Unit test**: Add to `controller/sync_test.go` or `controller/state_test.go` verifying the option is correctly read and applied.
- **E2E test**: Add to `test/e2e/sync_options_test.go` (or a new file) using the fixture DSL, e.g.:
  ```go
  func TestMyNewSyncBehavior(t *testing.T) {
      Given(t).
          Path("my-app").
          When().CreateApp().
          AppSyncOptions("MyNewBehavior=true").
          Sync().
          Then().Expect(OperationPhaseIs(OperationSucceeded))
  }
  ```

### Summary of Files to Modify
| File | Purpose |
|------|---------|
| `common/common.go` | Add new constant for the option string |
| `pkg/apis/application/v1alpha1/types.go` | Add new field or document new option |
| `controller/sync.go` | Wire option into `SyncAppState()` (line 90) |
| `controller/hook.go` | (if new hook) hook detection and ordering logic |
| `cmd/argocd/commands/app.go` | CLI flag for user-facing option |
| `controller/sync_test.go` | Unit test coverage |
| `test/e2e/sync_options_test.go` | E2E test coverage |
