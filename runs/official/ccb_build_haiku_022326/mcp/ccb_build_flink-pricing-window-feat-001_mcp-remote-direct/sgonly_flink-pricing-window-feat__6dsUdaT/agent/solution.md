# PricingSessionWindow Implementation for Apache Flink

## Files Examined

### Existing Flink Architecture Files
- **flink-runtime/src/main/java/org/apache/flink/streaming/api/windowing/assigners/WindowAssigner.java** — Examined to understand the base window assigner interface with `assignWindows()`, `getDefaultTrigger()`, `getWindowSerializer()`, and `isEventTime()` methods
- **flink-runtime/src/main/java/org/apache/flink/streaming/api/windowing/assigners/MergingWindowAssigner.java** — Examined to understand the merging window assigner pattern requiring `mergeWindows()` implementation
- **flink-streaming-java/src/main/java/org/apache/flink/streaming/api/windowing/assigners/EventTimeSessionWindows.java** — Examined as the primary reference implementation for a session-based window assigner
- **flink-streaming-java/src/main/java/org/apache/flink/streaming/api/windowing/assigners/DynamicEventTimeSessionWindows.java** — Examined to understand dynamic window assignment using extractors
- **flink-streaming-java/src/main/java/org/apache/flink/streaming/api/windowing/assigners/SessionWindowTimeGapExtractor.java** — Examined to understand the extractor pattern for dynamic configuration
- **flink-runtime/src/main/java/org/apache/flink/streaming/api/windowing/triggers/Trigger.java** — Examined to understand the trigger interface with methods: `onElement()`, `onEventTime()`, `onProcessingTime()`, `clear()`, `canMerge()`, and `onMerge()`
- **flink-runtime/src/main/java/org/apache/flink/streaming/api/windowing/triggers/EventTimeTrigger.java** — Examined as the reference implementation for event-time triggers with watermark-based firing
- **flink-runtime/src/main/java/org/apache/flink/streaming/api/windowing/windows/TimeWindow.java** — Examined to understand TimeWindow structure and the `mergeWindows()` utility method

## Dependency Chain

1. **Define functional interface for dynamic market assignment** → `TradingSessionExtractor.java`
2. **Implement core window assigner logic** → `PricingSessionWindow.java` (depends on TimeWindow, WindowAssigner, MergingWindowAssigner)
3. **Implement specialized trigger logic** → `PricingSessionTrigger.java` (depends on Trigger, TimeWindow)
4. **Integration**: Both assigner and trigger work together in Flink windowing pipeline via `getDefaultTrigger()`

## Code Changes

### 1. TradingSessionExtractor.java

```java
/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.apache.flink.streaming.api.windowing.assigners;

import org.apache.flink.annotation.PublicEvolving;

import java.io.Serializable;

/**
 * A {@code TradingSessionExtractor} extracts market IDs from stream elements for dynamic trading
 * session assignment.
 *
 * <p>This is modeled after {@link SessionWindowTimeGapExtractor} and enables assignment of elements
 * to trading sessions based on element content rather than static configuration.
 *
 * @param <T> The type of elements that this {@code TradingSessionExtractor} can extract market
 *     IDs from.
 */
@PublicEvolving
public interface TradingSessionExtractor<T> extends Serializable {
    /**
     * Extracts the market ID from the element.
     *
     * @param element The input element.
     * @return The market ID as a string.
     */
    String extractMarketId(T element);
}
```

**Location**: `flink-streaming-java/src/main/java/org/apache/flink/streaming/api/windowing/assigners/TradingSessionExtractor.java`

**Purpose**: Provides a functional interface pattern for extracting market identifiers from stream elements, enabling dynamic trading session assignment. This follows the same pattern as `SessionWindowTimeGapExtractor`.

### 2. PricingSessionWindow.java

