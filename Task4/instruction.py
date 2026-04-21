"""
Instruction Module
------------------
Defines the 32-bit R-type instruction format for this processor.

Instruction format (R-type, inspired by MIPS):
  [31:26] opcode    (6 bits)  — 0x00 for R-type
  [25:21] rs        (5 bits)  — source register 1
  [20:16] rt        (5 bits)  — source register 2
  [15:11] rd        (5 bits)  — destination register
  [10:6]  shamt     (5 bits)  — unused (0)
  [5:0]   funct     (6 bits)  — function code

Function codes:
  0x24 (100100) = AND
  0x25 (100101) = OR
  0x64 (1100100) — we use bit 6 of funct as invert flag:
       funct[5] = 1 means invert input A (rs)
       So: funct = 0x24 -> AND
           funct = 0x64 -> AND with invert on rs  (ANDN)

  For this design, the invert flag is encoded in funct bit 5:
       funct & 0x20 != 0  ->  invert_a = True
       funct & 0x1F       ->  base operation (AND=0x04, OR=0x05)

  Simplified funct encoding:
       0x04 = AND
       0x05 = OR
       0x24 = AND with invert_a (bit 5 set)
       0x25 = OR  with invert_a (bit 5 set)
"""

# Funct codes (lower 5 bits = operation, bit 5 = invert flag)
FUNCT_AND       = 0x04   # 000100
FUNCT_OR        = 0x05   # 000101
FUNCT_AND_INV   = 0x24   # 100100  (AND with input A inverted)
FUNCT_OR_INV    = 0x25   # 100101  (OR  with input A inverted)

OPCODE_RTYPE = 0x00

# Bit masks
INVERT_FLAG_BIT = 0x20   # bit 5 of funct
BASE_OP_MASK    = 0x1F   # lower 5 bits of funct


class Instruction:
    """Represents a decoded 32-bit R-type instruction."""

    def __init__(self, opcode: int, rs: int, rt: int, rd: int, shamt: int, funct: int):
        self.opcode = opcode
        self.rs = rs
        self.rt = rt
        self.rd = rd
        self.shamt = shamt
        self.funct = funct

    @property
    def invert_a(self) -> bool:
        """Whether the invert flag is set in the function field."""
        return bool(self.funct & INVERT_FLAG_BIT)

    @property
    def base_funct(self) -> int:
        """The base operation (with invert flag masked off)."""
        return self.funct & BASE_OP_MASK

    @property
    def funct_name(self) -> str:
        base = self.base_funct
        inv = " (invert A)" if self.invert_a else ""
        if base == (FUNCT_AND & BASE_OP_MASK):
            return f"AND{inv}"
        elif base == (FUNCT_OR & BASE_OP_MASK):
            return f"OR{inv}"
        return f"UNKNOWN(0x{self.funct:02X})"

    def __repr__(self) -> str:
        return (
            f"Instruction: {self.funct_name}  "
            f"rd=t{self.rd}, rs=t{self.rs}, rt=t{self.rt}  "
            f"[opcode=0x{self.opcode:02X}, funct=0x{self.funct:02X}]"
        )


def encode_instruction(rd: int, rs: int, rt: int, funct: int, opcode: int = OPCODE_RTYPE) -> int:
    """
    Encode an R-type instruction into a 32-bit integer.

    Format: [opcode(6)][rs(5)][rt(5)][rd(5)][shamt(5)][funct(6)]
    """
    word = 0
    word |= (opcode & 0x3F) << 26
    word |= (rs & 0x1F) << 21
    word |= (rt & 0x1F) << 16
    word |= (rd & 0x1F) << 11
    word |= (0 & 0x1F) << 6       # shamt = 0
    word |= (funct & 0x3F)
    return word


def decode_instruction(word: int) -> Instruction:
    """Decode a 32-bit instruction word into an Instruction object."""
    opcode = (word >> 26) & 0x3F
    rs     = (word >> 21) & 0x1F
    rt     = (word >> 16) & 0x1F
    rd     = (word >> 11) & 0x1F
    shamt  = (word >> 6)  & 0x1F
    funct  = word & 0x3F
    return Instruction(opcode, rs, rt, rd, shamt, funct)


def assemble_program() -> list[int]:
    """
    Assemble the required program:
        and t4, t0, t1    ; t4 = A & B
        and t6, t5, t3    ; t6 = (~C) & D   (t5 holds C, invert flag set)
        or  t0, t4, t6    ; t0 = t4 | t6

    Note: The second instruction uses AND with invert on rs (t2=C).
    Per the assignment, the inversion is handled via the funct field invert bit.

    However, looking at the assembly: "and t6, t5, t3" — t5 is used but
    the assignment states t2=C. The instruction inverts the first source (rs).
    So we encode: AND_INV t6, t2, t3 → t6 = (~t2) & t3 = (~C) & D
    The assembly listing uses t5 as a placeholder for ~C, but in our
    implementation the inversion happens inside the ALU on the rs input.
    """
    program = [
        # and t4, t0, t1  → t4 = t0 & t1 = A & B
        encode_instruction(rd=4, rs=0, rt=1, funct=FUNCT_AND),

        # and t6, t2, t3 with invert on rs → t6 = (~t2) & t3 = (~C) & D
        encode_instruction(rd=6, rs=2, rt=3, funct=FUNCT_AND_INV),

        # or t0, t4, t6  → t0 = t4 | t6
        encode_instruction(rd=0, rs=4, rt=6, funct=FUNCT_OR),
    ]
    return program
