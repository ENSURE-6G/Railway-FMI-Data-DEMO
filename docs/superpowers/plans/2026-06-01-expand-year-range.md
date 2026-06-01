# Expand Year Range to 2018–2025 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the app's selectable year range from 2024–2025 to 2018–2025 to expose the full dataset available in all Allas buckets.

**Architecture:** Single-constant change in `const.py` propagates to all data page selectboxes automatically. Two hardcoded year strings in `Home.py` are replaced with dynamic f-strings using `min(AVAILABLE_YEARS)` and `max(AVAILABLE_YEARS)`. No data loader or page logic changes required.

**Tech Stack:** Python 3.11, Streamlit

---

## Files Modified

- `const.py` — expand `AVAILABLE_YEARS`
- `Home.py` — replace hardcoded year strings with dynamic expressions

---

### Task 1: Expand AVAILABLE_YEARS in const.py

**Files:**
- Modify: `const.py:13`

- [ ] **Step 1: Change AVAILABLE_YEARS**

In `const.py`, change line 13 from:

```python
AVAILABLE_YEARS: list[int] = [2024, 2025]
```

to:

```python
AVAILABLE_YEARS: list[int] = list(range(2018, 2026))
```

- [ ] **Step 2: Verify the value**

Run:
```bash
python -c "from const import AVAILABLE_YEARS; print(AVAILABLE_YEARS)"
```

Expected output:
```
[2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
```

- [ ] **Step 3: Run tests to confirm nothing broke**

```bash
pytest tests/ -v
```

Expected: all 22 tests pass.

- [ ] **Step 4: Commit**

```bash
git add const.py
git commit -m "feat: expand AVAILABLE_YEARS to 2018-2025"
```

---

### Task 2: Replace hardcoded year strings in Home.py

**Files:**
- Modify: `Home.py:16` (caption)
- Modify: `Home.py:181` (About expander)

- [ ] **Step 1: Update the page caption**

In `Home.py`, find line 16:

```python
st.caption("Finnish railway timetable and FMI meteorological observations — 2024–2025")
```

Replace with:

```python
st.caption(f"Finnish railway timetable and FMI meteorological observations — {min(AVAILABLE_YEARS)}–{max(AVAILABLE_YEARS)}")
```

- [ ] **Step 2: Update the About expander text**

In `Home.py`, find the line inside the About expander (around line 181):

```python
with scheduled and actual timetable rows including delay information, for the years 2024–2025.
```

Replace with:

```python
with scheduled and actual timetable rows including delay information, for the years {min(AVAILABLE_YEARS)}–{max(AVAILABLE_YEARS)}.
```

Note: this line is inside an `st.markdown(f"""...""")` f-string block, so the `{...}` expressions will be interpolated automatically. Confirm the surrounding `f"""` prefix is present — if it is, just swap the literal `2024–2025` for `{min(AVAILABLE_YEARS)}–{max(AVAILABLE_YEARS)}`.

- [ ] **Step 3: Verify imports**

Confirm `AVAILABLE_YEARS` is already imported at the top of `Home.py`:

```python
from const import MAP_CENTER, MAP_ZOOM, AVAILABLE_YEARS, METADATA_PATH
```

It is — no import change needed.

- [ ] **Step 4: Run tests**

```bash
pytest tests/ -v
```

Expected: all 22 tests pass.

- [ ] **Step 5: Commit**

```bash
git add Home.py
git commit -m "feat: replace hardcoded year strings in Home.py with dynamic AVAILABLE_YEARS"
```
