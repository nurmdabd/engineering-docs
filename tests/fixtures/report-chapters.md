# Day 01: RTL Analysis

## Objective

Run the **OpenLane** flow on `picorv32a`.

## Command and output

**Command:**

```bash
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

# Day 02: Floorplan

## Core utilisation

$$\text{Utilisation} = \frac{\text{Area of cells}}{\text{Core area}}$$
