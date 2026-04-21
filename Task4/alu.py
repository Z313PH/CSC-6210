
# ALU operation codes
ALU_AND = 0b00
ALU_OR  = 0b01


class ALUResult:

    def __init__(self, result: int, operation: int, invert_a: bool):
        self.result = result
        self.operation = operation
        self.invert_a = invert_a

    @property
    def op_name(self) -> str:
        names = {ALU_AND: "AND", ALU_OR: "OR"}
        return names.get(self.operation, "???")

    def __repr__(self) -> str:
        inv = " (input A inverted)" if self.invert_a else ""
        return f"ALU: {self.op_name}{inv} -> 0x{self.result:08X}"


def alu_execute(input_a: int, input_b: int, alu_op: int, invert_a: bool = False) -> ALUResult:
    """
    Execute an ALU operation on two 32-bit inputs.

    Parameters:
        input_a:  First operand (from register read port 1)
        input_b:  Second operand (from register read port 2)
        alu_op:   Operation selector (ALU_AND or ALU_OR)
        invert_a: If True, bitwise invert input_a before the operation

    Returns:
        ALUResult with the 32-bit result
    """
    # Apply inversion if the control signal is set
    if invert_a:
        input_a = (~input_a) & 0xFFFFFFFF

    # Perform the selected operation
    if alu_op == ALU_AND:
        result = (input_a & input_b) & 0xFFFFFFFF
    elif alu_op == ALU_OR:
        result = (input_a | input_b) & 0xFFFFFFFF
    else:
        raise ValueError(f"Unknown ALU operation: {alu_op}")

    return ALUResult(result, alu_op, invert_a)
