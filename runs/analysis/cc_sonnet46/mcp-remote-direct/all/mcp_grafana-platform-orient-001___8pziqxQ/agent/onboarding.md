# Grafana Codebase Onboarding

## 1. Main Entry Points

### Binary and CLI Framework

The main server binary entry point is `pkg/cmd/grafana/main.go`. The `main()` function calls `MainApp()`, which constructs a `*cli.App` using **`github.com/urfave/cli/v2`** as the CLI framework. The app exposes two primary subcommands:

- `grafana server` — defined in `pkg/cmd/grafana-server/commands`, starts the full Grafana backend
- `grafana cli` — defined in `pkg/cmd/grafana-cli/commands`, for plugin management

The CLI also optionally registers an API server factory subcommand via `server.InitializeAPIServerFactory()`.

### Server Bootstrap

Grafana uses **Google Wire** (`github.com/google/wire`) for compile-time dependency injection. The wire entry point is `pkg/server/wire.go`, which defines several wire sets:

- `wireBasicSet` — the full set of ~100+ service providers wired together
- `wireSet` — extends `wireBasicSet` with metrics, SQL store, OAuth, and notifications
- `wireCLISet` — for CLI target invocations

The top-level `Initialize(cfg, opts, apiOpts)` function in `pkg/server/wire.go` calls `wire.Build(wireExtsSet)`, which resolves the entire dependency graph at compile time.

At runtime, bootstrap proceeds as follows:

1. `server.New(...)` in `pkg/server/server.go` creates the `Server` struct, collecting all background services from the `BackgroundServiceRegistry`.
2. `Server.Init()` writes the PID file, sets Prometheus environment info, calls `roleRegistry.RegisterFixedRoles()`, and then calls `provisioningService.RunInitProvisioners()` — which provisions datasources, plugins, and alerting configs.
3. `Server.Run()` iterates over all `registry.BackgroundService` implementations and starts each in its own goroutine via `errgroup`. It then notifies systemd with `READY=1`.

---

## 2. Core Backend Packages

### `pkg/api`
HTTP API layer. `pkg/api/http_server.go` defines the `HTTPServer` struct, which wires together the route register, middleware, and all API handlers. `pkg/api/api.go` contains `registerRoutes()` which registers all HTTP routes using `pkg/api/routing.RouteRegister`. Routes are organized by resource (dashboards, datasources, users, orgs, plugins, alerting, etc.) with middleware chains for authentication, authorization, and quota enforcement.

### `pkg/registry`
Service registry contracts. Defines the key interfaces: `BackgroundService` (with `Run(ctx context.Context) error`) for long-running services, `CanBeDisabled` for services that may opt out of starting, and `BackgroundServiceRegistry` which provides the ordered list of background services to the server. All services that need to run continuously implement `BackgroundService`.

### `pkg/services/datasourceproxy`
Datasource proxy service (`pkg/services/datasourceproxy/`). Handles proxying HTTP requests from the Grafana frontend through to external datasource backends, attaching authentication headers, handling secrets, and enforcing network access policies. Consumed by `pkg/api/dataproxy.go`.

### `pkg/services/ngalert`
Unified alerting engine (Grafana Alerting). Lives in `pkg/services/ngalert/`. Implements the full alerting lifecycle: rule evaluation, state machine, notification routing via Alertmanager integration, silences, and contact points. The alert rule store lives in `pkg/services/ngalert/store/`, and provisioning of alerting configs is in `pkg/services/provisioning/alerting/`.

### `pkg/services/authn`
Authentication framework. Defined in `pkg/services/authn/authn.go`. Provides a pluggable `Client`-based system with named clients: `auth.client.api-key`, `auth.client.anonymous`, `auth.client.basic`, `auth.client.jwt`, `auth.client.session`, `auth.client.proxy`, `auth.client.saml`, and more. The `authnimpl` package (`pkg/services/authn/authnimpl/`) provides the concrete `AuthnService` implementation that iterates through registered clients to authenticate each request.

### `pkg/setting`
Centralized configuration management. The `Cfg` struct in `pkg/setting/` holds all configuration values loaded from `grafana.ini` / environment variables. Used throughout the codebase as the single source of truth for feature flags, paths, database settings, etc.

### `pkg/infra/db`
Database abstraction layer. Provides the `db.DB` interface backed by `sqlstore.SQLStore` (using **XORM** over SQLite, MySQL, or PostgreSQL). All persistence goes through this layer.

---

## 3. Datasource Plugin Architecture

### Plugin System Overview

Plugins are described by a `plugin.json` manifest file and represented in Go by `plugins.Plugin` (`pkg/plugins/plugins.go`). The `JSONData` struct within captures all manifest fields: `id`, `type`, `name`, `backend`, `executable`, routes, dependencies, etc. Plugin types are: `datasource`, `panel`, `app`, `renderer`, `secretsmanager`.

