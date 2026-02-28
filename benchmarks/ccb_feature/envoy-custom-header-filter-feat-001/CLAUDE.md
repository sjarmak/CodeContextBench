# envoy-custom-header-filter-feat-001: Custom Header Injection Filter

## Task Type: Feature Implementation (HTTP Filter)

Implement an Envoy HTTP filter following extension patterns.

## Key Reference Files
- `source/extensions/filters/http/header_to_metadata/` — reference filter
- `source/extensions/filters/http/common/factory_base.h` — factory base
- `source/common/http/filter_manager.h` — filter interfaces

## Search Strategy
- Search for `StreamDecoderFilter` to find filter interface pattern
- Search for `header_to_metadata` as closest reference implementation
- Search for `RegisterFactory` for factory registration pattern
