## Core Algorithms (Full GazeComposer Engine – Sketch)

This repository exposes only a mouse-driven, grid-based skeleton. The full GazeComposer engine adds several layers of computation. Below is a high-level description of those components, so that the underlying mathematical models are inspectable without releasing the full private codebase.

---

### 1. 2D Polynomial Gaze Calibration

In the full system, raw gaze features (for example, normalized iris ratios) are mapped to screen coordinates via a low-order 2D polynomial with ridge regularization.

For each calibration sample, we observe a feature vector and a target screen coordinate:

$$
\mathbf{f}_{i} = (f_{i1}, f_{i2}), \qquad (x_{i}, y_{i}).
$$

We build a design matrix using a quadratic basis:

$$
\phi(\mathbf{f}_{i}) =
\big[\, 1,\ f_{i1},\ f_{i2},\ f_{i1}^{2},\ f_{i1} f_{i2},\ f_{i2}^{2} \,\big].
$$

Stacking these row-wise gives

$$
X =
\begin{bmatrix}
\phi(\mathbf{f}_{1}) \\
\phi(\mathbf{f}_{2}) \\
\vdots \\
\phi(\mathbf{f}_{N})
\end{bmatrix},
\qquad
\mathbf{x} =
\begin{bmatrix}
x_{1} \\ x_{2} \\ \vdots \\ x_{N}
\end{bmatrix},
\qquad
\mathbf{y} =
\begin{bmatrix}
y_{1} \\ y_{2} \\ \vdots \\ y_{N}
\end{bmatrix}.
$$

We then solve two independent ridge–regression problems:

$$
\mathbf{w}_{x}^{*}
= \arg\min_{\mathbf{w}}
\Bigl( \bigl\| X \mathbf{w} - \mathbf{x} \bigr\|_{2}^{2}
+ \lambda \bigl\| \mathbf{w} \bigr\|_{2}^{2} \Bigr),
$$

$$
\mathbf{w}_{y}^{*}
= \arg\min_{\mathbf{w}}
\Bigl( \bigl\| X \mathbf{w} - \mathbf{y} \bigr\|_{2}^{2}
+ \lambda \bigl\| \mathbf{w} \bigr\|_{2}^{2} \Bigr).
$$

These have the standard closed-form solutions:

$$
\mathbf{w}_{x}^{*}
= (X^{\top} X + \lambda I)^{-1} X^{\top} \mathbf{x},
\qquad
\mathbf{w}_{y}^{*}
= (X^{\top} X + \lambda I)^{-1} X^{\top} \mathbf{y}.
$$

At runtime, a new feature vector is mapped via

$$
\hat{x} = \phi(\mathbf{f}) \cdot \mathbf{w}_{x}^{*},
\qquad
\hat{y} = \phi(\mathbf{f}) \cdot \mathbf{w}_{y}^{*}.
$$

> **Note.** The mouse-based demo in this repository replaces this calibration stage by reading \((\hat{x}, \hat{y})\) directly from the cursor.

---

### 2. Temporal Smoothing and Outlier Rejection

To control jitter from raw gaze estimates, the calibrated coordinates are passed through an exponential moving average (one-pole IIR filter):

$$
\mathbf{g}_{t}
= (1 - \alpha)\, \mathbf{g}_{t-1}
+ \alpha\, \mathbf{g}^{\text{raw}}_{t}.
$$

Here \(\mathbf{g}^{\text{raw}}_{t}\) is the instantaneous calibrated position at time \(t\), \(\mathbf{g}_{t}\) is the smoothed position, and \(\alpha \in (0, 1)\) controls the trade-off between jitter suppression and latency (typical values: \(\alpha \approx 0.3 \dots 0.5\)).

For outlier rejection we compare successive positions and ignore large jumps. If

$$
\bigl\| \mathbf{g}^{\text{raw}}_{t} - \mathbf{g}_{t-1} \bigr\|
$$

exceeds a defined jump threshold (saccade detection), the sample is clamped or ignored for the dwell detector. This ensures that short-lived tracking glitches or fast saccades do not trigger spurious note events.

---

### 3. Dwell-Based Note Selection

For a given smoothed position, we compute the active grid cell index \(c_{t}\).

A dwell is defined as continuous residency in a single cell. If the gaze enters at time \(t_{\text{enter}}\) and leaves at time \(t_{\text{exit}}\), the dwell duration is

$$
d = t_{\text{exit}} - t_{\text{enter}}.
$$

A note event is committed only if

$$
d \ge d_{\min}.
$$

Here \(d_{\min}\) is a selection threshold (for example, \(100 \text{ ms}\)). Sub-threshold dwells are treated as noise or saccades and ignored.

For each committed dwell, the system logs start time, end time, dwell duration, grid indices \((\text{row}, \text{col})\), pitch, and derived control state (for example, vibrato depth). The demo script in this repository implements the same logic, but uses mouse position instead of smoothed gaze and omits the audio engine.

---

### 4. Dwell \(\rightarrow\) Vibrato Mapping

The vibrato-mapping presets in this repository approximate a more general family of curves used in the full engine.

#### 4.1 Normalize dwell duration

Given a dwell duration \(d\), we first normalize to \([0, 1]\):

$$
u = \mathrm{clamp}\!\left(
\frac{d - d_{\min}}{d_{\max} - d_{\min}},\ 0,\ 1
\right),
$$

where \(d_{\min}\) and \(d_{\max}\) are lower/upper reference points for “short” and “long” dwells in performance.

#### 4.2 Preset-specific depth curves

Each preset \(p\) is defined by a function

$$
f_{p} : [0, 1] \to [0, 1].
$$

Baseline (no vibrato):

$$
f_{\text{base}}(u) = 0.
$$

Conservative vibrato (late onset, shallow):

$$
f_{\text{cons}}(u) =
\begin{cases}
  0, & u < u_{0}, \\[4pt]
  \left(
    \dfrac{u - u_{0}}{1 - u_{0}}
  \right)^{\gamma_{\text{cons}}}, & u \ge u_{0},
\end{cases}
$$

where \(u_{0} \in (0, 1)\) sets a “vibrato onset” point and \(\gamma_{\text{cons}} \ge 1\) controls how quickly depth grows.

Expressive presets (earlier onset, deeper):

$$
f_{\text{expr}}(u) = u^{\gamma_{\text{expr}}},
$$

with \(0 < \gamma_{\text{expr}} \le 1\) for a more compressive, forgiving response.

#### 4.3 Depth to synthesis parameter

The vibrato depth parameter is then

$$
v = f_{p}(u),
$$

which is mapped to a MIDI CC or synth modulation index in the full engine. The lite demo logs \(v\) per note event but does not render audio.

Prototype scripts (outside this repository) also experiment with fitting \(f_{p}\) using regularized polynomial or logistic models to match target expressive profiles while constraining monotonicity and avoiding overfitting.

---

*This document is intentionally high-level: it is meant to show that the full GazeComposer engine uses standard tools from regression, filtering, and mapping design, even though this repository only includes the minimal mouse-based skeleton needed to reproduce the core dwell and vibrato logic.*