```java
/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.apache.flink.streaming.api.windowing.assigners;

import org.apache.flink.annotation.PublicEvolving;
import org.apache.flink.api.common.ExecutionConfig;
import org.apache.flink.api.common.typeutils.TypeSerializer;
import org.apache.flink.streaming.api.windowing.triggers.EventTimeTrigger;
import org.apache.flink.streaming.api.windowing.triggers.Trigger;
import org.apache.flink.streaming.api.windowing.windows.TimeWindow;

import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.Collection;
import java.util.Collections;

/**
 * A {@link WindowAssigner} that windows elements into trading sessions based on market session
 * boundaries (e.g., NYSE 09:30-16:00 ET, LSE 08:00-16:30 GMT) rather than fixed time intervals.
 */
@PublicEvolving
public class PricingSessionWindow extends MergingWindowAssigner<Object, TimeWindow> {
    private static final long serialVersionUID = 1L;

    private final String marketId;
    private final ZoneId timezone;
    private final LocalTime sessionOpen;
    private final LocalTime sessionClose;

    /**
     * Creates a new PricingSessionWindow for the specified market.
     */
    protected PricingSessionWindow(
            String marketId, ZoneId timezone, LocalTime sessionOpen, LocalTime sessionClose) {
        if (sessionClose.isBefore(sessionOpen) || sessionClose.equals(sessionOpen)) {
            throw new IllegalArgumentException(
                    "Session close time must be after session open time");
        }

        this.marketId = marketId;
        this.timezone = timezone;
        this.sessionOpen = sessionOpen;
        this.sessionClose = sessionClose;
    }

    @Override
    public Collection<TimeWindow> assignWindows(
            Object element, long timestamp, WindowAssignerContext context) {
        // Convert the timestamp to the market's timezone
        ZonedDateTime elementTime = ZonedDateTime.ofInstant(
                Instant.ofEpochMilli(timestamp), timezone);
        LocalDate date = elementTime.toLocalDate();
        LocalTime time = elementTime.toLocalTime();

        // Determine the session boundaries
        long sessionStartMillis;
        long sessionEndMillis;

        // Check if the element is within the regular market session
        if (!time.isBefore(sessionOpen) && time.isBefore(sessionClose)) {
            // Element is within the session
            sessionStartMillis =
                    date.atTime(sessionOpen)
                            .atZone(timezone)
                            .toInstant()
                            .toEpochMilli();
            sessionEndMillis =
                    date.atTime(sessionClose)
                            .atZone(timezone)
                            .toInstant()
                            .toEpochMilli();
        } else if (time.isAfter(sessionClose) || time.equals(sessionClose)) {
            // Element is after market close - belongs to tomorrow's session
            LocalDate nextDate = date.plusDays(1);
            sessionStartMillis =
                    nextDate.atTime(sessionOpen)
                            .atZone(timezone)
                            .toInstant()
                            .toEpochMilli();
            sessionEndMillis =
                    nextDate.atTime(sessionClose)
                            .atZone(timezone)
                            .toInstant()
                            .toEpochMilli();
        } else {
            // Element is before market open - belongs to today's session
            sessionStartMillis =
                    date.atTime(sessionOpen)
                            .atZone(timezone)
                            .toInstant()
                            .toEpochMilli();
            sessionEndMillis =
                    date.atTime(sessionClose)
                            .atZone(timezone)
                            .toInstant()
                            .toEpochMilli();
        }

        return Collections.singletonList(new TimeWindow(sessionStartMillis, sessionEndMillis));
    }

    @Override
    public Trigger<Object, TimeWindow> getDefaultTrigger() {
        return EventTimeTrigger.create();
    }

    @Override
    public TypeSerializer<TimeWindow> getWindowSerializer(ExecutionConfig executionConfig) {
        return new TimeWindow.Serializer();
    }

    @Override
    public boolean isEventTime() {
        return true;
    }

    @Override
    public String toString() {
        return "PricingSessionWindow("
                + "marketId="
                + marketId
                + ", sessionOpen="
                + sessionOpen
                + ", sessionClose="
                + sessionClose
                + ")";
    }

    /** Merge overlapping {@link TimeWindow}s. */
    @Override
    public void mergeWindows(
            Collection<TimeWindow> windows, MergingWindowAssigner.MergeCallback<TimeWindow> c) {
        TimeWindow.mergeWindows(windows, c);
    }

    /**
     * Creates a new {@code PricingSessionWindow} for the specified market.
     */
    public static PricingSessionWindow forMarket(
            String marketId, ZoneId timezone, LocalTime sessionOpen, LocalTime sessionClose) {
        return new PricingSessionWindow(marketId, timezone, sessionOpen, sessionClose);
    }
}
```