Plugins are organized into three classes:
- `ClassCore` — bundled with the binary, loaded from `{staticRoot}/app/plugins/datasource` and `{staticRoot}/app/plugins/panel`
- `ClassBundled` — from `cfg.BundledPluginsPath`
- `ClassExternal` — from `cfg.PluginsPath` or per-plugin `path` settings

### Plugin Discovery and Loading

The `pkg/plugins/manager/sources/sources.go` `Service.List()` method enumerates all plugin source directories. Core plugin paths are computed by `corePluginPaths(staticRootPath)` which returns `{staticRoot}/app/plugins/datasource` and `{staticRoot}/app/plugins/panel`.

The `pkg/plugins/manager/loader/loader.go` `Loader.Load()` runs a multi-stage pipeline:
1. **Discover** — finds plugin bundles in the source directory
2. **Bootstrap** — reads `plugin.json`, resolves metadata
3. **Validate** — checks signatures, compatibility
4. **Initialize** — starts the plugin process if it has a backend component

### Backend Communication via gRPC

Backend datasource plugins (those with `"backend": true` in `plugin.json`) are executed as separate processes and communicated with over **gRPC**, using `github.com/hashicorp/go-plugin` as the subprocess manager. The implementation lives in `pkg/plugins/backendplugin/grpcplugin/grpc_plugin.go`.

The `grpcPlugin.Start()` method calls `plugin.NewClient(...)` to spawn the subprocess via `hashicorp/go-plugin`, then negotiates a gRPC connection. All data plane calls (`QueryData`, `CheckHealth`, `CallResource`, `CollectMetrics`, streaming) are proxied over this gRPC connection to the plugin process.

The **`grafana-plugin-sdk-go`** (`github.com/grafana/grafana-plugin-sdk-go`) defines the shared gRPC contracts (`backend.QueryDataHandler`, `backend.CheckHealthHandler`, etc.) that both Grafana and plugin processes implement. The `Plugin` struct in `pkg/plugins/plugins.go` directly implements all these handler interfaces by delegating to its `client` (a `backendplugin.Plugin`).

Built-in datasource backends (Prometheus, Loki, CloudWatch, Elasticsearch, etc.) live in `pkg/tsdb/` and are registered as **core plugins** via Wire in `pkg/server/wire.go` (e.g., `prometheus.ProvideService`, `loki.ProvideService`). These are implemented as `ClassCore` plugins that run in-process rather than as separate subprocesses.

---

## 4. Dashboard Provisioning Pipeline

### Overview

Dashboard provisioning allows dashboards defined as JSON files on disk to be automatically loaded into Grafana. The feature is orchestrated by `pkg/services/provisioning/provisioning.go` (`ProvisioningServiceImpl`), which is a `registry.BackgroundService` registered via Wire.

### Config Reading

Provisioning configs are read from `{cfg.ProvisioningPath}/dashboards/` (typically `conf/provisioning/dashboards/`). The `configReader` in `pkg/services/provisioning/dashboards/config_reader.go` reads all YAML files in that directory using `gopkg.in/yaml.v3`. It supports two config schema versions: a legacy `v0` (list of configs) and the current `v1` (with `apiVersion: 1` field).

A typical v1 config declares a `providers` list, each specifying a `name`, `type: file`, and `options.path` pointing to the directory containing dashboard JSON files.

### Provisioning Execution

When `Server.Run()` calls `ProvisioningServiceImpl.Run()`:

1. `ProvisionDashboards(ctx)` is called first (at startup and on reload).
2. `ProvisioningServiceImpl.setDashboardProvisioner()` instantiates a `dashboards.Provisioner` (`pkg/services/provisioning/dashboards/dashboard.go`) by calling `dashboards.New(ctx, dashboardPath, ...)`.
3. `New()` uses `configReader.readConfig()` to load all YAML provider configs, then creates a `FileReader` (`pkg/services/provisioning/dashboards/file_reader.go`) for each `type: file` provider.
4. `Provisioner.Provision(ctx)` calls `reader.walkDisk(ctx)` on each `FileReader`, which walks the configured directory, reads each `.json` file, and saves it via `dashboards.DashboardProvisioningService`.
5. After initial provision, `Provisioner.PollChanges(ctx)` spawns goroutines calling `reader.pollChanges(ctx)` to continuously watch for file modifications and re-provision changed dashboards.

### Persistence

Dashboards are persisted to the database through `dashboards.DashboardProvisioningService`, backed by `pkg/services/dashboards/database/` (the `DashboardStore`). The provisioning service records a link between the provisioner name and the dashboard in the `dashboard_provisioning` table so Grafana can track which dashboards are under provisioning control.

