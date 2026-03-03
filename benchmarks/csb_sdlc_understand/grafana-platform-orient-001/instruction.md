# Onboarding: Grafana Codebase Orientation

**Repository:** grafana/grafana
**Task Type:** Codebase Orientation (analysis only — no code changes)

## Scenario

You are a new platform engineer joining the Grafana team. Your first task is to understand the codebase architecture — how the Go backend, React frontend, plugin system, and provisioning pipeline fit together. The codebase is large (~1.4GB, mixed Go/TypeScript/React), so targeted exploration is essential.

## Your Task

Explore the Grafana codebase and answer the following questions. Write your answers to `/logs/agent/onboarding.md`.

### 1. Main Entry Points
Where is the main server binary entry point? What CLI framework does Grafana use? How does the server bootstrap (what services/registries are initialized at startup)?

### 2. Core Backend Packages
Name at least 5 key Go packages under `pkg/` and describe their responsibilities. Include: API routing, service registry, data source proxy, alerting, and authentication.

### 3. Datasource Plugin Architecture
How does Grafana's plugin system work? Where are built-in datasource plugins defined? How does the backend communicate with plugin processes (gRPC, HTTP)? What is the role of the `grafana-plugin-sdk-go`?

### 4. Dashboard Provisioning Pipeline
Trace how a dashboard defined in a YAML provisioning file gets loaded into Grafana. What is the provisioning service? Where are provisioning configs read from? How do they get persisted to the database?

### 5. Frontend Build System
What frontend framework and build tools does Grafana use? How is the React frontend organized (packages, workspace structure)? Where is the main frontend entry point?

### 6. Extension: Adding a New Panel Plugin
If you needed to add a new visualization panel plugin, what steps would be needed? Which directories and configuration files would you touch? How does the plugin registry discover new panels?

## Output Requirements

Write a markdown document to `/logs/agent/onboarding.md` with numbered sections (1-6) matching the questions above. For each section:
- Be specific: include file paths, package names, function names
- Cite the actual code — reference specific files you explored
- Keep each section focused (2-4 paragraphs)

## Constraints

- Do NOT modify any source files
- Exploration and documentation only
- Be specific — include file paths, package names, function names
