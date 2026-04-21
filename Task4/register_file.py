"""
Register File Module
--------------------
Implements an 8-register file (t0–t7) with:
  - 2 read ports (read_reg1, read_reg2)
  - 1 write port (write_reg, write_data, write_enable)

Each register holds a 32-bit value.
"""


class RegisterFile:
    NUM_REGISTERS = 8
    REGISTER_NAMES = {i: f"t{i}" for i in range(8)}

    def __init__(self):
        """Initialize all 8 registers to 0."""
        self.registers = [0x00000000] * self.NUM_REGISTERS

    def read(self, reg_num: int) -> int:
        """Read a 32-bit value from register reg_num."""
        if not (0 <= reg_num < self.NUM_REGISTERS):
            raise ValueError(f"Invalid register number: {reg_num}")
        return self.registers[reg_num]

    def write(self, reg_num: int, data: int, write_enable: bool) -> None:
        """Write a 32-bit value to register reg_num if write_enable is True."""
        if not write_enable:
            return
        if not (0 <= reg_num < self.NUM_REGISTERS):
            raise ValueError(f"Invalid register number: {reg_num}")
        # Mask to 32 bits
        self.registers[reg_num] = data & 0xFFFFFFFF

    def load_initial_values(self, values: dict[int, int]) -> None:
        """Load initial values into registers. values = {reg_num: value}."""
        for reg_num, value in values.items():
            self.registers[reg_num] = value & 0xFFFFFFFF

    def dump(self) -> dict[str, int]:
        """Return all register values as {name: value}."""
        return {self.REGISTER_NAMES[i]: self.registers[i] for i in range(self.NUM_REGISTERS)}

    def __repr__(self) -> str:
        lines = []
        for i in range(self.NUM_REGISTERS):
            val = self.registers[i]
            lines.append(f"  {self.REGISTER_NAMES[i]} = 0x{val:08X} ({val})")
        return "RegisterFile:\n" + "\n".join(lines)
