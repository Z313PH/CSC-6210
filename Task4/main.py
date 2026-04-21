
from processor import Processor
from instruction import assemble_program


def format_bin32(val: int) -> str:
    """Format a 32-bit value as binary string."""
    return format(val & 0xFFFFFFFF, "032b")


def run_processor(A: int, B: int, C: int, D: int) -> None:
    """
    Initialize registers with A, B, C, D, execute the program,
    and display the full execution trace.
    """
    # ── Setup ──
    cpu = Processor()

    # Load initial values: t0=A, t1=B, t2=C, t3=D
    cpu.load_registers({0: A, 1: B, 2: C, 3: D})

    # Assemble the program
    program = assemble_program()

    # Assembly listing for display
    asm_listing = [
        "and t4, t0, t1    ; t4 = A & B",
        "and t6, t2, t3    ; t6 = (~C) & D   [invert on rs]",
        "or  t0, t4, t6    ; t0 = t4 | t6 = Y",
    ]

    print("=" * 70)
    print("  SINGLE-CYCLE PROCESSOR — Task 4")
    print("  Computing: Y = A·B + C'·D")
    print("=" * 70)

    # ── Input Values ──
    print(f"\n  Input Values:")
    print(f"    A = {A} (0x{A & 0xFFFFFFFF:08X})  ->  t0")
    print(f"    B = {B} (0x{B & 0xFFFFFFFF:08X})  ->  t1")
    print(f"    C = {C} (0x{C & 0xFFFFFFFF:08X})  ->  t2")
    print(f"    D = {D} (0x{D & 0xFFFFFFFF:08X})  ->  t3")

    # ── Initial Register State ──
    print(f"\n  Initial Register State:")
    for name, val in cpu.reg_file.dump().items():
        print(f"    {name} = 0x{val:08X}")

    # ── Execute ──
    print(f"\n  Program ({len(program)} instructions):")
    for i, asm in enumerate(asm_listing):
        print(f"    [{i}] {asm}")

    traces = cpu.execute_program(program)

    # ── Execution Trace ──
    print(f"\n{'=' * 70}")
    print("  EXECUTION TRACE")
    print(f"{'=' * 70}")

    for trace in traces:
        instr = trace.instruction
        ctrl = trace.control

        print(f"\n  ── Cycle {trace.cycle} ──")
        print(f"  Assembly:     {asm_listing[trace.cycle - 1]}")
        print(f"  Instruction:  0x{trace.instruction_word:08X}  ({format_bin32(trace.instruction_word)})")
        print(f"  Decoded:      {instr}")

        # Control signals
        print(f"\n  Control Signals:")
        print(f"    ALU Operation:  {ctrl.alu_op_name} ({ctrl.alu_op})")
        print(f"    Invert A:       {int(ctrl.invert_a)}")
        print(f"    Register Write: {int(ctrl.reg_write)}")

        # ALU inputs/output
        print(f"\n  ALU Execution:")
        print(f"    Read rs (t{instr.rs}):   0x{trace.read_data1:08X}  ({format_bin32(trace.read_data1)})")
        if ctrl.invert_a:
            inverted = (~trace.read_data1) & 0xFFFFFFFF
            print(f"    After invert:    0x{inverted:08X}  ({format_bin32(inverted)})")
        print(f"    Read rt (t{instr.rt}):   0x{trace.read_data2:08X}  ({format_bin32(trace.read_data2)})")
        print(f"    ALU Result:      0x{trace.alu_result.result:08X}  ({format_bin32(trace.alu_result.result)})")

        # Write-back
        print(f"\n  Write-back:")
        print(f"    t{instr.rd} <- 0x{trace.alu_result.result:08X}")

        # Register state after this cycle
        print(f"\n  Registers after cycle {trace.cycle}:")
        for name, val in trace.reg_snapshot.items():
            marker = " <--" if name == f"t{instr.rd}" else ""
            print(f"    {name} = 0x{val:08X}{marker}")

    # ── Final Result ──
    final_regs = traces[-1].reg_snapshot
    Y = final_regs["t0"]

    print(f"\n{'=' * 70}")
    print("  FINAL RESULT")
    print(f"{'=' * 70}")
    print(f"\n  Intermediate values:")
    print(f"    t4 = A & B     = 0x{final_regs['t4']:08X} ({final_regs['t4']})")
    print(f"    t6 = (~C) & D  = 0x{final_regs['t6']:08X} ({final_regs['t6']})")
    print(f"\n  Y = A·B + C'·D = t0 = 0x{Y:08X} ({Y})")
    print(f"  Y in binary: {format_bin32(Y)}")

    # ── Validation ──
    expected = ((A & B) | ((~C & 0xFFFFFFFF) & D)) & 0xFFFFFFFF
    print(f"\n  Validation:")
    print(f"    Expected: 0x{expected:08X}")
    print(f"    Got:      0x{Y:08X}")
    print(f"    Result:   {'PASS' if Y == expected else 'FAIL'}")
    print(f"\n{'=' * 70}")


def main():
    print("\nEnter 32-bit input values (decimal or hex with 0x prefix):\n")

    def read_val(prompt: str) -> int:
        while True:
            try:
                s = input(prompt).strip()
                if s.lower().startswith("0x"):
                    return int(s, 16)
                return int(s)
            except ValueError:
                print("  Invalid input. Enter a decimal integer or hex (0x...).")

    A = read_val("  A = ")
    B = read_val("  B = ")
    C = read_val("  C = ")
    D = read_val("  D = ")

    run_processor(A, B, C, D)


if __name__ == "__main__":
    main()
