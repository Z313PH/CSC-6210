"""
Unit Tests — Single-Cycle Processor (Task 4)
Tests cover all components and end-to-end validation.
"""

import unittest
from register_file import RegisterFile
from alu import alu_execute, ALU_AND, ALU_OR
from mux import mux2to1
from instruction import (
    encode_instruction, decode_instruction, assemble_program,
    FUNCT_AND, FUNCT_OR, FUNCT_AND_INV,
)
from control_unit import generate_control_signals
from processor import Processor


class TestRegisterFile(unittest.TestCase):
    def test_read_write(self):
        rf = RegisterFile()
        rf.write(3, 0xDEADBEEF, write_enable=True)
        self.assertEqual(rf.read(3), 0xDEADBEEF)

    def test_write_disabled(self):
        rf = RegisterFile()
        rf.write(3, 0xDEADBEEF, write_enable=False)
        self.assertEqual(rf.read(3), 0)

    def test_initial_values(self):
        rf = RegisterFile()
        rf.load_initial_values({0: 5, 1: 10})
        self.assertEqual(rf.read(0), 5)
        self.assertEqual(rf.read(1), 10)
        self.assertEqual(rf.read(2), 0)

    def test_32bit_mask(self):
        rf = RegisterFile()
        rf.write(0, 0x1FFFFFFFF, write_enable=True)
        self.assertEqual(rf.read(0), 0xFFFFFFFF)


class TestALU(unittest.TestCase):
    def test_and(self):
        r = alu_execute(0xFF00FF00, 0xF0F0F0F0, ALU_AND)
        self.assertEqual(r.result, 0xF000F000)

    def test_or(self):
        r = alu_execute(0xFF00FF00, 0xF0F0F0F0, ALU_OR)
        self.assertEqual(r.result, 0xFFF0FFF0)

    def test_and_with_invert(self):
        # ~0xFF = 0xFFFFFF00, then & 0x0F = 0x00
        r = alu_execute(0xFF, 0x0F, ALU_AND, invert_a=True)
        expected = (~0xFF & 0xFFFFFFFF) & 0x0F
        self.assertEqual(r.result, expected)

    def test_invert_all_ones(self):
        r = alu_execute(0xFFFFFFFF, 0xFFFFFFFF, ALU_AND, invert_a=True)
        self.assertEqual(r.result, 0)  # ~all_ones = 0, 0 & anything = 0

    def test_invert_zero(self):
        r = alu_execute(0, 0xFFFFFFFF, ALU_AND, invert_a=True)
        self.assertEqual(r.result, 0xFFFFFFFF)  # ~0 = all_ones


class TestMUX(unittest.TestCase):
    def test_select_0(self):
        self.assertEqual(mux2to1(10, 20, False), 10)

    def test_select_1(self):
        self.assertEqual(mux2to1(10, 20, True), 20)


class TestInstruction(unittest.TestCase):
    def test_encode_decode_and(self):
        word = encode_instruction(rd=4, rs=0, rt=1, funct=FUNCT_AND)
        instr = decode_instruction(word)
        self.assertEqual(instr.rd, 4)
        self.assertEqual(instr.rs, 0)
        self.assertEqual(instr.rt, 1)
        self.assertEqual(instr.base_funct, FUNCT_AND & 0x1F)
        self.assertFalse(instr.invert_a)

    def test_encode_decode_and_inv(self):
        word = encode_instruction(rd=6, rs=2, rt=3, funct=FUNCT_AND_INV)
        instr = decode_instruction(word)
        self.assertEqual(instr.rd, 6)
        self.assertEqual(instr.rs, 2)
        self.assertEqual(instr.rt, 3)
        self.assertTrue(instr.invert_a)

    def test_encode_decode_or(self):
        word = encode_instruction(rd=0, rs=4, rt=6, funct=FUNCT_OR)
        instr = decode_instruction(word)
        self.assertEqual(instr.rd, 0)
        self.assertFalse(instr.invert_a)

    def test_assemble_program_length(self):
        prog = assemble_program()
        self.assertEqual(len(prog), 3)


