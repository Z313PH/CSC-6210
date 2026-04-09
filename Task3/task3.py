
import random, sys
from collections import OrderedDict, deque

# ── Config (sizes = number of 32-bit instructions) ───────────────────────
CONFIG = {
    "ssd": 256, "dram": 64, "l3": 32, "l2": 16, "l1": 8,
    "latency":   {"SSD->DRAM": 10, "DRAM->L3": 5, "L3->L2": 3, "L2->L1": 2, "L1->CPU": 1},
    "bandwidth": {"SSD->DRAM": 4,  "DRAM->L3": 4, "L3->L2": 2, "L2->L1": 2, "L1->CPU": 1},
    "policy": "LRU",  # LRU, FIFO, or RANDOM
}
LEVELS = ["SSD", "DRAM", "L3", "L2", "L1"]

class LRU:
    def __init__(self): self._o = OrderedDict()
    def access(self, a): self._o.pop(a, None); self._o[a] = 1
    def evict(self): return self._o.popitem(last=False)[0]
    def remove(self, a): self._o.pop(a, None)

class FIFO:
    def __init__(self): self._q, self._s = deque(), set()
    def access(self, a):
        if a not in self._s: self._q.append(a); self._s.add(a)
    def evict(self): a = self._q.popleft(); self._s.discard(a); return a
    def remove(self, a):
        if a in self._s: self._s.discard(a); self._q = deque(x for x in self._q if x != a)

class RAND:
    def __init__(self): self._s = set()
    def access(self, a): self._s.add(a)
    def evict(self): a = random.choice(list(self._s)); self._s.discard(a); return a
    def remove(self, a): self._s.discard(a)

POLICIES = {"LRU": LRU, "FIFO": FIFO, "RANDOM": RAND}

class Level:
    def __init__(self, name, cap, policy=None):
        self.name, self.cap, self.data, self.policy = name, cap, {}, policy
        self.hits = self.misses = 0

    def read(self, a):
        if a in self.data:
            self.hits += 1
            if self.policy: self.policy.access(a)
            return self.data[a]
        self.misses += 1; return None

    def write(self, a, v):
        evicted = None
        if a not in self.data and len(self.data) >= self.cap:
            ea = self.policy.evict() if self.policy else next(iter(self.data))
            evicted = (ea, self.data.pop(ea))
        self.data[a] = v
        if self.policy: self.policy.access(a)
        return evicted

