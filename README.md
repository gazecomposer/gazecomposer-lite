# GazeComposer-lite: Dwell-based Grid + Vibrato Mapping (Research Skeleton)

If you are reading this as part of a graduate application: this lite repository is meant to expose the experimental core of my dwell-based vibrato mapping work, which I describe in more detail in my writing sample (“A Pilot Study of Dwell-Based Vibrato Mapping in GazeComposer”).

This repository provides a **minimal, research-focused skeleton** of the system I use to study dwell-based vibrato mapping on a 2D pitch grid. It accompanies my pilot study on dwell-based vibrato mapping described in my writing sample.

To protect ongoing patent work and a larger private codebase, this repo does **not** contain the full gaze-tracking implementation or the complete performance environment. Instead, it exposes:

- a simplified **5×10 pitch grid**  
- a **dwell-time based note selection** mechanism  
- a toy **dwell → vibrato-depth mapping** function  
- CSV logging for later analysis  

In this demo, a **mouse cursor stands in for gaze**. The architecture and data flow mirror the experimental pipeline used in my pilot study, but all core production code remains private.

---
## 1. Concept

The goal of this demo is to make the **experimental logic** of my work reproducible:

- A 2D grid behaves like a simplified “gaze keyboard”.
- When the pointer **dwells** in a cell longer than a threshold, a **note event** is triggered.
- The **dwell duration (ms)** is mapped to a **vibrato depth parameter** using different “presets”:
  - `baseline`: no vibrato  
  - `vib_cons`: conservative, shallow vibrato only on longer dwells  
  - `vib_aggr`: more aggressive vibrato growth with dwell time  
- Every event is logged to a CSV file so that dwell distributions and vibrato behavior can be analyzed offline.

This is essentially the “Phase 1” mapping pilot distilled into a stand-alone, mouse-controlled demo.

---

## 2. Requirements

Python 3.10+ is recommended.

Install dependencies: `pip install opencv-python numpy`  

If you only want logging and visualization, these are enough.  
MIDI/sound output is intentionally omitted in this lite version to minimize dependencies.

---

## 3. Usage

Run the demo from the command line:  
`python demo_grid_vibrato_lite.py --preset baseline --run-id test01`

Available options:

- `--preset {baseline,vib_cons,vib_aggr}` – selects a dwell→vibrato mapping profile.  
- `--run-id RUN_ID` – a string label used in the log file.  
- `--duration SECONDS` – maximum duration of the session (default: 120s).  

During a session:

- Move your mouse cursor over the grid.  
- When the cursor stays inside one cell longer than the selection threshold, a note event is triggered and logged.  
- The current cell and dwell time are visualized in the window.  

Press `q` to quit at any time.

---

## 4. Logged Data

Each session creates a CSV file in the current directory:

`events_<run_id>_<timestamp>.csv`

Columns:

- `ts_ms` – event timestamp in milliseconds  
- `run_id` – label you passed via `--run-id`  
- `preset` – mapping preset name (`baseline`, `vib_cons`, `vib_aggr`)  
- `row`, `col` – grid indices of the selected cell (0-based)  
- `cell_id` – flattened cell index (`row * n_cols + col`)  
- `dwell_ms` – dwell duration in milliseconds  
- `vib_depth` – mapped vibrato depth (0.0–1.0 in this toy demo)  
- `vib_rate_hz` – mapped vibrato rate in Hz (toy mapping)  
- `note_pitch` – MIDI-like integer pitch (analysis only; no sound in this lite version)  

These logs are designed to be easy to analyze in Python, R, or spreadsheet software.  
For example, you can compare `dwell_ms` distributions across presets, or check how often `vib_depth` is non-zero.

---

## 5. Architecture (Lite Version)

At a high level, the demo follows this data flow:

```
Mouse position  →  Grid cell / dwell tracker  →  Dwell duration  
                     ↓  
               Dwell→Vibrato mapping (preset)  
                     ↓  
                Event logging (CSV)
```

In the full system, the “mouse position” is replaced with webcam-based gaze coordinates that are calibrated to screen space, and the vibrato parameters modulate a continuous violin-like sound. Those details are intentionally omitted here, but the experimental structure is preserved.

