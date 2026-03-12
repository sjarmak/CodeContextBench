# Grafana Codebase Onboarding

## 1. Main Entry Points

### Binary Entry Point

The main Grafana server binary entry point is `pkg/cmd/grafana/main.go`. The `main()` function calls `MainApp()`, which constructs a `*cli.App` using **`github.com/urfave/cli/v2`** as the CLI framework. The app registers two top-level subcommands:

- `grafana server` — via `commands.ServerCommand()` from `pkg/cmd/grafana-server/commands`
- `grafana cli` — via `gcli.CLICommand()` from `pkg/cmd/grafana-cli/commands`

There is also a legacy entry point at `pkg/cmd/grafana-server/main.go` for backward compatibility.

### Server Bootstrap

Grafana uses **Google Wire** (`github.com/google/wire`) for dependency injection. The wiring is declared in `pkg/server/wire.go` (build tag `wireinject`). The `Initialize()` function calls `wire.Build(wireExtsSet)`, which wires together the entire dependency graph — over 100 `Provide*` functions — producing a fully initialized `*Server`.

The bootstrap sequence proceeds as follows:

1. `server.New()` (`pkg/server/server.go`) receives an `*api.HTTPServer`, a `provisioning.ProvisioningService`, a `registry.BackgroundServiceRegistry`, and other wired dependencies.
2. `Server.Init()` is called, which:
   - Writes a PID file
   - Registers fixed RBAC roles via `roleRegistry.RegisterFixedRoles()`
   - Calls `provisioningService.RunInitProvisioners()` — this synchronously provisions datasources, plugins, and alerting from YAML configs before the server accepts traffic.
3. `Server.Run()` starts all registered `registry.BackgroundService` implementations concurrently using `errgroup`, including the HTTP server, alerting engine, provisioning poller, live service, rendering service, and more.
4. When all services are running, Grafana sends `READY=1` to systemd via the notify socket.

The background service registry is assembled in `pkg/registry/backgroundsvcs/background_services.go` via `ProvideBackgroundServiceRegistry()`, which lists every long-running service as a constructor argument. The `registry.BackgroundService` interface (`pkg/registry/registry.go`) requires only a `Run(ctx context.Context) error` method; services that can be disabled implement `CanBeDisabled`.

---

## 2. Core Backend Packages

### `pkg/api` — HTTP Server and Route Registration

`pkg/api` contains the `HTTPServer` struct and the `registerRoutes()` function (`pkg/api/api.go`). All HTTP routes are registered here against a `routing.RouteRegister` (interface in `pkg/api/routing/`). Routes use middleware chains composed from `pkg/middleware` (auth, quota, CSRF, logging). The frontend settings endpoint in `pkg/api/frontendsettings.go` is particularly important — it serializes the plugin registry into the `config.panels` and `config.datasources` maps consumed by the React app at boot.

### `pkg/registry` — Service Registry Interfaces

`pkg/registry/registry.go` defines the core interfaces: `BackgroundService` (any long-running service), `CanBeDisabled` (opt-out of startup), `UsageStatsProvidersRegistry`, and `DatabaseMigrator`. `pkg/registry/backgroundsvcs/background_services.go` contains the concrete `BackgroundServiceRegistry` that collects all background services for the server's run loop.

### `pkg/services/datasourceproxy` — Datasource Proxy

`pkg/services/datasourceproxy/datasourceproxy.go` contains `DataSourceProxyService`. Its `ProxyDataSourceRequest()` method handles all `/api/datasources/proxy/:id/*` requests: it looks up the datasource by ID from the cache, validates the request via the plugin request validator, resolves OAuth tokens, and then delegates to `pkg/api/pluginproxy` to forward the HTTP request to the actual datasource backend. This service decouples the browser from direct datasource network access, applying authentication and secret injection.

### `pkg/services/ngalert` — Unified Alerting

`pkg/services/ngalert/ngalert.go` hosts `AlertNG`, the Next Generation (Unified) Alerting service. It wires together an evaluation scheduler (`schedule`), a notifier (Alertmanager), an expression engine (`expr`), a rule store backed by SQL (`store.DBstore`), state machine (`state`), image rendering (`image`), and a provisioning sub-package (`provisioning`). `AlertNG` implements `registry.BackgroundService` and `registry.CanBeDisabled`. It registers its own HTTP API routes under `/api/v1/provisioning/` and `/api/alertmanager/`.