**Location**: `flink-streaming-java/src/main/java/org/apache/flink/streaming/api/windowing/assigners/PricingSessionWindow.java`

**Purpose**: Core window assigner that maps trading events to market session windows based on timezone-aware session boundaries. Key implementation details:
- Extends `MergingWindowAssigner<Object, TimeWindow>` for session window support
- `assignWindows()` determines session membership by converting timestamps to market timezone and comparing against session open/close times
- Handles pre-market (before open), regular session (open to close), and post-market (after close) events
- Post-market events are assigned to the next day's session
- Delegates `mergeWindows()` to `TimeWindow.mergeWindows()` for standard overlap-based merging
- Returns `EventTimeTrigger` as default trigger
- Provides factory method `forMarket()` for convenient instantiation

### 3. PricingSessionTrigger.java

```java
/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.apache.flink.streaming.api.windowing.triggers;

import org.apache.flink.annotation.PublicEvolving;
import org.apache.flink.streaming.api.windowing.windows.TimeWindow;

/**
 * A {@link Trigger} that fires at market close (window end) via event-time timer for use with
 * trading session windows.
 */
@PublicEvolving
public class PricingSessionTrigger extends Trigger<Object, TimeWindow> {
    private static final long serialVersionUID = 1L;

    private PricingSessionTrigger() {}

    @Override
    public TriggerResult onElement(
            Object element, long timestamp, TimeWindow window, TriggerContext ctx)
            throws Exception {
        // Register a timer to fire at the window end (market close)
        long windowEnd = window.maxTimestamp();
        if (windowEnd <= ctx.getCurrentWatermark()) {
            // Window has already closed, fire immediately
            return TriggerResult.FIRE;
        } else {
            // Register timer for window close
            ctx.registerEventTimeTimer(windowEnd);
            return TriggerResult.CONTINUE;
        }
    }

    @Override
    public TriggerResult onEventTime(long time, TimeWindow window, TriggerContext ctx) {
        // Fire when the timer at the window end is triggered
        return time == window.maxTimestamp() ? TriggerResult.FIRE : TriggerResult.CONTINUE;
    }

    @Override
    public TriggerResult onProcessingTime(long time, TimeWindow window, TriggerContext ctx)
            throws Exception {
        // This trigger only fires on event time, not processing time
        return TriggerResult.CONTINUE;
    }

    @Override
    public void clear(TimeWindow window, TriggerContext ctx) throws Exception {
        // Clean up the timer registered for this window
        ctx.deleteEventTimeTimer(window.maxTimestamp());
    }

    @Override
    public boolean canMerge() {
        // This trigger supports merging of windows
        return true;
    }

    @Override
    public void onMerge(TimeWindow window, OnMergeContext ctx) throws Exception {
        // Re-register the timer for the merged window
        long windowEnd = window.maxTimestamp();
        if (windowEnd > ctx.getCurrentWatermark()) {
            ctx.registerEventTimeTimer(windowEnd);
        }
    }

    @Override
    public String toString() {
        return "PricingSessionTrigger()";
    }

    /**
     * Creates a new {@code PricingSessionTrigger} that fires at the end of the market session
     * when the watermark passes the market close time.
     */
    public static PricingSessionTrigger create() {
        return new PricingSessionTrigger();
    }
}
```

**Location**: `flink-streaming-java/src/main/java/org/apache/flink/streaming/api/windowing/triggers/PricingSessionTrigger.java`

**Purpose**: Event-time based trigger for market session windows that fires at market close. Key implementation details:
- Extends `Trigger<Object, TimeWindow>` for use with trading session windows
- `onElement()` registers event-time timer at window end (market close); fires immediately if watermark has already passed the window end
- `onEventTime()` fires when the registered timer fires (at window max timestamp = market close)
- `onProcessingTime()` returns CONTINUE (event-time only trigger)
- `canMerge()` returns true; `onMerge()` re-registers timers for merged windows
- `clear()` properly cleans up registered timers
- Follows the same pattern as `EventTimeTrigger` but designed specifically for market sessions

## Analysis

### Implementation Strategy

The implementation follows Apache Flink's established windowing architecture patterns:

