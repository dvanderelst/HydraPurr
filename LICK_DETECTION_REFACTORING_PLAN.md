# Lick Detection System Refactoring Plan

## Overview

This document outlines the refactoring of the lick detection system to create a **unified, cleanly-separated architecture** that works both on the microcontroller board and in offline data analysis.

## Current Problems

1. **Tight Coupling**: Board-specific code mixed with algorithm logic
2. **Import Conflicts**: Offline analysis can't import board modules
3. **Duplication**: Similar logic in `LickCounter.py` and `utils.process_licks()`
4. **Testing Difficulty**: Hard to test algorithm without hardware
5. **Maintenance Burden**: Changes require updates in multiple places

## Proposed Solution

Create a **three-layer architecture** with clear separation of concerns:

```
┌───────────────────────────────────────────────────────┐
│                 OFFLINE ANALYSIS LAYER                 │
│  (ProcessLickData/analysis/LickAnalyzer.py)          │
│                                                       │
│  ✅ Uses LickDetectionCore                            │
│  ✅ Handles pandas/dataframe operations                │
│  ✅ Provides analysis-friendly interface              │
│  ✅ Zero hardware dependencies                        │
└───────────────────────────────────────────────────────┘
                       ▲          △
                       │          │
                       │          │
┌───────────────────────────────────────────────────────┐
│                 CORE ALGORITHM LAYER                  │
│  (BoardCode/lib/LickDetectionCore.py)                 │
│                                                       │
│  ✅ Pure lick detection algorithm                     │
│  ✅ Debouncing logic                                  │
│  ✅ Lick validation                                   │
│  ✅ Bout formation                                    │
│  ✅ Statistics tracking                               │
│  ✅ Zero hardware dependencies                        │
│  ✅ Zero pandas dependencies (optional)              │
└───────────────────────────────────────────────────────┘
                       ▲          △
                       │          │
                       │          │
┌───────────────────────────────────────────────────────┐
│                 BOARD HARDWARE LAYER                  │
│  (BoardCode/lib/LickCounter.py)                      │
│                                                       │
│  ✅ ADC sensor interfacing                           │
│  ✅ Water level reading                               │
│  ✅ SD card logging                                   │
│  ✅ RFID cat detection                               │
│  ✅ Feeder control                                   │
│  ✅ Uses LickDetectionCore for algorithm             │
└───────────────────────────────────────────────────────┘
```

## Detailed Component Breakdown

### 1. Core Algorithm Layer (`LickDetectionCore.py`)

**Location:** `BoardCode/lib/LickDetectionCore.py`

**Purpose:** Pure Python implementation of lick detection algorithm

**Classes:**

#### `BoutTracker` (refactored from `LickState`)
```python
class BoutTracker:
    """Tracks lick bouts for a single cat - pure algorithm, no hardware"""
    
    # Algorithm parameters
    def __init__(self, cat_name, min_lick_ms=50, max_lick_ms=150, 
                 min_licks_per_bout=3, max_bout_gap_ms=1000, debounce_ms=5):
        # Initialize detection parameters and state
    
    # Core algorithm methods
    def process_sample(self, binary_state, timestamp_ms, water_level=None):
        """Process single binary sample - returns detection results"""
        # Debouncing, lick detection, bout formation
        return (prev_state, curr_state, duration, lick_added, bout_closed)
    
    def end_bout(self, timestamp_ms, water_level=None):
        """Force end current bout"""
    
    def get_last_bout_summary(self):
        """Get summary of last completed bout"""
        return {duration_ms, lick_count, water_delta, ...}
    
    def get_current_bout_info(self):
        """Get info about ongoing bout"""
        return {start_time, lick_count_so_far, ...}
    
    # Internal algorithm methods
    def _debounce_state(self, binary_state, timestamp_ms):
        """Pure debounce algorithm"""
    
    def _track_lick(self, duration_ms, water_level):
        """Track individual lick for bout summary"""
    
    def _finalize_bout(self, timestamp_ms, water_level):
        """Calculate bout statistics"""
    
    def _reset_bout_tracking(self):
        """Reset bout tracking state"""
```