### `pkg/services/authn` — Authentication

`pkg/services/authn/authn.go` defines the `Service` interface and the `Client` pluggable authenticator concept. The service supports multiple auth clients identified by constants like `ClientAPIKey`, `ClientSession`, `ClientBasic`, `ClientJWT`, `ClientProxy`, `ClientSAML`, and `ClientAnonymous`. The concrete implementation lives in `pkg/services/authn/authnimpl/`. Each client implements credential extraction and identity lookup; the service tries clients in priority order and synchronizes the resulting identity to the DB when `SyncUser` is set.

### Additional Key Packages

- **`pkg/setting`** — Reads `grafana.ini` and environment variable overrides into a `*setting.Cfg` struct; the single source of truth for all configuration.
- **`pkg/infra/db`** — Database abstraction over SQLite/MySQL/PostgreSQL via XORM, used by all services for persistence.
- **`pkg/services/featuremgmt`** — Feature flag management; gates new features via `featuremgmt.FeatureToggles`.
- **`pkg/plugins`** — Core plugin model: the `Plugin` struct, `BackendFactoryProvider`, and `PluginSource` interfaces used throughout the plugin subsystem.

---

## 3. Datasource Plugin Architecture

### Plugin System Overview

Grafana's plugin system is organized around a **load pipeline** in `pkg/plugins/manager/`. The `Loader` struct (`pkg/plugins/manager/loader/loader.go`) orchestrates four sequential pipeline stages:

1. **Discovery** (`pipeline/discovery/`) — finds plugin bundles from a `plugins.PluginSource` (local disk, bundled, CDN). The default `FindFunc` walks the filesystem looking for `plugin.json` manifests.
2. **Bootstrap** (`pipeline/bootstrap/`) — reads `plugin.json`, constructs the `*plugins.Plugin` struct, sets class (Core, Bundled, External), and resolves dependencies.
3. **Validation** (`pipeline/validation/`) — verifies plugin signatures.
4. **Initialization** (`pipeline/initialization/`) — for backend plugins, calls `BackendClientInit.Initialize()` which uses `plugins.BackendFactoryProvider` to create a backend client and registers it on the plugin via `p.RegisterClient(backendClient)`.

### Built-in Datasource Plugins

Built-in datasource backends (server-side query execution) live in `pkg/tsdb/`: `prometheus`, `loki`, `cloudwatch`, `azuremonitor`, `cloud-monitoring`, `elasticsearch`, `graphite`, `influxdb`, `mysql`, `mssql`, `grafana-postgresql-datasource`, `tempo`, `pyroscope`, `parca`, and others. Each sub-package exports a `ProvideService()` function wired into the server via `pkg/server/wire.go`. Their frontend counterparts (query editors, config UI) live under `public/app/plugins/datasource/`.

### Backend Plugin Communication (gRPC)

External backend plugins run as **child processes** and communicate over gRPC using the **`github.com/hashicorp/go-plugin`** framework. The implementation is in `pkg/plugins/backendplugin/grpcplugin/grpc_plugin.go`. The `grpcPlugin` struct holds a `*plugin.Client` (from hashicorp/go-plugin) and a `*ClientV2`. When `Start()` is called, it spawns the plugin subprocess and establishes a gRPC connection. The gRPC protobuf contracts are defined by **`grafana-plugin-sdk-go`** (`github.com/grafana/grafana-plugin-sdk-go`), which provides the `backend` package with interfaces like `QueryDataHandler`, `CheckHealthHandler`, `CallResourceHandler`, and `StreamHandler`. The `Plugin` struct in `pkg/plugins/plugins.go` directly implements these interfaces, delegating to the backend client.

### Role of `grafana-plugin-sdk-go`

The SDK (`github.com/grafana/grafana-plugin-sdk-go`) defines the shared contract between Grafana and backend plugins:
- gRPC service definitions (proto-generated code in `backend/`)
- Data frame types (`data.Frame`) for query results
- HTTP client utilities (`backend/httpclient`)
- Plugin lifecycle management interfaces

