---
title: "EEE329: Basic Communication Engineering"
subtitle: "Solution of Session 2020--21"
type: past-paper
header: "EEE329: Basic Communication Engineering"
header_right: "Solution of Session 2020--21"
exam: "EEE329 Term Final"
year: "2020--21"
---

# Question 1

- **1. (a)** Find the entropy of a single-bit binary memoryless source. Also draw the curve of entropy versus probability. [Marks: 5]
- **(b)** Briefly explain the three major bands of the EM spectrum—radio waves, microwaves, and infrared waves. [Marks: 6]
- **(c)** Write short notes on:
  - **(i)** Thermal Noise
  - **(ii)** Transit Time Noise [Marks: 4]
- **(d)** A carrier of $10~\text{MHz}$ and $10~\text{V}$ peak is amplitude-modulated by a $5~\text{kHz}$ sine wave of $6~\text{V}$. Find the modulation index. [Marks: 4]

## 1(a) Entropy of a Single-Bit Binary Memoryless Source

### Answer

**What is the Source?**

A binary memoryless source emits 0 or 1 independently. The entropy measures the average information [in bits when logarithms of base 2 are used]{.note} per symbol:

$$\boxed{H(p) = -p \log_2 p - (1-p)\log_2(1-p)}$$

**Case $p = 0.5$:**

$$H(0.5) &= -0.5 \log_2 0.5 - 0.5 \log_2 0.5 \\ &= 1 \text{ bit}.$$

![Binary entropy function H(p) vs probability p](figures/pre_de_emphasis_chain.png)

## 1(b) Major Bands of the EM Spectrum

### Answer

The three bands are radio waves, microwaves and infrared.

## 1(c) Thermal Noise and Transit-Time Noise

### Theory

#### 1. What is Thermal Noise? (Core Idea)

Random voltage from the thermal motion of electrons; $v_{\text{rms}} = \sqrt{4kTRB}$.

### Answer

#### i. Thermal Noise

**What it is:** noise from thermal motion of charge carriers.

#### ii. Transit-Time Noise

**What it is:** noise when carrier transit time is comparable to the signal period.

### Keyword Explanation

#### 1. Bandwidth

The range of frequencies a system passes.

## (d) AM Problem

### Answer

**Given:** $A_c = 10$ V, $A_m = 6$ V.

$$m = \frac{A_m}{A_c} = \frac{6}{10} = 0.6$$

### Final Concise Answer

**(a)** $H(0.5) = 1$ bit. **(d)** $m = 0.6$.

## 1(e) A Part Missing From the Paper List

> Explain why the modulation index must stay below 1. Marks: 2

### Answer

Above 1 the envelope distorts.
