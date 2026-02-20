'''
Elie Wamana

Implements:
        unit tests for every feature
'''

import unittest

from process_design import (
    MIN_INT32,
    MAX_INT32,
    convert,
    bin32_to_int32,
    int32_to_bin32,
)


class TestDataSystems(unittest.TestCase):

    def test_positive(self):
        r = convert("123", "DEC")
        self.assertEqual(r.value_out, "123")
        self.assertEqual(r.overflow, 0)
        self.assertEqual(r.saturated, 0)

    def test_zero(self):
        r = convert("0", "BIN")
        self.assertEqual(len(r.value_out), 32)
        self.assertTrue(set(r.value_out) <= {"0", "1"})
        self.assertEqual(r.overflow, 0)
        self.assertEqual(r.saturated, 0)
        self.assertEqual(r.value_out, "0" * 32)

    def test_negative(self):
        r = convert("-123", "HEX")
        self.assertEqual(r.overflow, 0)
        self.assertEqual(r.saturated, 0)
        self.assertEqual(bin32_to_int32(r.bin32), -123)

    def test_boundary_max(self):
        r = convert(str(MAX_INT32), "BIN")
        self.assertEqual(r.overflow, 0)
        self.assertEqual(r.saturated, 0)
        self.assertEqual(r.bin32[0], "0")  # sign bit 0
        self.assertEqual(bin32_to_int32(r.bin32), MAX_INT32)

    def test_boundary_min(self):
        r = convert(str(MIN_INT32), "HEX")
        self.assertEqual(r.overflow, 0)
        self.assertEqual(r.saturated, 0)
        self.assertEqual(r.bin32, "1" + "0" * 31)  # 0x80000000 pattern
        self.assertEqual(bin32_to_int32(r.bin32), MIN_INT32)

    def test_overflow_max_plus_1(self):
        r = convert(str(MAX_INT32 + 1), "DEC")
        self.assertEqual(r.overflow, 1)
        self.assertEqual(r.saturated, 1)
        self.assertEqual(r.value_out, str(MAX_INT32))

    def test_overflow_min_minus_1(self):
        r = convert(str(MIN_INT32 - 1), "DEC")
        self.assertEqual(r.overflow, 1)
        self.assertEqual(r.saturated, 1)
        self.assertEqual(r.value_out, str(MIN_INT32))

    def test_bin_roundtrip_examples(self):
        # sanity checks
        self.assertEqual(bin32_to_int32(int32_to_bin32(-1)), -1)
        self.assertEqual(bin32_to_int32(int32_to_bin32(5)), 5)
        self.assertEqual(bin32_to_int32(int32_to_bin32(-5)), -5)


if __name__ == "__main__":
    unittest.main()