# servo-css-container-query-feat-001: CSS Container Queries

## Task Type: Feature Implementation (CSS Specification)

Implement CSS Container Queries (@container) in Servo's style system.

## Key Reference Files
- `components/style/properties/longhands/` — property definitions
- `components/style/stylesheets/rule_parser.rs` — at-rule parsing
- `components/style/stylesheets/container_rule.rs` — container rule (may be a stub)
- `components/style/matching.rs` — style matching/cascade
- `components/style/media_queries/` — reference for conditional rule pattern

## Search Strategy
- Search for `@media` or `media_queries` to understand the conditional rule pattern (container queries follow similar architecture)
- Search for `container` in components/style/ for any existing stubs
- Search for `AtRule` in stylesheets/ to find the at-rule dispatch
- Search for `longhands` to find property definition patterns
- Use `find_references` on `MediaList` to understand how conditional rules integrate with matching
