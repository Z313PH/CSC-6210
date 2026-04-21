# Task 4: Single-Cycle Processor Design (AND / OR)


## Overview

A single-cycle 32-bit processor simulator that computes **Y = A·B + C'·D** using AND and OR instructions. The NOT operation is handled via ALU input inversion controlled by a bit in the instruction's function field — NOT is not a separate instruction.

## Architecture

The processor follows the single-cycle execution model: **Fetch → Decode → Execute → Write-back** in one cycle.

### Modular File Structure

Each datapath component is in a separate file as required:

| File | Component | Description |
|------|-----------|-------------|
| `register_file.py` | Register File | 8 registers (t0–t7), 2 read ports, 1 write port |
| `alu.py` | ALU | AND/OR operations with input A inversion flag |
| `mux.py` | Multiplexer | 2-to-1 MUX for datapath routing |
| `instruction.py` | Instruction Memory | R-type encoding/decoding, program assembly |
| `control_unit.py` | Control Unit | Decodes instructions, generates control signals |
| `processor.py` | Datapath | Connects all components, single-cycle execution |
| `main.py` | Driver | Runs program, displays execution trace |
| `test_processor.py` | Tests | 27 unit tests covering all components |

### Instruction Format (R-type, 32-bit)

```
[31:26] opcode (6 bits) — 0x00 for R-type
[25:21] rs     (5 bits) — source register 1
[20:16] rt     (5 bits) — source register 2
[15:11] rd     (5 bits) — destination register
[10:6]  shamt  (5 bits) — unused
[5:0]   funct  (6 bits) — function code
```

Function codes:
- `0x04` — AND
- `0x05` — OR
- `0x24` — AND with input A inverted (bit 5 of funct = invert flag)

### Control Signals

| Signal | Description |
|--------|-------------|
| `alu_op` | ALU operation: AND (0) or OR (1) |
| `invert_a` | Invert ALU input A (for NOT, encoded in funct field) |
| `reg_write` | Enable writing to destination register |

### Program Executed

```
Assuming: t0=A, t1=B, t2=C, t3=D

and t4, t0, t1    ; t4 = A & B
and t6, t2, t3    ; t6 = (~C) & D   [invert flag set in funct]
or  t0, t4, t6    ; t0 = t4 | t6 = Y
```

## How to Run

```bash
python3 main.py
```


```
### Run unit tests:
```bash
python3 -m unittest test_processor -v
```

## Output

The program displays:
1. **Instruction execution trace** — decoded instruction per cycle
2. **Control signals per instruction** — ALU op, invert flag, reg write enable
3. **Register values after each instruction** — full register file dump
4. **Final output Y** — with intermediate values (t4, t6) and validation (PASS/FAIL)

## Requirements

- Python 3.10+
- No external libraries (standard library only)
