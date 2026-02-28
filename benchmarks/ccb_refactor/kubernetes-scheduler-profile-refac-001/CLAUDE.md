# kubernetes-scheduler-profile-refac-001: Rename SchedulerProfile

## Task Type: Cross-File Refactoring (Rename)

Rename SchedulerProfile → SchedulingProfile in Kubernetes scheduler.

## Key Reference Files
- `pkg/scheduler/profile/` — profile definition
- `pkg/scheduler/scheduler.go` — usage
- `staging/src/k8s.io/kube-scheduler/` — API types

## Search Strategy
- Search for `SchedulerProfile` across the codebase
- Search for `type SchedulerProfile` for definition
