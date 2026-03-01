# flink-window-late-data-fix-001: Late Data Side Output for Merging Windows

## Task Type: Bug Fix (Windowing Operator)

Fix silent late data dropping in Flink's merging window operator side output path.

## Key Reference Files
- `flink-streaming-java/src/main/java/org/apache/flink/streaming/runtime/operators/windowing/WindowOperator.java` — main target
- `flink-streaming-java/src/main/java/org/apache/flink/streaming/runtime/operators/windowing/EvictingWindowOperator.java` — evicting variant
- `flink-runtime/src/main/java/org/apache/flink/streaming/api/windowing/assigners/MergingWindowAssigner.java` — merge base
- `flink-streaming-java/src/test/java/org/apache/flink/streaming/runtime/operators/windowing/WindowOperatorTest.java` — tests

## Search Strategy
- Search for `isElementLate` in WindowOperator to find the lateness check
- Search for `sideOutputLateData` to find the API and where it's wired
- Search for `OutputTag` in the windowing package to understand side output dispatch
- Search for `mergingWindowsByKey` or `MergingWindowSet` to understand merge semantics
- Use `find_references` on `isElementLate` to see all callers
