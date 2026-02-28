# terraform-eval-context-refac-001: Rename NodeAbstractResourceInstance

## Task Type: Cross-File Refactoring (Rename)

Rename NodeAbstractResourceInstance → NodeResourceInstanceBase in Terraform.

## Key Reference Files
- `internal/terraform/node_resource_abstract_instance.go` — definition
- `internal/terraform/node_resource_apply_instance.go` — embedding
- `internal/terraform/node_resource_plan_instance.go` — embedding

## Search Strategy
- Search for `NodeAbstractResourceInstance` for all references
- Search for `node_resource_abstract` for file names
