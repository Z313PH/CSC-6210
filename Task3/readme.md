# Memory Hierarchy Simulation (SSD → DRAM → Cache → CPU)


## Run

```bash
python task3.py
```

## Configuration

On startup you can customize sizes and replacement policy, or press Enter to use defaults:

```
SSD size [256]:
DRAM size [64]:
L3 size [32]:
L2 size [16]:
L1 size [8]:
Policy (LRU/FIFO/RANDOM) [LRU]:
```

## Output

The program prints the following sections in order:

1. **Configuration** — level sizes, latencies, bandwidth, policy
2. **Access trace** — cycle-by-cycle log of reads, writes, hits, misses, transfers, evictions
3. **Hit/miss stats** — per-level counts and hit rates
4. **Final state** — contents of each memory level after simulation

## Code Structure

- `LRU`, `FIFO`, `RAND` — replacement policies
- `Level` — memory level (SSD, DRAM, or cache) with read/write and eviction
- `MemSim` — clock-driven simulator with `load()`, `read()`, `write()`