class MemSim:
    def __init__(self, cfg):
        self.cfg, self.clock, self.log, self.pending = cfg, 0, [], []
        p = POLICIES[cfg["policy"]]
        self.lvl = {n: Level(n, cfg[n.lower()], p() if n not in ("SSD","DRAM") else None) for n in LEVELS}
        sizes = [self.lvl[n].cap for n in LEVELS]
        for i in range(len(sizes)-1):
            assert sizes[i] > sizes[i+1], f"{LEVELS[i]}({sizes[i]}) must be > {LEVELS[i+1]}({sizes[i+1]})"

    def _log(self, msg): self.log.append(f"[Cycle {self.clock:>4}] {msg}")

    def _tick(self):
        self.clock += 1
        done, rest = [], []
        for t in self.pending:
            t[4] -= 1
            (done if t[4] <= 0 else rest).append(t)
        self.pending = rest
        for instrs, src, dst, _, _ in done:
            if dst == "CPU":
                for a, v in instrs: self._log(f"CPU received 0x{a:04X}")
            else:
                for a, v in instrs:
                    ev = self.lvl[dst].write(a, v)
                    self._log(f"Moved 0x{a:04X}: {src} -> {dst}")
                    if ev: self._evict(dst, *ev)

    def _drain(self):
        while self.pending: self._tick()

    def _evict(self, lvl, addr, val):
        i = LEVELS.index(lvl)
        if i > 0:
            lower = LEVELS[i-1]
            self._log(f"Evicted 0x{addr:04X} from {lvl} -> write-back {lower}")
            self.lvl[lower].write(addr, val)

    def _transfer(self, src, dst, instrs):
        k = f"{src}->{dst}"
        lat, bw = self.cfg["latency"][k], self.cfg["bandwidth"][k]
        for i in range(0, len(instrs), bw):
            batch = instrs[i:i+bw]
            self.pending.append([batch, src, dst, lat, lat])
            self._log(f"Transfer {k} [{', '.join(f'0x{a:04X}' for a,_ in batch)}] lat={lat}")

    def load(self, program):
        for a, v in program: self.lvl["SSD"].data[a] = v
        self._log(f"Loaded {len(program)} instructions into SSD")

    def read(self, addr):
        self._log(f"CPU READ 0x{addr:04X}")
        found = None
        for n in reversed(LEVELS):
            r = self.lvl[n].read(addr)
            if r is not None:
                self._log(f"  HIT  {n}"); found = (n, r); break
            self._log(f"  MISS {n}")
        if not found: self._log("  NOT FOUND"); return None
        name, val = found
        si = LEVELS.index(name)
        for i in range(si, len(LEVELS)-1):
            self._transfer(LEVELS[i], LEVELS[i+1], [(addr, val)]); self._drain()
        self._transfer("L1", "CPU", [(addr, val)]); self._drain()
        return val

    def write(self, addr, val):
        self._log(f"CPU WRITE 0x{val:08X} -> 0x{addr:04X}")
        ev = self.lvl["L1"].write(addr, val)
        self._log("  Wrote to L1")
        if ev: self._evict("L1", *ev)

    def print_config(self):
        print("=" * 58 + "\n  MEMORY HIERARCHY CONFIGURATION\n" + "=" * 58)
        print(f"  Policy: {self.cfg['policy']}\n")
        print(f"  {'Level':<6} {'Cap':>6} {'Latency':>8} {'BW':>4}")
        print(f"  {'-'*6} {'-'*6} {'-'*8} {'-'*4}")
        for i, n in enumerate(LEVELS):
            k = f"{LEVELS[i-1]}->{n}" if i > 0 else None
            lat = str(self.cfg["latency"].get(k,"")) if k else "—"
            bw  = str(self.cfg["bandwidth"].get(k,"")) if k else "—"
            print(f"  {n:<6} {self.lvl[n].cap:>6} {lat:>8} {bw:>4}")
        print(f"  {'CPU':<6} {'—':>6} {self.cfg['latency']['L1->CPU']:>8} {self.cfg['bandwidth']['L1->CPU']:>4}")
        print("=" * 58 + "\n")

    def print_trace(self):
        print("=" * 58 + "\n  ACCESS TRACE\n" + "=" * 58)
        for l in self.log: print(f"  {l}")
        print("=" * 58 + "\n")

    def print_stats(self):
        print("=" * 58 + "\n  CACHE HIT/MISS STATS\n" + "=" * 58)
        print(f"  {'Level':<6} {'Hits':>6} {'Miss':>6} {'Rate':>8}")
        for n in LEVELS:
            lv = self.lvl[n]; t = lv.hits + lv.misses
            r = f"{lv.hits/t*100:.1f}%" if t else "N/A"
            print(f"  {n:<6} {lv.hits:>6} {lv.misses:>6} {r:>8}")
        print("=" * 58 + "\n")

    def print_state(self):
        print("=" * 58 + "\n  FINAL STATE\n" + "=" * 58)
        for n in LEVELS:
            lv = self.lvl[n]
            print(f"  {n} ({len(lv.data)}/{lv.cap}):")
            for a in sorted(lv.data): print(f"    0x{a:04X} = 0x{lv.data[a]:08X}")
        print("=" * 58 + "\n")

# ── Main ─────────────────────────────────────────────────────────────────
def main():
    cfg = dict(CONFIG)
    if sys.stdin.isatty():
        for k in ["ssd","dram","l3","l2","l1"]:
            r = input(f"  {k.upper()} size [{cfg[k]}]: ").strip()
            if r: cfg[k] = int(r)
        r = input(f"  Policy (LRU/FIFO/RANDOM) [{cfg['policy']}]: ").strip()
        if r: cfg["policy"] = r.upper()
    else:
        print("  Running with defaults.\n")

    sim = MemSim(cfg)
    sim.print_config()

    prog = [(a, random.randint(0, 0xFFFFFFFF)) for a in range(min(20, cfg["ssd"]))]
    sim.load(prog)

    print("  --- READ operations ---")
    for a in [0,1,2,3,0,4,5,6,7,0,2,8,9,10,1,3]: sim.read(a)

    print("\n  --- WRITE operations ---")
    sim.write(0x0000, 0xDEADBEEF)
    sim.write(0x0001, 0xCAFEBABE)
    sim.write(0x00FF, 0x12345678)

    print()
    sim.print_trace()
    sim.print_stats()
    sim.print_state()
    print(f"  Total clock cycles: {sim.clock}\n")

if __name__ == "__main__":
    main()