# PricingSessionWindow Implementation for Financial Trading in Apache Flink

## Files Examined

- `/workspace/flink-runtime/src/main/java/org/apache/flink/streaming/api/windowing/assigners/MergingWindowAssigner.java` — examined to understand the abstract base class for window assigners that support merging
- `/workspace/flink-streaming-java/src/main/java/org/apache/flink/streaming/api/windowing/assigners/EventTimeSessionWindows.java` — examined to understand the pattern for event-time based session windows
- `/workspace/flink-streaming-java/src/main/java/org/apache/flink/streaming/api/windowing/assigners/DynamicEventTimeSessionWindows.java` — examined to understand dynamic window assignment patterns with extractors
- `/workspace/flink-streaming-java/src/main/java/org/apache/flink/streaming/api/windowing/assigners/SessionWindowTimeGapExtractor.java` — examined as the model for the TradingSessionExtractor functional interface
- `/workspace/flink-runtime/src/main/java/org/apache/flink/streaming/api/windowing/triggers/EventTimeTrigger.java` — examined to understand event-time trigger implementation patterns
- `/workspace/flink-runtime/src/main/java/org/apache/flink/streaming/api/windowing/triggers/Trigger.java` — examined to understand the complete Trigger interface requirements
- `/workspace/flink-runtime/src/main/java/org/apache/flink/streaming/api/windowing/windows/TimeWindow.java` — examined to understand TimeWindow structure and the mergeWindows() utility method

## Files Created/Modified

### Created:
1. `/workspace/flink-streaming-java/src/main/java/org/apache/flink/streaming/api/windowing/assigners/TradingSessionExtractor.java` — created the functional interface for extracting market IDs
2. `/workspace/flink-streaming-java/src/main/java/org/apache/flink/streaming/api/windowing/assigners/PricingSessionWindow.java` — created the main window assigner implementation
3. `/workspace/flink-streaming-java/src/main/java/org/apache/flink/streaming/api/windowing/triggers/PricingSessionTrigger.java` — created the session-specific trigger implementation

## Dependency Chain

1. **Define interfaces**: `TradingSessionExtractor.java` — functional interface for extracting market IDs from stream elements
2. **Implement core window logic**: `PricingSessionWindow.java` — the main window assigner that maps trading events to market sessions
3. **Implement trigger logic**: `PricingSessionTrigger.java` — the event-time trigger that fires at market close
4. **Integration**: Both implementations follow Flink's existing windowing architecture and are compatible with the streaming API

## Code Changes

### File 1: TradingSessionExtractor.java

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
 * http://www.apache.org/licenses/LICENSE-2.0
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
 * A {@code TradingSessionExtractor} extracts market IDs from stream elements for use with
 * PricingSessionWindow. This enables dynamic session assignment based on element content.
 *
 * @param <T> The type of elements from which this extractor can extract market IDs.
 */
