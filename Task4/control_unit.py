"""
Control Unit Module
-------------------
Decodes instruction fields and generates control signals for the datapath.

Control signals generated:
  - alu_op:       ALU operation selector (AND=0, OR=1)
  - invert_a:     ALU input A inversion flag (for NOT behavior)
  - reg_write:    Register write enable

The control logic differentiates between:
  - Standard AND       (funct=0x04)
  - AND with inversion (funct=0x24, AND-NOT behavior)
  - Standard OR        (funct=0x05)
"""

from instruction import Instruction, INVERT_FLAG_BIT, BASE_OP_MASK, FUNCT_AND, FUNCT_OR
from alu import ALU_AND, ALU_OR


class ControlSignals:
    """Bundle of control signals for one instruction cycle."""

    def __init__(self, alu_op: int, invert_a: bool, reg_write: bool):
        self.alu_op = alu_op
        self.invert_a = invert_a
        self.reg_write = reg_write

    @property
    def alu_op_name(self) -> str:
        return {ALU_AND: "AND", ALU_OR: "OR"}.get(self.alu_op, "???")

    def __repr__(self) -> str:
        return (
            f"ControlSignals: alu_op={self.alu_op_name}({self.alu_op}), "
            f"invert_a={int(self.invert_a)}, "
            f"reg_write={int(self.reg_write)}"
        )


def generate_control_signals(instr: Instruction) -> ControlSignals:
    """
    Decode an instruction and produce the control signals.

    The control unit reads:
      - opcode: must be 0x00 (R-type) for our ISA
      - funct field:
          bit 5 (0x20) → invert_a flag
          bits [4:0]   → base operation
            0x04 → ALU_AND
            0x05 → ALU_OR

    For ALL R-type instructions, reg_write is enabled.
    """
    # Extract invert flag from funct field (not from opcode)
    invert_a = bool(instr.funct & INVERT_FLAG_BIT)

    # Determine ALU operation from base funct
    base = instr.funct & BASE_OP_MASK
    if base == (FUNCT_AND & BASE_OP_MASK):
        alu_op = ALU_AND
    elif base == (FUNCT_OR & BASE_OP_MASK):
        alu_op = ALU_OR
    else:
        raise ValueError(f"Unknown funct code: 0x{instr.funct:02X}")

    # R-type instructions always write back to rd
    reg_write = True

    return ControlSignals(alu_op=alu_op, invert_a=invert_a, reg_write=reg_write)
