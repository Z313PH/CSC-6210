"""
Processor Module (Single-Cycle Datapath)
-----------------------------------------
Implements the single-cycle execution model:
  Fetch → Decode → Execute → Write-back (all in one cycle)

Connects:
  - Instruction memory (program list)
  - Register file
  - Control unit
  - ALU
  - MUX (for ALU input inversion routing)

Produces an execution trace per instruction showing:
  - Instruction details
  - Control signals
  - Register values after execution
"""

from register_file import RegisterFile
from alu import alu_execute, ALUResult
from mux import mux2to1
from control_unit import generate_control_signals, ControlSignals
from instruction import decode_instruction, Instruction


class CycleTrace:
    """Trace data for a single instruction cycle."""

    def __init__(
        self,
        cycle: int,
        instruction_word: int,
        instruction: Instruction,
        control: ControlSignals,
        read_data1: int,
        read_data2: int,
        alu_input_a: int,
        alu_result: ALUResult,
        reg_snapshot: dict[str, int],
    ):
        self.cycle = cycle
        self.instruction_word = instruction_word
        self.instruction = instruction
        self.control = control
        self.read_data1 = read_data1
        self.read_data2 = read_data2
        self.alu_input_a = alu_input_a
        self.alu_result = alu_result
        self.reg_snapshot = reg_snapshot


class Processor:
    """Single-cycle 32-bit processor."""

    def __init__(self):
        self.reg_file = RegisterFile()
        self.pc = 0  # Program counter
        self.traces: list[CycleTrace] = []

    def load_registers(self, values: dict[int, int]) -> None:
        """Load initial register values (e.g., A, B, C, D into t0–t3)."""
        self.reg_file.load_initial_values(values)

    def execute_program(self, program: list[int]) -> list[CycleTrace]:
        """
        Execute the entire program (list of 32-bit instruction words).
        Each instruction completes in a single cycle:
          1. FETCH:      Read instruction from program[PC]
          2. DECODE:     Decode fields + generate control signals
          3. EXECUTE:    Read registers, run ALU
          4. WRITE-BACK: Write ALU result to destination register
        """
        self.traces = []
        self.pc = 0

        for cycle_num, instr_word in enumerate(program, start=1):
            trace = self._execute_one_cycle(cycle_num, instr_word)
            self.traces.append(trace)
            self.pc += 1

        return self.traces

    def _execute_one_cycle(self, cycle_num: int, instr_word: int) -> CycleTrace:
        """Execute one instruction through the full single-cycle pipeline."""

        # ── FETCH ──
        # Instruction word is provided (simulating instruction memory)

        # ── DECODE ──
        instr = decode_instruction(instr_word)
        control = generate_control_signals(instr)

        # ── EXECUTE ──
        # Read register file (two read ports)
        read_data1 = self.reg_file.read(instr.rs)
        read_data2 = self.reg_file.read(instr.rt)

        # MUX: select ALU input A (normal or inverted path is inside ALU,
        # but conceptually the mux routes the invert control signal)
        # The invert_a signal goes to the ALU which handles inversion internally
        alu_input_a = read_data1  # before inversion (ALU applies it)

        # ALU execution
        alu_result = alu_execute(
            input_a=read_data1,
            input_b=read_data2,
            alu_op=control.alu_op,
            invert_a=control.invert_a,
        )

        # ── WRITE-BACK ──
        self.reg_file.write(instr.rd, alu_result.result, control.reg_write)

        # Snapshot registers after write-back
        reg_snapshot = self.reg_file.dump()

        return CycleTrace(
            cycle=cycle_num,
            instruction_word=instr_word,
            instruction=instr,
            control=control,
            read_data1=read_data1,
            read_data2=read_data2,
            alu_input_a=alu_input_a,
            alu_result=alu_result,
            reg_snapshot=reg_snapshot,
        )
