# Expand Year Range to 2018–2025 — Design Spec

**Date:** 2026-06-01  
**Scope:** `const.py` and `Home.py` only. No data loader, page logic, or test changes.

## Context

All three Allas buckets (`train_flat_data`, `weather_data`, `matched_flat_data`) contain parquet files from 2018 through 2025. The app currently restricts selection to 2024–2025 via `AVAILABLE_YEARS = [2024, 2025]` in `const.py`, and two hardcoded strings in `Home.py`. This change unlocks the full dataset.

## Changes

### `const.py`

Change `AVAILABLE_YEARS` from:

```python
AVAILABLE_YEARS: list[int] = [2024, 2025]
```

to:

```python
AVAILABLE_YEARS: list[int] = list(range(2018, 2026))
```

This single change propagates to all three data page selectboxes automatically — they all import and use `AVAILABLE_YEARS`.

### `Home.py`

Two hardcoded year strings become dynamic:

1. Page caption (line 16):
   - Before: `"Finnish railway timetable and FMI meteorological observations — 2024–2025"`
   - After: `f"Finnish railway timetable and FMI meteorological observations — {min(AVAILABLE_YEARS)}–{max(AVAILABLE_YEARS)}"`

2. About expander text:
   - Before: `"for the years 2024–2025"`
   - After: `f"for the years {min(AVAILABLE_YEARS)}–{max(AVAILABLE_YEARS)}"`

The Data Coverage metric already uses `min(AVAILABLE_YEARS)` / `max(AVAILABLE_YEARS)` dynamically — no change needed there.

## Out of Scope

- Data loaders — already accept any `year` and `month`, no changes needed
- Data page logic — selectboxes already driven by `AVAILABLE_YEARS`
- Tests — no test covers `AVAILABLE_YEARS` values directly