Note: `Server.Init()` calls `RunInitProvisioners()` which provisions datasources, plugins, and alerting synchronously before background services start. Dashboard provisioning happens later in `Run()` as a background service.

---

## 5. Frontend Build System

### Framework and Build Tools

Grafana's frontend is built with **React** and **TypeScript**. The build system uses **Webpack**, configured in `scripts/webpack/webpack.prod.js` (production) and `scripts/webpack/webpack.dev.js` (development). Package management uses **Yarn** with workspaces. The monorepo is managed with **Nx** (task orchestration) and **Lerna** (package versioning/publishing).

Key build scripts in `package.json`:
- `yarn build` — production Webpack build
- `yarn start` — development Webpack with watch mode
- `yarn test` — Jest unit tests
- `yarn typecheck` — TypeScript type checking across all packages

### Workspace Structure

The frontend is organized into two main areas:

**`packages/`** — Shared npm packages published to the Grafana npm registry:
- `packages/grafana-data` — core data model types (DataFrame, Field, PanelData, PanelPlugin, etc.)
- `packages/grafana-ui` — React component library (shared UI components)
- `packages/grafana-runtime` — runtime API contracts between Grafana and plugins (`setBackendSrv`, `setDataSourceSrv`, `setPluginImportUtils`, etc.)
- `packages/grafana-schema` — CUE-generated TypeScript schema types

**`public/app/`** — Main application source:
- `public/app/features/` — feature-specific React pages and state (dashboards, alerting, explore, etc.)
- `public/app/core/` — shared core utilities and services
- `public/app/plugins/panel/` — built-in panel plugins
- `public/app/plugins/datasource/` — built-in datasource frontend implementations
- `public/app/store/` — Redux store setup

### Main Frontend Entry Point

The main entry point is `public/app/index.ts`, which bootstraps `public/app/app.ts`. The `app.ts` file initializes global singletons from `@grafana/runtime` (e.g., `setBackendSrv`, `setDataSourceSrv`, `setPluginExtensionGetter`, `setCurrentUser`) and mounts the root React component (`AppWrapper.tsx`) using `createRoot` from `react-dom/client`.

---

## 6. Extension: Adding a New Panel Plugin

### Step-by-Step

To add a new built-in visualization panel plugin:

**1. Create the plugin directory:**
```
public/app/plugins/panel/<your-plugin-id>/
```

**2. Create `plugin.json`:**
```json
{
  "type": "panel",
  "name": "My Panel",
  "id": "my-panel-id",
  "info": {
    "description": "Description of the panel",
    "author": { "name": "Grafana Labs", "url": "https://grafana.com" },
    "logos": { "small": "img/icon.svg", "large": "img/icon.svg" }
  }
}
```
See `public/app/plugins/panel/timeseries/plugin.json` as a reference.

**3. Create `module.tsx`** — the main export file that Grafana loads:
```tsx
import { PanelPlugin } from '@grafana/data';
import { MyPanel } from './MyPanel';
import { Options } from './types';

export const plugin = new PanelPlugin<Options>(MyPanel)
  .setPanelOptions((builder) => {
    builder.addTextInput({ path: 'myOption', name: 'My Option', defaultValue: '' });
  });
```
The `PanelPlugin` class is imported from `@grafana/data` (`packages/grafana-data`). See `public/app/plugins/panel/timeseries/module.tsx` as a reference.

**4. Create the React panel component** (e.g., `MyPanel.tsx`) implementing the `PanelProps<Options>` interface from `@grafana/data`.

**5. Optionally create a `panelcfg.cue` schema** for typed options and generate TypeScript types with `panelcfg.gen.ts` — following the pattern used by `timeseries`, `barchart`, etc.

### Plugin Discovery

Core panel plugins are discovered automatically. The Go-side `pkg/plugins/manager/sources/sources.go` `corePluginPaths()` function returns `{staticRoot}/app/plugins/panel` as a scan root. The plugin loader discovers every subdirectory with a `plugin.json` — no manual registration in a Go registry is needed for frontend-only panels.

On the frontend, when a dashboard loads, Grafana uses `@grafana/runtime`'s plugin import utilities (set via `setPluginImportUtils` in `app.ts`) to dynamically import `module.tsx` from the plugin's directory. The exported `plugin` object (a `PanelPlugin` instance) is registered in the runtime panel plugin registry.

### If a Backend Component Is Needed

If the panel plugin requires a Go backend (unusual for panels, common for datasources), you would additionally:
- Add a Go package under `pkg/tsdb/<your-plugin-id>/`
- Implement the `backend.QueryDataHandler` interface from `grafana-plugin-sdk-go`
- Add `ProvideService` and wire it in `pkg/server/wire.go` within `wireBasicSet`
- Set `"backend": true` in `plugin.json`