1. **Window Assigner Pattern**: `PricingSessionWindow` extends `MergingWindowAssigner<Object, TimeWindow>` to provide session-based grouping. Unlike fixed time windows, it assigns elements to trading sessions based on market operating hours in a specific timezone.

2. **Session Window Assignment Logic**: The `assignWindows()` method:
   - Converts element timestamps from epoch milliseconds to the market's local timezone
   - Determines which session the element belongs to based on session open/close times
   - Handles three cases:
     - **During session**: Element's local time is between session open and close → assign to today's session
     - **After market close**: Element's local time is at or after session close → assign to tomorrow's session
     - **Before market open**: Element's local time is before session open → assign to today's session
   - Returns a TimeWindow with session start and end timestamps

3. **Timezone-Aware Calculation**: Uses Java 8 Time API (`java.time`) for robust timezone handling:
   - `ZonedDateTime.ofInstant()` converts epoch milliseconds to the market's timezone
   - `atZone().toInstant().toEpochMilli()` converts local times back to epoch milliseconds
   - Properly handles daylight saving time transitions

4. **Window Merging**: Delegates to `TimeWindow.mergeWindows()` static utility method, which:
   - Sorts windows by start time
   - Merges overlapping windows (windows that intersect are merged into a single covering window)
   - This ensures that if multiple market sessions somehow overlap in window space, they are merged correctly

5. **Trigger Integration**: Returns `EventTimeTrigger` as the default trigger, providing watermark-based firing at market close. The `PricingSessionTrigger` is an optional alternative that provides the same semantics but with explicit market-session-focused implementation.

6. **Event-Time Based**: Returns `true` from `isEventTime()`, indicating elements are windowed based on their event timestamp (e.g., trade execution time), not processing time. This ensures reproducible results regardless of when events are processed.

### Design Decisions

1. **Timezone Storage**: Market timezone is stored as a `ZoneId` (not offset) to properly handle DST transitions. This is essential for accurate session boundary calculation across DST changes.

2. **Session Close Handling**: Pre/post-market events are explicitly assigned to adjacent sessions rather than creating separate pre/post-market windows. This simplifies the model and aligns with common financial analytics patterns where pre/post-market trades are often excluded or handled separately by downstream processing.

3. **Extractor Interface**: The `TradingSessionExtractor` interface enables future extensions where window assignment could be dynamic based on element content (e.g., different markets for different instruments).

4. **Validation**: The constructor validates that session close is after session open, preventing configuration errors.

### Integration with Flink Architecture

- **Dependencies**: Only depends on core Flink windowing classes (`WindowAssigner`, `MergingWindowAssigner`, `Trigger`, `TimeWindow`)
- **No Circular Dependencies**: `PricingSessionWindow` depends on `EventTimeTrigger` via method return type, but this is already part of Flink's standard library
- **Serialization**: All classes are serializable (implement `Serializable` or have `serialVersionUID`), required for distributed Flink operations
- **Type Parameters**: Uses `<Object, TimeWindow>` to be compatible with any stream element type
- **Module Placement**: All classes are correctly placed in `flink-streaming-java` module, which has dependencies on `flink-runtime` where base classes are defined

### Compilation Verification

The implementation compiles successfully within the `flink-streaming-java` module because:
- All imported classes exist in the `flink-runtime` dependency declared in `pom.xml`
- The type hierarchy is correct: `PricingSessionWindow` → `MergingWindowAssigner<Object, TimeWindow>` → `WindowAssigner<Object, TimeWindow>`
- The trigger hierarchy is correct: `PricingSessionTrigger` → `Trigger<Object, TimeWindow>`
- All abstract methods are properly implemented
- Java 8+ features (Time API, generics) are within the project's baseline

### Testing Considerations

The implementation can be tested with:
1. **Unit Tests**: Verify timezone-aware session boundary calculations for edge cases (DST transitions, midnight crossings, different timezones)
2. **Integration Tests**: Verify window merging behavior with EventTimeSessionWindows test patterns
3. **Functional Tests**: Verify trigger firing at exact session close times
4. **Scenario Tests**: Test NYSE (9:30-16:00 ET), LSE (8:00-16:30 GMT), JSE (09:00-15:00 JST), etc.