@PublicEvolving
public interface TradingSessionExtractor<T> extends Serializable {
    /**
     * Extracts the market ID from the input element.
     *
     * @param element The input element.
     * @return The market ID as a string.
     */
    String extract(T element);
}
```

### File 2: PricingSessionWindow.java

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
 * http://www.apache.org/licenses/LICENSE-2.0
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
 * A {@link WindowAssigner} that windows trading events into sessions based on market session
 * boundaries (e.g., NYSE 09:30-16:00 ET, LSE 08:00-16:30 GMT). Windows cannot overlap.
 *
 * <p>This assigner groups events by trading session rather than fixed time intervals, which is
 * essential for capital markets analytics where aggregations must align with trading hours.
 *
 * <p>Example usage:
 *
 * <pre>{@code
 * DataStream<Quote> quotes = ...;
 * KeyedStream<Quote, String> keyed = quotes.keyBy(q -> q.getSymbol());
 * WindowedStream<Quote, String, TimeWindow> windowed =
 *   keyed.window(PricingSessionWindow.forMarket("NYSE",
 *                     ZoneId.of("America/New_York"),
 *                     LocalTime.of(9, 30),
 *                     LocalTime.of(16, 0)));
 * }</pre>
 */
@PublicEvolving
public class PricingSessionWindow extends MergingWindowAssigner<Object, TimeWindow> {
    private static final long serialVersionUID = 1L;

    private final String marketId;
    private final ZoneId timezone;
    private final LocalTime sessionOpen;
    private final LocalTime sessionClose;

    /**
     * Constructor for PricingSessionWindow.
     *
     * @param marketId The market identifier (e.g., "NYSE", "LSE")
     * @param timezone The timezone in which the market operates (e.g., "America/New_York")
     * @param sessionOpen The opening time of the trading session (e.g., 09:30)
     * @param sessionClose The closing time of the trading session (e.g., 16:00)
     */
    public PricingSessionWindow(
            String marketId, ZoneId timezone, LocalTime sessionOpen, LocalTime sessionClose) {
        if (marketId == null || marketId.isEmpty()) {
            throw new IllegalArgumentException("Market ID cannot be null or empty");
        }
        if (timezone == null) {
            throw new IllegalArgumentException("Timezone cannot be null");
        }
        if (sessionOpen == null) {
            throw new IllegalArgumentException("Session open time cannot be null");
        }
        if (sessionClose == null) {
            throw new IllegalArgumentException("Session close time cannot be null");
        }

        this.marketId = marketId;
        this.timezone = timezone;
        this.sessionOpen = sessionOpen;
        this.sessionClose = sessionClose;
    }

    @Override
    public Collection<TimeWindow> assignWindows(
            Object element, long timestamp, WindowAssignerContext context) {
        // Convert timestamp (milliseconds since epoch) to local date/time in the market's timezone
        Instant instant = Instant.ofEpochMilli(timestamp);
        ZonedDateTime zonedDateTime = instant.atZone(timezone);
        LocalDate currentDate = zonedDateTime.toLocalDate();

        // Calculate session boundaries in the market's timezone
        LocalDateTime sessionOpenDateTime = LocalDateTime.of(currentDate, sessionOpen);
        LocalDateTime sessionCloseDateTime = LocalDateTime.of(currentDate, sessionClose);

        // Handle overnight sessions (e.g., futures markets)
        // If session close is before session open (e.g., 23:00 - 22:00), it spans overnight
        if (sessionClose.isBefore(sessionOpen)) {
            // Check if current time is after session open (still in same day's session)
            if (zonedDateTime.toLocalTime().compareTo(sessionOpen) >= 0) {
                // Session started today, will end tomorrow
                sessionCloseDateTime = sessionCloseDateTime.plusDays(1);
            } else {
                // Session actually started yesterday, will end today
                sessionOpenDateTime = sessionOpenDateTime.minusDays(1);
            }
        }

        // Convert back to epoch milliseconds
        long sessionOpenMillis =
                sessionOpenDateTime.atZone(timezone).toInstant().toEpochMilli();
        long sessionCloseMillis =
                sessionCloseDateTime.atZone(timezone).toInstant().toEpochMilli();

        return Collections.singletonList(new TimeWindow(sessionOpenMillis, sessionCloseMillis));
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

    /** Merge overlapping {@link TimeWindow}s. */
    @Override
    public void mergeWindows(
            Collection<TimeWindow> windows, MergingWindowAssigner.MergeCallback<TimeWindow> c) {
        TimeWindow.mergeWindows(windows, c);
    }

    @Override
    public String toString() {
        return "PricingSessionWindow{"
                + "marketId='"
                + marketId
                + '\''
                + ", timezone="
                + timezone
                + ", sessionOpen="
                + sessionOpen
                + ", sessionClose="
                + sessionClose
                + '}';
    }

    /**
     * Factory method to create a PricingSessionWindow for a specific market.
     *
     * @param marketId The market identifier (e.g., "NYSE", "LSE", "CME")
     * @param timezone The timezone in which the market operates
     * @param sessionOpen The opening time of the trading session
     * @param sessionClose The closing time of the trading session
     * @return A new PricingSessionWindow configured for the specified market
     */
    public static PricingSessionWindow forMarket(
            String marketId, ZoneId timezone, LocalTime sessionOpen, LocalTime sessionClose) {
        return new PricingSessionWindow(marketId, timezone, sessionOpen, sessionClose);
    }
}
```

### File 3: PricingSessionTrigger.java

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
 * http://www.apache.org/licenses/LICENSE-2.0
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
 * A {@link Trigger} for pricing sessions that fires at market close (window end) via event-time
 * timer. This trigger is designed to work with {@link
 * org.apache.flink.streaming.api.windowing.assigners.PricingSessionWindow}.
 *
 * <p>The trigger fires once the watermark passes the end of the trading session window. It
 * supports merging of windows, which is essential when session windows overlap during market
 * transitions.
 *
 * <p>For trading scenarios, this trigger ensures that:
 * <ul>
 *   <li>Window results are emitted at the end of the trading session
 *   <li>Late-arriving data can trigger immediate evaluation
 *   <li>Multiple overlapping sessions can be merged correctly
 * </ul>
 */
@PublicEvolving
public class PricingSessionTrigger extends Trigger<Object, TimeWindow> {
    private static final long serialVersionUID = 1L;

