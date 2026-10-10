## Lecture 24 — FM bandwidth

### 24.1 Peak deviation

For FM, the instantaneous frequency follows the message: $f_i = f_c + \dfrac{k_f}{2\pi} m(t)$, so the peak deviation is

$$\Delta f = \frac{k_f m_p}{2\pi}$$

where $k_f$ is the frequency sensitivity (rad/s per volt) and $m_p$ the peak of $|m(t)|$.

### 24.2 Carson's rule

The modulation index is $\beta = \Delta f / B$, with $B$ the message bandwidth. The transmission bandwidth is

$$B_T \approx 2(\Delta f + B) = 2B(\beta + 1)$$

NBFM ($\beta \ll 1$) needs about $2B$, like AM; WBFM ($\beta \gg 1$) needs about $2\Delta f$.

### 24.3 Pre-emphasis

The pre-emphasis corner frequency of a 75 µs network is $f_1 = \dfrac{1}{2\pi \cdot 75\,\mu\text{s}} \approx 2.12$ kHz.