#### `LickDetectionCore` (main interface)
```python
class LickDetectionCore:
    """Main interface for lick detection algorithm"""
    
    def __init__(self, cat_names=['unknown'], **kwargs):
        """Initialize with cat names and detection parameters"""
        self.trackers = {name: BoutTracker(name, **kwargs) for name in cat_names}
        self.active_cat = cat_names[0]
    
    def process_sample(self, binary_state, timestamp_ms, water_level=None, cat_name=None):
        """Process single sample for specified cat"""
        tracker = self.trackers[cat_name or self.active_cat]
        return tracker.process_sample(binary_state, timestamp_ms, water_level)
    
    def set_active_cat(self, cat_name):
        """Switch active cat (finalizes previous cat's bout)"""
    
    def process_dataframe(self, df):
        """Batch process dataframe of lick data"""
        # Uses pandas to process entire dataset
        return (events_df, summary_df)
    
    # Proxy methods to active tracker
    def get_last_bout_summary(self, cat_name=None):
        return self.trackers[cat_name or self.active_cat].get_last_bout_summary()
    
    def get_current_bout_info(self, cat_name=None):
        return self.trackers[cat_name or self.active_cat].get_current_bout_info()
```

**Dependencies:** None (pure Python)

**Optional Dependencies:** `pandas`, `numpy` (only for `process_dataframe()`)

### 2. Board Hardware Layer (`LickCounter.py`)

**Location:** `BoardCode/lib/LickCounter.py`

**Purpose:** Hardware-specific implementation for microcontroller

```python
class LickCounter:
    """Board-specific lick counter with hardware dependencies"""
    
    def __init__(self, cat_names=None):
        # Hardware setup
        self.water_sensor = MyADC(0)          # Water level sensor
        self.data_store = MyStore(Settings.lick_data_filename)  # SD card
        self.lick_threshold = 2.0           # From Settings
        
        # Create core algorithm with board settings
        self.core = LickDetectionCore(
            cat_names=cat_names or ['unknown'],
            min_lick_ms=Settings.min_lick_ms,
            max_lick_ms=Settings.max_lick_ms,
            min_licks_per_bout=Settings.min_licks_per_bout,
            max_bout_gap_ms=Settings.max_bout_gap_ms
        )
    
    def update(self, raw_adc_value, cat_name=None):
        """Update with raw ADC value from sensor"""
        # Hardware-specific: convert raw ADC to binary
        binary_state = 1 if raw_adc_value < self.lick_threshold else 0
        timestamp = now()  # Hardware time
        water = self.water_sensor.mean(10)  # Hardware sensor reading
        
        # Use core algorithm
        prev, curr, dur, lick_added, bout_closed = self.core.process_sample(
            binary_state, timestamp, water, cat_name
        )
        
        # Hardware-specific: logging
        if lick_added or bout_closed:
            self._log_to_sd_card(cat_name, curr, 
                               self.core.get_lick_count(cat_name),
                               self.core.get_bout_count(cat_name), water)
        
        # Hardware-specific: cat management
        if cat_name and cat_name != self.core.active_cat:
            self.core.set_active_cat(cat_name)
        
        return {
            "cat_name": cat_name or self.core.active_cat,
            "previous_state": prev,
            "current_state": curr,
            "state_duration_ms": dur,
            "lick_added": lick_added,
            "bout_closed": bout_closed,
            "lick_count": self.core.get_lick_count(cat_name),
            "bout_count": self.core.get_bout_count(cat_name),
            "bout_summary": self.core.get_last_bout_summary(cat_name),
            "water_level": water
        }
    
    def _log_to_sd_card(self, cat_name, state, lick_count, bout_count, water):
        """Hardware-specific logging to SD card"""
        data = [cat_name, state, lick_count, bout_count, water]
        self.data_store.add(data)
    
    # Proxy methods to core for convenience
    def get_last_bout_summary(self, cat_name=None):
        return self.core.get_last_bout_summary(cat_name)
    
    def get_current_bout_info(self, cat_name=None):
        return self.core.get_current_bout_info(cat_name)
```