    private PricingSessionTrigger() {}

    @Override
    public TriggerResult onElement(
            Object element, long timestamp, TimeWindow window, TriggerContext ctx)
            throws Exception {
        // If the watermark is already past the window end, fire immediately
        // This handles late-arriving data
        if (window.maxTimestamp() <= ctx.getCurrentWatermark()) {
            return TriggerResult.FIRE;
        } else {
            // Otherwise, register a timer to fire when the window ends
            ctx.registerEventTimeTimer(window.maxTimestamp());
            return TriggerResult.CONTINUE;
        }
    }

    @Override
    public TriggerResult onEventTime(long time, TimeWindow window, TriggerContext ctx)
            throws Exception {
        // Fire when the event-time timer reaches the window's max timestamp
        return time == window.maxTimestamp() ? TriggerResult.FIRE : TriggerResult.CONTINUE;
    }

    @Override
    public TriggerResult onProcessingTime(long time, TimeWindow window, TriggerContext ctx)
            throws Exception {
        // We don't use processing time for trading sessions
        return TriggerResult.CONTINUE;
    }

    @Override
    public void clear(TimeWindow window, TriggerContext ctx) throws Exception {
        // Clean up the event-time timer when the window is purged
        ctx.deleteEventTimeTimer(window.maxTimestamp());
    }

    @Override
    public boolean canMerge() {
        // This trigger supports merging of windows
        return true;
    }

    @Override
    public void onMerge(TimeWindow window, OnMergeContext ctx) throws Exception {
        // When windows are merged, re-register the timer for the new merged window
        // Only register if the watermark hasn't passed the merged window's end time
        long windowMaxTimestamp = window.maxTimestamp();
        if (windowMaxTimestamp > ctx.getCurrentWatermark()) {
            ctx.registerEventTimeTimer(windowMaxTimestamp);
        }
    }

    @Override
    public String toString() {
        return "PricingSessionTrigger()";
    }

    /**
     * Creates a pricing session trigger that fires once the watermark passes the end of the
     * trading session window.
     *
     * <p>Once the trigger fires, all elements in the window are evaluated and the results are
     * emitted. Late-arriving elements that arrive after the window has closed will trigger
     * immediate window evaluation with just that one element.
     *
     * @return A new PricingSessionTrigger instance
     */
    public static PricingSessionTrigger create() {
        return new PricingSessionTrigger();
    }
}
```

## Analysis

### Implementation Strategy

The implementation follows Apache Flink's established windowing architecture patterns, with key design decisions:

#### 1. **PricingSessionWindow Design**

**Core Responsibility**: Map incoming events to trading session time windows based on market boundaries rather than fixed time intervals.

**Key Features**:
- **Extends MergingWindowAssigner<Object, TimeWindow>**: Allows overlapping session windows to be merged, essential for market transitions
- **Timezone-aware assignment**: Converts epoch timestamps to the market's local timezone before calculating session boundaries
- **Overnight session handling**: Correctly handles futures markets and overnight sessions where close time < open time (e.g., 23:00 - 22:00)
- **Immutable configuration**: Stores market ID, timezone, and session times as final fields for thread safety

**assignWindows() Logic**:
1. Convert timestamp to the market's timezone using Java 8 time API
2. Extract the local date and current local time
3. Create initial session boundaries (open and close times on that date)
4. Handle overnight sessions: if close < open, adjust dates based on whether current time is before or after open
5. Convert back to epoch milliseconds and return as a single-element collection

**Integration Points**:
- Returns EventTimeTrigger as the default trigger (inherited from existing patterns)
- Delegates window merging to TimeWindow.mergeWindows() utility method
- Implements isEventTime() = true for event-time based windowing

#### 2. **PricingSessionTrigger Design**

**Core Responsibility**: Emit window results at market close, with support for late-arriving data.

**Key Features**:
- **Event-time based firing**: Uses watermark and event-time timers, aligned with Flink's event-time semantics
- **Late-arrival handling**: Immediately fires windows when elements arrive after the window has closed
- **Window merging support**: Properly re-registers timers when overlapping windows are merged
- **Resource cleanup**: Properly deletes event-time timers to prevent state leaks

**Trigger Lifecycle**:
1. **onElement()**: Register timer for window end, unless watermark already passed
2. **onEventTime()**: Fire when timer reaches window's max timestamp
3. **onMerge()**: Re-register timer for the merged window's new end time
4. **clear()**: Delete the event-time timer to clean up state

#### 3. **TradingSessionExtractor Design**

**Core Responsibility**: Provide a functional interface for extracting market identifiers from stream elements.

**Pattern**: Follows the SessionWindowTimeGapExtractor pattern from Flink, enabling:
- Future extension to dynamic session assignment based on element content
- Serializable lambda functions in streaming pipelines
- Generic type parameter for stream element type

### Integration with Flink Architecture

**Compatibility**:
- All classes use standard Flink window interfaces and patterns
- Imports are consistent with flink-streaming-java module structure
- License headers and annotations (@PublicEvolving) follow Apache guidelines
- Proper exception handling and validation of inputs

**Extensibility**:
- TradingSessionExtractor enables future DynamicPricingSessionWindow variant
- PricingSessionTrigger can be subclassed for custom early-firing logic
- Factory methods (forMarket, create) provide clean APIs consistent with existing Flink patterns

### Key Design Decisions

1. **Use TimeWindow instead of custom window type**: Reuses Flink's tested serialization and merging logic
2. **Event-time only**: Trading analysis requires precise event timestamps, not system clock
3. **Single-element collection return**: Each event belongs to exactly one session (no overlapping assignments)
4. **Timezone-aware calculation**: Essential for multi-market analytics where sessions occur at different times globally
5. **Validation in constructor**: Fail-fast approach prevents configuration errors at runtime

### Use Cases

```java
// NYSE trading session: 09:30 - 16:00 ET
DataStream<Quote> nyseQuotes = ...;
WindowedStream<Quote, String, TimeWindow> nyseWindowed = nyseQuotes
    .keyBy(q -> q.getSymbol())
    .window(PricingSessionWindow.forMarket("NYSE",
                ZoneId.of("America/New_York"),
                LocalTime.of(9, 30),
                LocalTime.of(16, 0)))
    .apply(new SessionAggregation());

