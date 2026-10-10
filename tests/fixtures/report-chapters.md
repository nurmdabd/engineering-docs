# Day 01: RTL Analysis

## Objective

Run the **OpenLane** flow on `picorv32a`, then check **standard cell rows** and **legalization**; do **not** skip it.

## Command and output

**Command:**

```{.bash caption="Run run_synthesis on picorv32a"}
./flow.tcl -design picorv32a
```

**Output Snippet:**

```
[INFO]: Synthesis complete
```

### Results

| Metric | Value |
|---|---|
| Cells | 14876 |
| Flop ratio | 0.108 |
| Result DEF | `runs/03-10_09-12/results/picorv32a.def` |

# Day 02: Floorplan

## Core utilisation

$$\text{Utilisation} = \frac{\text{Area of cells}}{\text{Core area}}$$

## What is a floorplan?

The placement of the core and its I/O.

## Placement result:

The colon above was typed by hand.