**Dependencies:**
- `components.MyStore` (SD card)
- `components.MyADC` (sensors)
- `Settings` (board configuration)
- `LickDetectionCore` (algorithm)

### 3. Offline Analysis Layer (`LickAnalyzer.py`)

**Location:** `ProcessLickData/analysis/LickAnalyzer.py`

**Purpose:** Offline data analysis using the same algorithm

```python
class LickAnalyzer:
    """Offline lick data analyzer using core algorithm"""
    
    def __init__(self, settings=None):
        """Initialize with board settings or custom parameters"""
        if settings:
            # Use board settings
            self.core = LickDetectionCore(
                min_lick_ms=settings.min_lick_ms,
                max_lick_ms=settings.max_lick_ms,
                min_licks_per_bout=settings.min_licks_per_bout,
                max_bout_gap_ms=settings.max_bout_gap_ms
            )
        else:
            # Use defaults
            self.core = LickDetectionCore()
    
    def analyze_dataframe(self, df):
        """Analyze dataframe of lick data"""
        return self.core.process_dataframe(df)
    
    def analyze_data_folder(self, folder_path):
        """Analyze complete data folder"""
        from library.data_reader import read_data_folder
        contents = read_data_folder(folder_path)
        if contents.licks is not None:
            events, summaries = self.analyze_dataframe(contents.licks)
            return {
                'events': events,
                'summaries': summaries,
                'system_log': contents.system_log
            }
        return None
    
    def compare_with_existing(self, contents):
        """Compare results with existing utils.process_licks()"""
        from library.utils import process_licks
        
        # Process with our algorithm
        our_events, our_summaries = self.analyze_dataframe(contents.licks)
        
        # Process with existing algorithm
        their_events, their_summaries = process_licks(contents)
        
        return {
            'our_results': (our_events, our_summaries),
            'their_results': (their_events, their_summaries),
            'events_match': len(our_events) == len(their_events),
            'bouts_match': len(our_summaries) == len(their_summaries)
        }
    
    # Proxy methods to core
    def get_last_bout_summary(self, cat_name=None):
        return self.core.get_last_bout_summary(cat_name)
```

**Dependencies:**
- `pandas`, `numpy` (data analysis)
- `LickDetectionCore` (algorithm)
- `data_reader` (local module)

## Migration Plan

### Phase 1: Create Core Algorithm
1. ✅ Create `BoardCode/lib/LickDetectionCore.py`
2. ✅ Move `BoutTracker` class (from `LickState`)
3. ✅ Move `LickDetectionCore` class
4. ✅ Implement pure algorithm methods
5. ✅ Add batch processing capability
6. ✅ Write unit tests for core algorithm

### Phase 2: Refactor Board Code
1. ✅ Refactor `BoardCode/lib/LickCounter.py`
2. ✅ Make it use `LickDetectionCore`
3. ✅ Remove algorithm logic (keep hardware code)
4. ✅ Ensure backward compatibility
5. ✅ Test on actual hardware

### Phase 3: Create Offline Analysis
1. ✅ Create `ProcessLickData/analysis/LickAnalyzer.py`
2. ✅ Implement dataframe processing
3. ✅ Add comparison with existing `process_licks()`
4. ✅ Write integration tests

### Phase 4: Update Existing Code
1. ✅ Update `ProcessLickData/run_my_viz.py` to use `LickAnalyzer`
2. ✅ Update `BoardCode/MainLoop.py` to use new bout summaries
3. ✅ Add example feeding logic using bout data
4. ✅ Document new capabilities

### Phase 5: Testing & Validation
1. ✅ Test core algorithm with unit tests
2. ✅ Test board integration
3. ✅ Test offline analysis
4. ✅ Compare results between old and new approaches
5. ✅ Validate bout detection consistency

## Benefits of This Architecture

### 1. **Clean Separation of Concerns**
- Algorithm ≠ Hardware ≠ Analysis
- Each layer has single responsibility
- Clear dependency boundaries