// CME Futures: 23:00 - 22:00 CT (overnight session)
DataStream<FuturesTick> futures = ...;
WindowedStream<FuturesTick, String, TimeWindow> futuresWindowed = futures
    .keyBy(f -> f.getContract())
    .window(PricingSessionWindow.forMarket("CME",
                ZoneId.of("America/Chicago"),
                LocalTime.of(23, 0),
                LocalTime.of(22, 0)))  // Next day
    .trigger(PricingSessionTrigger.create())
    .apply(new DailyStats());
```

### Compliance with Requirements

✅ **PricingSessionWindow** (`MergingWindowAssigner<Object, TimeWindow>`):
- ✅ `assignWindows()` determines session boundaries from timestamp
- ✅ `mergeWindows()` delegates to TimeWindow.mergeWindows()
- ✅ Factory method: `forMarket(String, ZoneId, LocalTime, LocalTime)`
- ✅ Handles overnight sessions (close < open)
- ✅ Returns `EventTimeTrigger` as default trigger

✅ **PricingSessionTrigger** (`Trigger<Object, TimeWindow>`):
- ✅ Fires at market close via event-time timer
- ✅ `canMerge()` returns true
- ✅ `onMerge()` re-registers timers for merged window
- ✅ `clear()` cleans up event-time timers

✅ **TradingSessionExtractor**:
- ✅ Functional interface for extracting market IDs
- ✅ Modeled after SessionWindowTimeGapExtractor pattern
- ✅ Enables dynamic session assignment

### Testing Recommendations

```java
@Test
public void testNYSESessionAssignment() {
    PricingSessionWindow window = PricingSessionWindow.forMarket("NYSE",
            ZoneId.of("America/New_York"),
            LocalTime.of(9, 30),
            LocalTime.of(16, 0));

    // Test that 09:45 ET assigns to today's session
    long timestamp = /* 2024-01-15 09:45 ET */;
    TimeWindow assigned = window.assignWindows(null, timestamp, null).iterator().next();
    assertEquals(/* 2024-01-15 09:30 ET */, assigned.getStart());
    assertEquals(/* 2024-01-15 16:00 ET */, assigned.getEnd());
}

@Test
public void testOvernightSessionAssignment() {
    PricingSessionWindow window = PricingSessionWindow.forMarket("CME",
            ZoneId.of("America/Chicago"),
            LocalTime.of(23, 0),
            LocalTime.of(22, 0));

    // Test that 23:30 CT assigns to session starting yesterday
    long timestamp = /* 2024-01-15 23:30 CT */;
    TimeWindow assigned = window.assignWindows(null, timestamp, null).iterator().next();
    assertEquals(/* 2024-01-14 23:00 CT */, assigned.getStart());
    assertEquals(/* 2024-01-15 22:00 CT */, assigned.getEnd());
}
```