Both the Grafana server (as gRPC client) and plugin processes (as gRPC server) import this SDK, ensuring type-safe communication.

---

## 4. Dashboard Provisioning Pipeline

### Provisioning Service

`pkg/services/provisioning/provisioning.go` contains `ProvisioningServiceImpl`, which implements both `registry.BackgroundService` (for continuous polling) and `ProvisioningService`. It is constructed via `ProvideService()` (a Wire provider). On startup, `Server.Init()` calls `RunInitProvisioners()`, which synchronously provisions datasources, plugins, and alerting. Dashboard provisioning runs slightly later in `Server.Run()` via the `ProvisioningServiceImpl.Run()` background loop.

### Config File Reading

Dashboard provisioning config is read from `{cfg.ProvisioningPath}/dashboards/` (default: `conf/provisioning/dashboards/`). The `configReader` struct in `pkg/services/provisioning/dashboards/config_reader.go` scans this directory for `*.yaml`/`*.yml` files. It supports two schema versions:
- **v0** (legacy): a plain YAML list
- **v1** (current): a struct with `apiVersion: 1` and a `providers` list

Each provider config specifies a `name`, `orgId`, `type: file`, `folder`, `folderUID`, and `options.path` pointing to a directory of dashboard JSON files.

### File Reader and DB Persistence

For each provider config, a `FileReader` is created (`pkg/services/provisioning/dashboards/file_reader.go`). The `FileReader.walkDisk()` method recursively scans the configured `path` for `*.json` files. For each discovered JSON file it computes a hash; if the hash has changed (or the dashboard is new), it calls:

```
fr.dashboardProvisioningService.SaveProvisionedDashboard(ctx, dash, dp)
```

`dashboardProvisioningService` is the `dashboards.DashboardProvisioningService` interface, implemented in `pkg/services/dashboards/service/`. `SaveProvisionedDashboard` writes the dashboard JSON into the `dashboard` SQL table and records provisioning metadata (file path, checksum) in the `dashboard_provisioning` table, linking the dashboard to its on-disk source. The `FileReader.pollChanges()` method runs on a configurable interval (default 30s) to detect file changes and re-sync.

Orphaned dashboards (those previously provisioned from a file that no longer exists) are cleaned up via `CleanUpOrphanedDashboards()` before each provisioning cycle.

---

## 5. Frontend Build System

### Framework and Build Tools

The Grafana frontend is built with **React** (TypeScript). The build system uses **Webpack** with configurations in `scripts/webpack/` (`webpack.common.js`, `webpack.dev.js`, `webpack.prod.js`). The package manager is **Yarn** with **Nx** for monorepo task orchestration (`nx.json`). **Lerna** manages package versioning (`lerna.json`).

Key build scripts (from `package.json`):
- `yarn build` — production Webpack build (`NODE_ENV=production`)
- `yarn dev` — development Webpack build with watch
- `yarn test` — Jest test runner
- `yarn packages:build` — builds all `@grafana/*` packages via Nx

### Workspace Structure

The monorepo contains two layers of frontend code:

**`packages/`** — Published `@grafana/*` npm packages (also used internally):
- `grafana-data` — core data types: `DataFrame`, `Field`, `PanelPlugin`, `DataSourcePlugin`, query interfaces
- `grafana-ui` — React component library (UI primitives, form controls, visualizations)
- `grafana-runtime` — runtime interfaces (`BackendSrv`, `DataSourceSrv`, `LocationService`) and plugin registration hooks
- `grafana-schema` — CUE-generated TypeScript types for panel/datasource configs
- `grafana-prometheus`, `grafana-sql` — shared datasource utilities

**`public/app/`** — The application itself:
- `public/app/app.ts` — **main frontend entry point**; bootstraps React, registers global services, initializes i18n, and mounts `<AppWrapper>`
- `public/app/core/` — core services, context, routing utilities
- `public/app/features/` — feature modules (dashboard, explore, alerting, plugins admin, etc.)
- `public/app/plugins/panel/` — 32 built-in panel plugins (barchart, gauge, timeseries, geomap, etc.)
- `public/app/plugins/datasource/` — built-in datasource frontend plugins

