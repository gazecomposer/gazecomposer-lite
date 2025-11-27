```python
#!/usr/bin/env python3
"""
demo_grid_vibrato_lite.py

Minimal, mouse-controlled version of a dwell-based grid +
vibrato mapping experiment.

- 5×10 pitch grid (row = register, col = stepwise motion)
- Mouse cursor stands in for gaze
- Dwell-based note selection
- Simple dwell → vibrato mapping presets
- CSV logging for later analysis

This script is intentionally self-contained and does NOT include any
webcam gaze tracking or advanced performance features from the full system.
"""

from __future__ import annotations
import argparse
import csv
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np


# -----------------------------
# Grid and event data structures
# -----------------------------

@dataclass
class GridConfig:
    rows: int = 5
    cols: int = 10
    width: int = 1000
    height: int = 500
    margin: int = 40

    @property
    def cell_w(self) -> int:
        return (self.width - 2 * self.margin) // self.cols

    @property
    def cell_h(self) -> int:
        return (self.height - 2 * self.margin) // self.rows


@dataclass
class NoteEvent:
    ts_ms: int
    run_id: str
    preset: str
    row: int
    col: int
    cell_id: int
    dwell_ms: float
    vib_depth: float
    vib_rate_hz: float
    note_pitch: int


# -----------------------------
# Mapping utilities
# -----------------------------

def cell_from_xy(cfg: GridConfig, x: int, y: int) -> Optional[Tuple[int, int]]:
    """Convert window coordinates to (row, col) indices, or None if outside grid."""
    if not (cfg.margin <= x < cfg.width - cfg.margin):
        return None
    if not (cfg.margin <= y < cfg.height - cfg.margin):
        return None

    col = (x - cfg.margin) // cfg.cell_w
    row = (y - cfg.margin) // cfg.cell_h

    if row < 0 or row >= cfg.rows or col < 0 or col >= cfg.cols:
        return None
    return int(row), int(col)


def pitch_from_cell(row: int, col: int, base_pitch: int = 60) -> int:
    """
    Map (row, col) to a simple MIDI-like pitch.
    Here we treat rows as register shifts (4 semitones per row)
    and columns as stepwise motion (1 semitone per col).
    """
    return int(base_pitch + col + row * 4)


# -----------------------------
# Vibrato mapping presets (toy)
# -----------------------------

def map_dwell_to_vibrato(
    dwell_ms: float,
    preset: str,
    min_dwell_ms: float = 120.0,
    max_dwell_ms: float = 800.0,
) -> Tuple[float, float]:
    """
    Map dwell duration (ms) to (vib_depth, vib_rate_hz) in a simple, preset-dependent way.

    - baseline: vib_depth = 0 always
    - vib_cons: shallow vibrato that grows slowly with dwell
    - vib_aggr: deeper vibrato that grows faster with dwell

    This is intentionally a toy mapping just to demonstrate experimental structure.
    """
    if dwell_ms < min_dwell_ms:
        return 0.0, 0.0

    # Normalize dwell into [0, 1]
    norm = (dwell_ms - min_dwell_ms) / (max_dwell_ms - min_dwell_ms)
    norm = max(0.0, min(1.0, norm))

    if preset == "baseline":
        vib_depth = 0.0
        vib_rate = 0.0

    elif preset == "vib_cons":
        # Gentle depth up to about 0.3, slow-ish rate 4–5 Hz
        vib_depth = 0.3 * norm
        vib_rate = 4.0 + norm  # 4–5 Hz

    elif preset == "vib_aggr":
        # More aggressive depth up to ~0.6, rate 5–7 Hz
        vib_depth = 0.6 * norm
        vib_rate = 5.0 + 2.0 * norm  # 5–7 Hz

    else:
        vib_depth = 0.0
        vib_rate = 0.0

    return float(vib_depth), float(vib_rate)


# -----------------------------
# Mouse handling
# -----------------------------

class MouseTracker:
    def __init__(self) -> None:
        self.x = -1
        self.y = -1

    def callback(self, event, x, y, flags, param) -> None:  # type: ignore[override]
        # We only care about current position; no clicks needed for dwell.
        self.x = x
        self.y = y


# -----------------------------
# Main experiment loop
# -----------------------------

def run_experiment(
    run_id: str,
    preset: str,
    duration_sec: float = 120.0,
    min_select_ms: float = 140.0,
) -> None:
    cfg = GridConfig()
    win_name = "GazeComposer-lite (mouse = gaze)"
    cv2.namedWindow(win_name)
    cv2.resizeWindow(win_name, cfg.width, cfg.height)

    tracker = MouseTracker()
    cv2.setMouseCallback(win_name, tracker.callback)

    # Logging setup
    out_dir = Path(".")
    ts_str = time.strftime("%Y%m%d_%H%M%S")
    csv_path = out_dir / f"events_{run_id}_{ts_str}.csv"

    csv_file = open(csv_path, "w", newline="", encoding="utf-8")
    writer = csv.writer(csv_file)
    writer.writerow([
        "ts_ms",
        "run_id",
        "preset",
        "row",
        "col",
        "cell_id",
        "dwell_ms",
        "vib_depth",
        "vib_rate_hz",
        "note_pitch",
    ])

    print(f"[INFO] Logging events to: {csv_path}")

    # Dwell tracking state
    current_cell: Optional[Tuple[int, int]] = None
    enter_time_ms: Optional[float] = None
    last_event_time_ms: float = 0.0

    start_time = time.time()
    frame = np.zeros((cfg.height, cfg.width, 3), dtype=np.uint8)

    try:
        while True:
            now = time.time()
            elapsed = now - start_time
            if elapsed > duration_sec:
                print("[INFO] Max duration reached, stopping.")
                break

            # Clear frame
            frame[:] = (0, 0, 0)

            # Draw grid
            for r in range(cfg.rows):
                for c in range(cfg.cols):
                    x0 = cfg.margin + c * cfg.cell_w
                    y0 = cfg.margin + r * cfg.cell_h
                    x1 = x0 + cfg.cell_w
                    y1 = y0 + cfg.cell_h
                    color = (50, 50, 50)
                    thickness = 1
                    cv2.rectangle(frame, (x0, y0), (x1, y1), color, thickness)

            # Current "gaze" = mouse pos
            x, y = tracker.x, tracker.y
            cell = cell_from_xy(cfg, x, y)

            now_ms = now * 1000.0

            # Dwell tracking logic
            if cell != current_cell:
                # Cell changed: finalize previous dwell if any
                if current_cell is not None and enter_time_ms is not None:
                    dwell_ms = now_ms - enter_time_ms
                    if dwell_ms >= min_select_ms:
                        r, c = current_cell
                        cell_id = r * cfg.cols + c
                        note_pitch = pitch_from_cell(r, c)
                        vib_depth, vib_rate = map_dwell_to_vibrato(
                            dwell_ms, preset
                        )

                        evt = NoteEvent(
                            ts_ms=int(now_ms),
                            run_id=run_id,
                            preset=preset,
                            row=r,
                            col=c,
                            cell_id=cell_id,
                            dwell_ms=dwell_ms,
                            vib_depth=vib_depth,
                            vib_rate_hz=vib_rate,
                            note_pitch=note_pitch,
                        )
                        writer.writerow([
                            evt.ts_ms,
                            evt.run_id,
                            evt.preset,
                            evt.row,
                            evt.col,
                            evt.cell_id,
                            f"{evt.dwell_ms:.2f}",
                            f"{evt.vib_depth:.4f}",
                            f"{evt.vib_rate_hz:.3f}",
                            evt.note_pitch,
                        ])
                        last_event_time_ms = now_ms

                # Start dwell in new cell
                current_cell = cell
                enter_time_ms = now_ms if cell is not None else None

            # Visual indications
            # Highlight current cell
            if cell is not None:
                r, c = cell
                x0 = cfg.margin + c * cfg.cell_w
                y0 = cfg.margin + r * cfg.cell_h
                x1 = x0 + cfg.cell_w
                y1 = y0 + cfg.cell_h
                cv2.rectangle(frame, (x0, y0), (x1, y1), (80, 80, 80), 2)

            # Draw cursor
            cv2.circle(frame, (x, y), 6, (0, 255, 255), -1)

            # Show dwell time text
            if current_cell is not None and enter_time_ms is not None:
                dwell_ms = now_ms - enter_time_ms
                text = f"cell={current_cell}, dwell={dwell_ms:.0f} ms"
            else:
                text = "Move the mouse around the grid (q to quit)"

            cv2.putText(
                frame,
                text,
                (20, cfg.height - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

            cv2.imshow(win_name, frame)
            key = cv2.waitKey(10) & 0xFF
            if key == ord("q"):
                print("[INFO] 'q' pressed, stopping.")
                break

    finally:
        csv_file.close()
        cv2.destroyAllWindows()
        print("[INFO] Finished. Events were logged to:", csv_path)


# -----------------------------
# CLI
# -----------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Minimal dwell-based grid + vibrato mapping demo."
    )
    parser.add_argument(
        "--preset",
        type=str,
        default="baseline",
        choices=["baseline", "vib_cons", "vib_aggr"],
        help="Dwell→vibrato mapping preset.",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default="demo",
        help="Label used in the log filename and CSV.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=120.0,
        help="Maximum duration of the session in seconds.",
    )
    args = parser.parse_args()

    run_experiment(
        run_id=args.run_id,
        preset=args.preset,
        duration_sec=args.duration,
    )


if __name__ == "__main__":
    main()