class TestControlUnit(unittest.TestCase):
    def test_and_signals(self):
        word = encode_instruction(rd=4, rs=0, rt=1, funct=FUNCT_AND)
        instr = decode_instruction(word)
        ctrl = generate_control_signals(instr)
        self.assertEqual(ctrl.alu_op, ALU_AND)
        self.assertFalse(ctrl.invert_a)
        self.assertTrue(ctrl.reg_write)

    def test_and_inv_signals(self):
        word = encode_instruction(rd=6, rs=2, rt=3, funct=FUNCT_AND_INV)
        instr = decode_instruction(word)
        ctrl = generate_control_signals(instr)
        self.assertEqual(ctrl.alu_op, ALU_AND)
        self.assertTrue(ctrl.invert_a)
        self.assertTrue(ctrl.reg_write)

    def test_or_signals(self):
        word = encode_instruction(rd=0, rs=4, rt=6, funct=FUNCT_OR)
        instr = decode_instruction(word)
        ctrl = generate_control_signals(instr)
        self.assertEqual(ctrl.alu_op, ALU_OR)
        self.assertFalse(ctrl.invert_a)
        self.assertTrue(ctrl.reg_write)


class TestProcessorEndToEnd(unittest.TestCase):
    """Section 5 validation: execute program and verify Y = A·B + C'·D"""

    def _run(self, A, B, C, D):
        cpu = Processor()
        cpu.load_registers({0: A, 1: B, 2: C, 3: D})
        program = assemble_program()
        traces = cpu.execute_program(program)
        Y = cpu.reg_file.read(0)
        expected = ((A & B) | ((~C & 0xFFFFFFFF) & D)) & 0xFFFFFFFF
        return Y, expected, traces

    def test_simple_all_ones(self):
        Y, expected, _ = self._run(0xFFFFFFFF, 0xFFFFFFFF, 0x00000000, 0xFFFFFFFF)
        self.assertEqual(Y, expected)

    def test_simple_all_zeros(self):
        Y, expected, _ = self._run(0, 0, 0, 0)
        self.assertEqual(Y, expected)

    def test_example_1(self):
        # A=0xFF, B=0x0F, C=0xF0, D=0xFF
        A, B, C, D = 0xFF, 0x0F, 0xF0, 0xFF
        Y, expected, traces = self._run(A, B, C, D)
        self.assertEqual(Y, expected)
        # Check intermediates
        t4 = traces[0].alu_result.result
        t6 = traces[1].alu_result.result
        self.assertEqual(t4, A & B)
        self.assertEqual(t6, (~C & 0xFFFFFFFF) & D)

    def test_example_small(self):
        # A=5 (0101), B=3 (0011), C=6 (0110), D=9 (1001)
        A, B, C, D = 5, 3, 6, 9
        Y, expected, traces = self._run(A, B, C, D)
        self.assertEqual(Y, expected)

    def test_example_large(self):
        A, B, C, D = 0xAAAAAAAA, 0x55555555, 0x0F0F0F0F, 0xF0F0F0F0
        Y, expected, _ = self._run(A, B, C, D)
        self.assertEqual(Y, expected)

    def test_c_all_ones(self):
        # ~C = 0 when C = 0xFFFFFFFF, so C'·D = 0
        A, B, C, D = 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF
        Y, expected, _ = self._run(A, B, C, D)
        self.assertEqual(Y, expected)
        self.assertEqual(Y, 0xFFFFFFFF)  # A&B = all ones, C'&D = 0, OR = all ones

    def test_only_cd_term(self):
        # A&B = 0, rely on C'·D
        A, B, C, D = 0, 0, 0, 0xFFFFFFFF
        Y, expected, _ = self._run(A, B, C, D)
        self.assertEqual(Y, expected)
        self.assertEqual(Y, 0xFFFFFFFF)  # ~0 & 0xFFFFFFFF

    def test_three_instructions_executed(self):
        _, _, traces = self._run(1, 1, 1, 1)
        self.assertEqual(len(traces), 3)

    def test_control_signals_per_cycle(self):
        _, _, traces = self._run(1, 1, 1, 1)
        # Cycle 1: AND, no invert
        self.assertEqual(traces[0].control.alu_op, ALU_AND)
        self.assertFalse(traces[0].control.invert_a)
        # Cycle 2: AND, with invert
        self.assertEqual(traces[1].control.alu_op, ALU_AND)
        self.assertTrue(traces[1].control.invert_a)
        # Cycle 3: OR, no invert
        self.assertEqual(traces[2].control.alu_op, ALU_OR)
        self.assertFalse(traces[2].control.invert_a)


if __name__ == "__main__":
    unittest.main()
