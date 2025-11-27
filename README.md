# GazeComposer-lite: Dwell-based Grid + Vibrato Mapping (Research Skeleton)

This repository provides a **minimal, research-focused skeleton** of the system I use to study dwell-based vibrato mapping on a 2D pitch grid.

This lite demo accompanies my pilot study on dwell-based vibrato mapping described in my writing sample.

To protect ongoing patent work and a larger private codebase, this repo does **not** contain the full gaze-tracking implementation or the complete performance environment. Instead, it exposes:

- a simplified **5×10 pitch grid**,
- a **dwell-time based note selection** mechanism,
- a toy **dwell → vibrato-depth mapping** function, and
- CSV logging for later analysis.

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

Install dependencies:


Install dependencies: `pip install opencv-python numpy`  
If you only want logging and visualization, these are enough.
MIDI/sound output is intentionally omitted in this lite version to minimize dependencies.

3. Usage

Run the demo from the command line:

python demo_grid_vibrato_lite.py --preset baseline --run-id test01


Available options:

--preset {baseline,vib_cons,vib_aggr}
Selects a dwell→vibrato mapping profile.

--run-id RUN_ID
A string label used in the log file.

--duration SECONDS
Maximum duration of the session (default: 120s).

During a session:

Move your mouse cursor over the grid.

When the cursor stays inside one cell longer than the selection threshold, a note event is triggered and logged.

The current cell and dwell time are visualized in the window.

Press q to quit at any time.

4. Logged Data

Each session creates a CSV file in the current directory:

events_<run_id>_<timestamp>.csv

Columns:

ts_ms – event timestamp in milliseconds

run_id – label you passed via --run-id

preset – mapping preset name (baseline, vib_cons, vib_aggr)

row, col – grid indices of the selected cell (0-based)

cell_id – flattened cell index (row * n_cols + col)

dwell_ms – dwell duration in milliseconds

vib_depth – mapped vibrato depth (0.0–1.0 in this toy demo)

vib_rate_hz – mapped vibrato rate in Hz (toy mapping)

note_pitch – MIDI-like integer pitch (for analysis only; no sound in this lite version)

These logs are designed to be easy to analyze in Python, R, or spreadsheet software.
For example, you can compare dwell_ms distributions across presets, or check how often vib_depth is non-zero.

5. Architecture (Lite Version)

At a high level, the demo follows this data flow:

Mouse position  →  Grid cell / dwell tracker  →  Dwell duration
                   ↓
             Dwell→Vibrato mapping (preset)
                   ↓
              Event logging (CSV)


In the full system, the “mouse position” is replaced with webcam-based gaze coordinates that are calibrated to screen space, and the vibrato parameters modulate a continuous violin-like sound. Those details are intentionally omitted here, but the experimental structure is preserved.

6. Relation to the Full System

The full GazeComposer system:

uses webcam-based gaze tracking instead of the mouse,

combines gaze with mouth dynamics and hand gestures,

feeds parameters into a real-time performance engine, and

logs more detailed modality states.

This repository is a research skeleton intended for reviewers and collaborators who want to see how the mapping and logging pipeline is structured, without exposing the complete performance implementation or patent-sensitive details.