---

## 6. Core Algorithms / Mathematical Components

This lite repository exposes only a **subset** of the algorithms used in the full GazeComposer system, but the core experimental logic is preserved.

### In this lite demo

- **Dwell-time based fixation detection**  
  – Tracks how long the pointer remains within a given grid cell.  
  – Triggers a note event when dwell exceeds a configurable threshold.  

- **Dwell → vibrato mapping (preset-based)**  
  – Maps `dwell_ms` to a normalized vibrato depth parameter in `[0.0, 1.0]` using simple piecewise / compressive curves.  
  – Supports multiple presets (`baseline`, `vib_cons`, `vib_aggr`) to emulate different expressive profiles.  

- **Grid-to-pitch mapping**  
  – Converts `(row, col)` indices and a `cell_id` into a MIDI-like pitch index, allowing comparisons across runs and presets.

### In the full system (not included in this repo)

The private, production codebase additionally implements:

- **2D polynomial gaze calibration**  
  – **Least-squares regression (with optional L2 regularization)** from normalized iris-based ratios to screen coordinates.  

- **IIR / exponential smoothing for gaze trajectories**  
  – One-pole IIR low-pass filtering of gaze trajectories,  
    using an exponential moving average  
    `g_t = (1 - α) · g_{t-1} + α · g_t^{raw}`  
    with **MAD-based outlier rejection** to handle blinks and tracking glitches.  

- **Ridge-style regression for preset fitting**  
  – Using regularized regression to fit mapping presets, keeping vibrato depth stable across presets while preserving perceptual differences.  

These components are kept private due to ongoing patent work, but they share the same experimental structure as this lite demo:  
calibrated gaze → smoothed trajectory → dwell detection → mapping to vibrato and other performance parameters → logging.

---

## 7. Relation to the Full System

The full GazeComposer system:

- uses webcam-based gaze tracking instead of the mouse,  
- combines gaze with mouth dynamics and hand gestures,  
- feeds parameters into a real-time performance engine, and  
- logs more detailed modality states.

  ---

## 8. Example Analysis (Python)

The CSV logs are meant to be simple to analyze with standard tools.

For example, if you collect several runs with different presets, you can reproduce the main pilot-style summary statistics (events per preset, mean dwell, mean vibrato depth, zero-vibrato ratio):

- concatenate all `events_*.csv` files for a participant or condition
- group by `preset`
- compute descriptive statistics

A minimal Python example:

```python
import glob
import pandas as pd

files = sorted(glob.glob("events_*.csv"))
df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)

summary = (
    df.groupby("preset", as_index=False)
      .agg(
          events_total=("dwell_ms", "size"),
          dwell_ms_mean=("dwell_ms", "mean"),
          vib_depth_mean=("vib_depth", "mean"),
          vib_zero_ratio=("vib_depth", lambda x: (x.fillna(0) == 0).mean()),
      )
)

print(summary)
```


This mirrors the analysis pipeline used in my pilot study:
for each vibrato preset, I look at how many note events it produces, how long participants tend to dwell, and how often the mapped vibrato depth is effectively zero.

## 9. Limitations and Planned Analysis

This repository focuses on the **mapping and logging skeleton** rather than full-scale data analysis. In my pilot work I primarily use descriptive statistics (e.g., dwell-time distributions, vibrato incidence per preset) to check that the mappings behave sensibly.

For future work, I plan to extend this pipeline with more formal models, for example:

- **Mixed-effects models** for dwell time  
  – to compare presets while accounting for participant-level differences.  
- **Logistic regression** for vibrato onset  
  – modeling the probability that `vib_depth > 0` as a function of dwell time, grid position, and preset.  
- **Survival / hazard-style analyses** for dwell durations  
  – treating note selection as a time-to-event process.  

These planned analyses build on my ongoing self-study in linear algebra, probability, and introductory machine learning, and are intended to turn this pilot-style mapping exploration into a more robust experimental framework.


This repository is a research skeleton intended for reviewers and collaborators who want to see how the mapping and logging pipeline is structured, **without** exposing the complete performance implementation or patent-sensitive details.
