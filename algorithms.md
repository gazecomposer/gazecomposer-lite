\section{Core Algorithms (Sketch of Full GazeComposer Engine)}

\subsection{2D Polynomial Gaze Calibration}

For each calibration sample $i$, we observe a feature vector
$\mathbf{f}_i = (f_{i1}, f_{i2})$ and a target screen coordinate $(x_i, y_i)$.
We construct a quadratic feature map
\[
\phi(\mathbf{f}_i)
=
\bigl[\, 1,\ f_{i1},\ f_{i2},\ f_{i1}^2,\ f_{i1} f_{i2},\ f_{i2}^2 \,\bigr].
\]

Stacking these row-wise gives the design matrix
\[
X =
\begin{bmatrix}
\phi(\mathbf{f}_1) \\
\phi(\mathbf{f}_2) \\
\vdots \\
\phi(\mathbf{f}_N)
\end{bmatrix},
\qquad
\mathbf{x} =
\begin{bmatrix}
x_1 \\ x_2 \\ \vdots \\ x_N
\end{bmatrix},
\qquad
\mathbf{y} =
\begin{bmatrix}
y_1 \\ y_2 \\ \vdots \\ y_N
\end{bmatrix}.
\]

We solve two ridge-regression problems:
\begin{align}
\mathbf{w}_x^\ast
&=
\arg\min_{\mathbf{w}}
\left\| X \mathbf{w} - \mathbf{x} \right\|_2^2
+ \lambda \left\| \mathbf{w} \right\|_2^2,
\\[4pt]
\mathbf{w}_y^\ast
&=
\arg\min_{\mathbf{w}}
\left\| X \mathbf{w} - \mathbf{y} \right\|_2^2
+ \lambda \left\| \mathbf{w} \right\|_2^2.
\end{align}

The closed-form solutions are
\begin{align}
\mathbf{w}_x^\ast
&=
\left( X^\top X + \lambda I \right)^{-1} X^\top \mathbf{x},\\
\mathbf{w}_y^\ast
&=
\left( X^\top X + \lambda I \right)^{-1} X^\top \mathbf{y}.
\end{align}

At run time, a new feature vector $\mathbf{f}$ is mapped via
\begin{align}
\hat{x} &= \phi(\mathbf{f}) \, \mathbf{w}_x^\ast,\\
\hat{y} &= \phi(\mathbf{f}) \, \mathbf{w}_y^\ast.
\end{align}


\subsection{Temporal Smoothing (IIR Filter)}

Let $\mathbf{g}_t^{\text{raw}}$ be the instantaneous calibrated position at time $t$,
and $\mathbf{g}_t$ the smoothed position. We apply a one-pole IIR filter:
\begin{equation}
\mathbf{g}_t
=
(1 - \alpha)\, \mathbf{g}_{t-1}
+ \alpha\, \mathbf{g}_t^{\text{raw}},
\qquad
0 < \alpha < 1.
\end{equation}

A simple jump-based outlier rejection can be expressed as
\[
\left\| \mathbf{g}_t^{\text{raw}} - \mathbf{g}_{t-1} \right\|
> \tau_{\text{jump}}
\quad\Rightarrow\quad
\text{clamp or ignore } \mathbf{g}_t^{\text{raw}},
\]
for some threshold $\tau_{\text{jump}} > 0$.


\subsection{Dwell-Based Note Selection}

Let $\mathbf{g}_t$ be the smoothed position and $c_t$ the corresponding
grid-cell index at time $t$. A \emph{dwell} is continuous residency in a single
cell $c$ from time $t_{\text{enter}}$ to $t_{\text{exit}}$, with duration
\[
d = t_{\text{exit}} - t_{\text{enter}}.
\]

A note event is committed only if
\begin{equation}
d \;\geq\; d_{\min},
\end{equation}
where $d_{\min}$ is the selection threshold (e.g.\ $100\ \text{ms}$).


\subsection{Dwell-to-Vibrato Mapping}

Given a dwell duration $d$, we first normalize to $[0,1]$:
\begin{equation}
u =
\operatorname{clamp}
\!\left(
  \frac{d - d_{\min}}{d_{\max} - d_{\min}},
  0,\,
  1
\right),
\end{equation}
where $d_{\min}$ and $d_{\max}$ define the reference range for short vs.\ long
dwells in performance.

Each preset $p$ is defined by a curve
\[
f_p : [0,1] \to [0,1], \quad u \mapsto f_p(u),
\]
which we interpret as a normalized vibrato depth.

\paragraph{Baseline (no vibrato).}
\begin{equation}
f_{\text{base}}(u) = 0.
\end{equation}

\paragraph{Conservative vibrato (late onset, shallow).}
For a conservative preset we may use
\begin{equation}
f_{\text{cons}}(u)
=
\begin{cases}
0, &
u < u_0,\\[6pt]
\left(
  \dfrac{u - u_0}{1 - u_0}
\right)^{\gamma_{\text{cons}}}, &
u \ge u_0,
\end{cases}
\end{equation}
with $u_0 \in (0,1)$ setting the onset point and
$\gamma_{\text{cons}} \ge 1$ controlling growth.

\paragraph{More expressive preset (earlier onset, deeper).}
A more expressive preset can use a compressive power curve, e.g.
\begin{equation}
f_{\text{expr}}(u) = u^{\gamma_{\text{expr}}},
\qquad
0 < \gamma_{\text{expr}} \le 1.
\end{equation}

\paragraph{Depth parameter.}
The (normalized) vibrato depth parameter is then
\begin{equation}
v = f_p(u),
\end{equation}
which is finally mapped to a MIDI control or synthesis parameter in the
audio engine.
