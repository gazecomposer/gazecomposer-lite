## Core Algorithms (Full GazeComposer Engine – Sketch)

This repository exposes only a mouse-driven, grid-based skeleton. The full GazeComposer engine adds three main layers of computation. Below is a high-level description of those components.

---

### 1. 2D Polynomial Gaze Calibration

In the full system, raw gaze features (e.g., iris ratios) are mapped to screen coordinates via a low-order 2D polynomial with ridge regularization.

For each calibration sample $i$, we observe:
- Feature vector: \\(\mathbf{f}_{i} = (f_{i1}, f_{i2})\\)
- Target screen coordinate: $(x_{i}, y_{i})$

We build a design matrix $X \in \mathbb{R}^{N \times D}$ using a quadratic basis:

$$
\phi(\mathbf{f}_{i}) = \big[\, 1,\ f_{i1},\ f_{i2},\ f_{i1}^2,\ f_{i1} f_{i2},\ f_{i2}^2 \,\big]
$$

Stacking these row-wise gives:

$$
X = 
\begin{bmatrix}
\phi(\mathbf{f}_{1}) \\
\phi(\mathbf{f}_{2}) \\
\vdots \\
\phi(\mathbf{f}_{N})
\end{bmatrix},
\quad
\mathbf{x} = 
\begin{bmatrix}
x_{1} \\ x_{2} \\ \vdots \\ x_{N}
\end{bmatrix},
\quad
\mathbf{y} = 
\begin{bmatrix}
y_{1} \\ y_{2} \\ \vdots \\ y_{N}
\end{bmatrix}
$$

We then solve two independent ridge-regression problems:

$$
\mathbf{w}_{x}^* = \arg\min_{\mathbf{w}} \bigl\| X \mathbf{w} - \mathbf{x} \bigr\|_{2}^2 + \lambda \bigl\| \mathbf{w} \bigr\|_{2}^2
$$

$$
\mathbf{w}_{y}^* = \arg\min_{\mathbf{w}} \bigl\| X \mathbf{w} - \mathbf{y} \bigr\|_{2}^2 + \lambda \bigl\| \mathbf{w} \bigr\|_{2}^2
$$

These have the standard closed-form solutions:

$$
\mathbf{w}_{x}^* = (X^\top X + \lambda I)^{-1} X^\top \mathbf{x}
$$

$$
\mathbf{w}_{y}^* = (X^\top X + \lambda I)^{-1} X^\top \mathbf{y}
$$

At runtime, each new feature vector $\mathbf{f}$ is mapped via:

$$
\hat{x} = \phi(\mathbf{f}) \cdot \mathbf{w}_{x}^*, \quad \hat{y} = \phi(\mathbf{f}) \cdot \mathbf{w}_{y}^*
$$

*Note: The mouse-based demo in this repository replaces this calibration stage by reading $(\hat{x}, \hat{y})$ directly from the cursor.*

---

### 2. Temporal Smoothing and Outlier Rejection

To control jitter from raw gaze estimates, we use an exponential moving average (one-pole IIR filter) on the calibrated coordinates:

$$
\mathbf{g}_{t} = (1 - \alpha)\, \mathbf{g}_{t-1} + \alpha\, \mathbf{g}^{\text{raw}}_{t}
$$

Where:
- $\mathbf{g}^{\text{raw}}_{t}$ is the instantaneous calibrated position at time $t$
- $\mathbf{g}_{t}$ is the smoothed position
- $\alpha \in (0,1)$ controls the trade-off between jitter suppression and latency (typical values: $\alpha \approx 0.3 \dots 0.5$)

In practice, we combine this with simple outlier rejection:
- If $\|\mathbf{g}^{\text{raw}}_{t} - \mathbf{g}_{t-1}\|$ exceeds a defined jump threshold (saccade detection), the sample is strictly clamped or ignored for the dwell detector.

---

### 3. Dwell-Based Note Selection

For a given smoothed position $\mathbf{g}_{t}$, we compute the active grid cell index $c_{t}$. A **dwell** is defined as continuous residency in a single cell:

- Enter time: $t_{\text{enter}}$
- Exit time: $t_{\text{exit}}$
- Dwell duration: $d = t_{\text{exit}} - t_{\text{enter}}$

A note event is committed only if:

$$
d \geq d_{\min}
$$

Where $d_{\min}$ is the selection threshold (e.g., $100\text{ ms}$). Sub-threshold dwells are treated as noise/saccades and ignored.

---

### 4. Dwell $\to$ Vibrato Mapping

The vibrato-mapping presets in this repository approximate a more general family of curves used in the full engine.

**1. Normalize dwell duration** Given a dwell duration $d$, we first normalize to $[0,1]$:

$$
u = \mathrm{clamp}\!\left( \frac{d - d_{\min}}{d_{\max} - d_{\min}},\ 0,\ 1 \right)
$$

Where $d_{\min}$ and $d_{\max}$ are lower/upper reference points for "short" and "long" dwells in performance.

**2. Preset-specific depth curves** Each preset $p$ is defined by a function $f_{p} : [0,1] \to [0,1]$.

* **Baseline (no vibrato):**
    $$
    f_{\text{base}}(u) = 0
    $$

* **Conservative vibrato (late onset, shallow):**
    $$
    f_{\text{cons}}(u) = 
    \begin{cases} 
      0 & u < u_{0} \\
      \left( \dfrac{u - u_{0}}{1 - u_{0}} \right)^{\gamma_{\text{cons}}} & u \ge u_{0} 
    \end{cases}
    $$
    Where $u_{0} \in (0,1)$ sets a "vibrato onset" point and $\gamma_{\text{cons}} \ge 1$ controls how quickly depth grows.

* **Expressive presets (earlier onset, deeper):**
    $$
    f_{\text{expr}}(u) = u^{\gamma_{\text{expr}}}
    $$
    With $0 < \gamma_{\text{expr}} \le 1$ for a more compressive, "forgiving" response.

**3. Depth to synthesis parameter** The vibrato depth parameter is then:

$$
v = f_{p}(u)
$$

which is ultimately mapped to a MIDI CC in the full engine. The lite demo logs $v$ per note event but does not render audio.