### 2. **No Import Conflicts**
- Offline code never imports hardware modules
- Board code doesn't need pandas
- Clean dependency tree

### 3. **Algorithm Consistency**
- Same detection logic on board and offline
- Identical parameters and behavior
- Easy to compare results

### 4. **Testability**
- Core algorithm can be unit tested
- No hardware required for testing
- Easy to create test cases

### 5. **Maintainability**
- Changes in one place
- Clear upgrade path
- Better documentation

### 6. **Flexibility**
- Can use different settings for analysis
- Easy to experiment with parameters
- Supports multiple use cases

## Example Usage After Refactoring

### Board Usage (MainLoop.py)
```python
from lib.LickCounter import LickCounter

# Initialize
counter = LickCounter(cat_names=['henk', 'bob'])

# In main loop
while True:
    lick_sample = hydrapurr.read_lick()
    result = counter.update(lick_sample)
    
    # Use bout summary for decisions
    if result['bout_closed']:
        bout = counter.get_last_bout_summary()
        if bout['lick_count'] >= 5 and bout['duration_ms'] >= 2000:
            hydrapurr.feeder_on()
            time.sleep(2)
            hydrapurr.feeder_off()
```

### Offline Analysis (run_my_viz.py)
```python
from analysis.LickAnalyzer import LickAnalyzer

# Initialize analyzer
analyzer = LickAnalyzer()

# Analyze data folder
results = analyzer.analyze_data_folder('data/Jan_6_26')

# Use results for visualization
events = results['events']
summaries = results['summaries']

# Create plots as before
create_lick_plot(events, summaries)
```

## Files to Create/Modify

### New Files
- `BoardCode/lib/LickDetectionCore.py` - Core algorithm
- `ProcessLickData/analysis/LickAnalyzer.py` - Offline analysis
- `ProcessLickData/analysis/__init__.py` - Package init

### Modified Files
- `BoardCode/lib/LickCounter.py` - Refactored to use core
- `ProcessLickData/run_my_viz.py` - Updated to use analyzer
- `BoardCode/example_bout_usage.py` - Updated examples

### Deprecated Files
- `ProcessLickData/library/utils.py::process_licks()` - Replaced by analyzer

## Backward Compatibility

✅ **All existing board code continues to work**
- `LickCounter.update()` has same interface
- All existing methods preserved
- No changes required to `MainLoop.py`

✅ **Existing data format unchanged**
- Same log file structure
- Same column names
- Compatible with existing analysis tools

✅ **Gradual migration possible**
- Can use new features incrementally
- Old analysis code still works
- No breaking changes

## Implementation Timeline

1. **Day 1-2**: Create `LickDetectionCore.py` with core algorithm
2. **Day 3**: Refactor `LickCounter.py` to use core
3. **Day 4**: Create `LickAnalyzer.py` for offline use
4. **Day 5**: Update `run_my_viz.py` and test
5. **Day 6**: Documentation and examples
6. **Day 7**: Final testing and validation

## Success Criteria

1. ✅ Core algorithm works in isolation
2. ✅ Board code uses core algorithm correctly
3. ✅ Offline analysis produces same results as board
4. ✅ All existing functionality preserved
5. ✅ New bout summary features work
6. ✅ No import conflicts in any environment
7. ✅ Comprehensive tests pass
8. ✅ Documentation is clear and complete

## Risks and Mitigations

### Risk: Algorithm Differences
**Mitigation:** Careful refactoring, extensive testing, comparison with existing results

### Risk: Hardware Compatibility
**Mitigation:** Preserve all hardware interfaces, test on actual device

### Risk: Performance Issues
**Mitigation:** Profile critical sections, optimize if needed

### Risk: Data Format Changes
**Mitigation:** Preserve existing formats, add new fields optionally

## Conclusion

This refactoring creates a robust, maintainable architecture that:
- Separates algorithm from hardware
- Enables consistent on-board and offline analysis
- Provides better testing capabilities
- Maintains full backward compatibility
- Supports future enhancements

The three-layer architecture ensures clean separation of concerns while providing a unified lick detection experience across all use cases.