# GazeComposer-lite: Dwell-based Grid + Vibrato Mapping (Research Skeleton)

This repository provides a **minimal, research-focused skeleton** of the system I use to study dwell-based vibrato mapping on a 2D pitch grid.

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

```bash
pip install opencv-python numpy
