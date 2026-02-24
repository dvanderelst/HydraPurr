# Enhanced LickCounter - Unified Lick Detection

## Overview

This enhancement to `BoardCode/lib/LickCounter.py` creates a unified lick detection system that works both:
- **On the board** (real-time processing with bout summary tracking)
- **Offline** (batch processing of logged data with pandas)

## Key Features

### 1. Bout Summary Tracking (For Board Use)

The enhanced `LickCounter` now tracks detailed information about completed bouts:

```python
bout_summary = counter.get_last_bout_summary()
# Returns dictionary with:
# - cat_name: Which cat triggered the bout
# - start_time: Monotonic time when bout started (ms)
# - end_time: Monotonic time when bout ended (ms)
# - duration_ms: Total bout duration
# - lick_count: Number of licks in bout
# - start_water: Water level at bout start
# - end_water: Water level at bout end
# - water_delta: Water level change (end - start)
# - water_extent: Water level variation during bout (max - min)
# - lick_durations: List of individual lick durations
```

### 2. Batch Processing (For Offline Analysis)

```python
# Process logged data using the same algorithm as the board
processed_df, summary_df = counter.process_dataframe(lick_dataframe)

# processed_df contains individual lick events with bout assignments
# summary_df contains bout-level statistics (same format as utils.process_licks())
```

### 3. Current Bout Monitoring

```python
current_info = counter.get_current_bout_info()
# Returns dictionary with:
# - start_time: When current bout started
# - start_water: Water level at start
# - lick_count_so_far: Number of licks so far
```

## Usage Examples

### Board Usage (Real-time)

```python
from lib.LickCounter import LickCounter

# Initialize counter
counter = LickCounter(cat_names=['henk', 'bob'])

# In main loop - process each sample
while True:
    lick_sample = hydrapurr.read_lick()  # Get raw ADC value
    result = counter.update(lick_sample)
    
    # Check if bout was completed
    if result['bout_closed']:
        bout_summary = counter.get_last_bout_summary()
        
        # Make feeding decision based on bout characteristics
        if (bout_summary['lick_count'] >= 5 and 
            bout_summary['duration_ms'] >= 2000):
            hydrapurr.feeder_on()
            time.sleep(2)  # Feed for 2 seconds
            hydrapurr.feeder_off()
            counter.reset_counts()  # Reset for next bout
```

### Offline Analysis

```python
import pandas as pd
from BoardCode.lib.LickCounter import LickCounter

# Load logged data
lick_data = pd.read_csv('licks.dat')

# Create counter (no hardware dependencies needed)
counter = LickCounter(cat_names=['henk', 'bob'])

# Process data using same algorithm as board
processed_events, bout_summaries = counter.process_dataframe(lick_data)

# Analyze results
print(f"Found {len(bout_summaries)} drinking bouts")
print(bout_summaries.describe())
```

## Backward Compatibility

✅ **All existing code continues to work unchanged**
- Existing `update()` method works exactly as before
- All existing parameters and methods preserved
- Board code requires no modifications

## Technical Details

### Smart Pandas Handling

The enhanced LickCounter uses optional pandas imports:
- **Board use**: No pandas required, works with CircuitPython
- **Offline use**: Pandas imported when available for batch processing
- **Graceful degradation**: Clear error if pandas missing for batch mode

### Algorithm Consistency

The batch processing algorithm (`process_dataframe()`) implements the same logic as the real-time processing:
- Same lick duration validation (`min_lick_ms` to `max_lick_ms`)
- Same bout grouping logic (`max_bout_gap_ms`)
- Same minimum licks per bout requirement (`min_licks_per_bout`)

## Testing

A comprehensive test script is provided in `ProcessLickData/test_lick_counter_integration.py` that:
1. Tests basic functionality
2. Processes real logged data
3. Compares results with existing `process_licks()` function
4. Verifies bout summary generation

## Files Modified

- `BoardCode/lib/LickCounter.py` - Enhanced with bout tracking and batch processing
- `ProcessLickData/test_lick_counter_integration.py` - Integration test script
- `BoardCode/example_bout_usage.py` - Example usage patterns

## Benefits

1. **Consistency**: Same algorithm runs on-board and offline
2. **Testability**: Can test with real data before deploying to hardware
3. **Enhanced Decision Making**: Board can use bout characteristics for smarter feeding
4. **Debugging**: Easier to compare live vs. processed results
5. **Maintenance**: Single source of truth for lick detection logic