### Main Frontend Entry Point

`public/app/app.ts` imports `@grafana/runtime` service setters and calls them to register implementations (e.g. `setBackendSrv`, `setDataSourceSrv`, `setLocationSrv`). It then calls `createRoot(document.getElementById('reactRoot')).render(createElement(AppWrapper, ...))` to mount the React tree. The `AppWrapper` component (`public/app/AppWrapper.tsx`) sets up Redux store, routing, and the main application chrome.

---

## 6. Extension: Adding a New Panel Plugin

### Step 1: Create the Plugin Directory

Create a new directory under `public/app/plugins/panel/<your-plugin-id>/`. The plugin ID must be lowercase and unique (e.g. `myteam-heatmapv2`).

### Step 2: Define `plugin.json`

Create `public/app/plugins/panel/<your-plugin-id>/plugin.json`:
```json
{
  "type": "panel",
  "name": "My Panel",
  "id": "myteam-heatmapv2",
  "info": {
    "description": "Custom heatmap panel",
    "author": { "name": "My Team" },
    "logos": {
      "small": "img/icon.svg",
      "large": "img/icon.svg"
    }
  }
}
```

### Step 3: Create `module.tsx`

Export a `PanelPlugin` instance from `module.tsx`:
```typescript
import { PanelPlugin } from '@grafana/data';
import { MyPanel } from './MyPanel';
import { Options, defaultOptions } from './panelcfg.gen';

export const plugin = new PanelPlugin<Options>(MyPanel)
  .setPanelOptions((builder) => {
    builder.addBooleanSwitch({ path: 'showLegend', name: 'Show legend', defaultValue: true });
  });
```

The `PanelPlugin` class is from `@grafana/data` (`packages/grafana-data`). The React component receives `PanelProps<Options>` typed props.

### Step 4: Register in the Webpack Build

Built-in plugins are bundled as separate Webpack entry points. Examine `scripts/webpack/plugins/` or `scripts/webpack/webpack.common.js` to see how panel entry points are resolved. Each `public/app/plugins/panel/<id>/module.tsx` is automatically discovered as a separate chunk.

### Step 5: How the Plugin Registry Discovers the Panel

At runtime, the backend API handler in `pkg/api/frontendsettings.go` (`getFrontendSettings()`) iterates over `availablePlugins[plugins.TypePanel]` — the set of all loaded `*plugins.Plugin` structs of type `panel` from the `pluginstore.Store`. For each panel it constructs a `plugins.PanelDTO` and serializes it into the `panels` map in the JSON response to `/api/frontend/settings`.

The React app receives this JSON and populates `config.panels` (imported from `app/core/config`). When a dashboard panel renders, `importPanelPlugin(id)` in `public/app/features/plugins/importPanelPlugin.ts` looks up `config.panels[id]` for the plugin metadata and then calls `importPluginModule()` to dynamically import the `module.tsx` chunk. The exported `plugin` object (a `PanelPlugin` instance) drives the rendering, options editor, and field config UI.

For **backend plugins** (e.g. if your panel needs server-side processing), you would additionally create a Go package under `pkg/tsdb/` or implement a separate plugin process using `grafana-plugin-sdk-go`, register it in `pkg/server/wire.go`, and mark `"backend": true` in `plugin.json`.

### Files to Touch Summary

| File/Directory | Purpose |
|---|---|
| `public/app/plugins/panel/<id>/plugin.json` | Plugin manifest and metadata |
| `public/app/plugins/panel/<id>/module.tsx` | Entry point exporting `PanelPlugin` instance |
| `public/app/plugins/panel/<id>/MyPanel.tsx` | React panel component |
| `public/app/plugins/panel/<id>/panelcfg.gen.ts` | TypeScript options types (from CUE schema) |
| `public/app/plugins/panel/<id>/img/` | Plugin icons |
| `pkg/server/wire.go` | Only needed for Go backend plugins |
| `pkg/tsdb/<id>/` | Go backend query handler (backend plugins only) |
