"""
Unit tests for Task 2: Truth Table -> Boolean Equation -> K-Map Simplification
"""

import unittest
from boolean_simplifier import (
    validate_truth_table,
    sort_truth_table,
    get_minterms,
    get_maxterms,
    canonical_sop,
    canonical_pos,
    build_kmap,
    quine_mccluskey,
    essential_prime_implicants,
    simplify_sop,
    simplify_pos,
    validate_simplification,
    evaluate_simplified_sop,
    evaluate_simplified_pos,
    minterm_to_bits,
    row_to_minterm_index,
)


# Helper to build truth table rows from output list
def make_rows(n: int, outputs: list[int]) -> list[tuple[tuple[int, ...], int]]:
    """Build truth table rows from a list of outputs (in binary order)."""
    import itertools
    combos = list(itertools.product((0, 1), repeat=n))
    assert len(combos) == len(outputs)
    return [(combo, out) for combo, out in zip(combos, outputs)]


class TestValidation(unittest.TestCase):
    """Section 1: Input validation tests."""

    def test_valid_2var(self):
        rows = make_rows(2, [0, 1, 1, 0])
        validate_truth_table(2, rows)  # Should not raise

    def test_wrong_row_count(self):
        rows = make_rows(2, [0, 1, 1, 0])[:3]
        with self.assertRaises(ValueError):
            validate_truth_table(2, rows)

    def test_duplicate_input(self):
        rows = [((0, 0), 0), ((0, 0), 1), ((1, 0), 0), ((1, 1), 1)]
        with self.assertRaises(ValueError):
            validate_truth_table(2, rows)

    def test_invalid_output(self):
        rows = [((0, 0), 0), ((0, 1), 2), ((1, 0), 0), ((1, 1), 1)]
        with self.assertRaises(ValueError):
            validate_truth_table(2, rows)


class TestMintermMaxterm(unittest.TestCase):
    """Test minterm/maxterm extraction."""

    def test_minterms_2var(self):
        # F = A'B + AB' (XOR): outputs [0, 1, 1, 0]
        rows = make_rows(2, [0, 1, 1, 0])
        self.assertEqual(get_minterms(rows), [1, 2])

    def test_maxterms_2var(self):
        rows = make_rows(2, [0, 1, 1, 0])
        self.assertEqual(get_maxterms(rows), [0, 3])

    def test_all_ones(self):
        rows = make_rows(2, [1, 1, 1, 1])
        self.assertEqual(get_minterms(rows), [0, 1, 2, 3])
        self.assertEqual(get_maxterms(rows), [])

    def test_all_zeros(self):
        rows = make_rows(2, [0, 0, 0, 0])
        self.assertEqual(get_minterms(rows), [])
        self.assertEqual(get_maxterms(rows), [0, 1, 2, 3])


class TestCanonicalForms(unittest.TestCase):
    """Test canonical SOP and POS generation."""

    def test_sop_2var_xor(self):
        rows = make_rows(2, [0, 1, 1, 0])
        sop = canonical_sop(2, rows)
        self.assertIn("A'B", sop)
        self.assertIn("AB'", sop)
        self.assertIn("+", sop)

    def test_pos_2var_xor(self):
        rows = make_rows(2, [0, 1, 1, 0])
        pos = canonical_pos(2, rows)
        self.assertIn("(A + B)", pos)
        self.assertIn("(A' + B')", pos)

    def test_sop_all_ones(self):
        rows = make_rows(2, [1, 1, 1, 1])
        self.assertEqual(canonical_sop(2, rows), "1")

    def test_sop_all_zeros(self):
        rows = make_rows(2, [0, 0, 0, 0])
        self.assertEqual(canonical_sop(2, rows), "0")

    def test_pos_all_ones(self):
        rows = make_rows(2, [1, 1, 1, 1])
        self.assertEqual(canonical_pos(2, rows), "1")

    def test_pos_all_zeros(self):
        rows = make_rows(2, [0, 0, 0, 0])
        self.assertEqual(canonical_pos(2, rows), "0")


class TestKMap(unittest.TestCase):
    """Test K-Map construction."""

    def test_kmap_2var(self):
        rows = make_rows(2, [0, 1, 1, 0])
        kmap = build_kmap(2, rows)
        self.assertEqual(len(kmap['grid']), 2)
        self.assertEqual(len(kmap['grid'][0]), 2)

    def test_kmap_3var(self):
        rows = make_rows(3, [0, 1, 1, 0, 1, 0, 0, 1])
        kmap = build_kmap(3, rows)
        self.assertEqual(len(kmap['grid']), 2)
        self.assertEqual(len(kmap['grid'][0]), 4)

    def test_kmap_4var(self):
        rows = make_rows(4, [0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1])
        kmap = build_kmap(4, rows)
        self.assertEqual(len(kmap['grid']), 4)
        self.assertEqual(len(kmap['grid'][0]), 4)


class TestSimplification(unittest.TestCase):
    """Test Quine-McCluskey simplification and validation."""

    def test_simplify_and_gate(self):
        # F = AB: outputs [0, 0, 0, 1]
        rows = make_rows(2, [0, 0, 0, 1])
        expr, essentials = simplify_sop(2, rows)
        self.assertEqual(expr, "AB")

    def test_simplify_or_gate(self):
        # F = A + B: outputs [0, 1, 1, 1]
        rows = make_rows(2, [0, 1, 1, 1])
        expr, essentials = simplify_sop(2, rows)
        # Should simplify to A + B (two prime implicants)
        self.assertIn("A", expr)
        self.assertIn("B", expr)

    def test_simplify_single_var(self):
        # F = A: outputs [0, 0, 1, 1]
        rows = make_rows(2, [0, 0, 1, 1])
        expr, essentials = simplify_sop(2, rows)
        self.assertEqual(expr, "A")

    def test_simplify_3var(self):
        # F(A,B,C) = sum(1,2,5,6) = A'B'C + A'BC' + AB'C + ABC'
        # Simplified: B'C + BC' = B XOR C
        rows = make_rows(3, [0, 1, 1, 0, 0, 1, 1, 0])
        expr, essentials = simplify_sop(3, rows)
        # Should have two terms
        self.assertIn("+", expr)

    def test_constant_zero(self):
        rows = make_rows(2, [0, 0, 0, 0])
        expr, essentials = simplify_sop(2, rows)
        self.assertEqual(expr, "0")

    def test_constant_one(self):
        rows = make_rows(2, [1, 1, 1, 1])
        expr, essentials = simplify_sop(2, rows)
        self.assertEqual(expr, "1")


class TestRoundTripValidation(unittest.TestCase):
    """Section 3: Validate simplified expression matches original truth table."""

    def _validate_sop(self, n, outputs):
        rows = make_rows(n, outputs)
        expr, essentials = simplify_sop(n, rows)
        passed, mismatches = validate_simplification(n, rows, essentials, "SOP", expr)
        self.assertTrue(passed, f"SOP validation failed: {mismatches}")

    def _validate_pos(self, n, outputs):
        rows = make_rows(n, outputs)
        expr, essentials = simplify_pos(n, rows)
        passed, mismatches = validate_simplification(n, rows, essentials, "POS", expr)
        self.assertTrue(passed, f"POS validation failed: {mismatches}")

    def test_sop_2var_xor(self):
        self._validate_sop(2, [0, 1, 1, 0])

    def test_sop_2var_and(self):
        self._validate_sop(2, [0, 0, 0, 1])

    def test_sop_2var_or(self):
        self._validate_sop(2, [0, 1, 1, 1])

    def test_sop_3var(self):
        self._validate_sop(3, [0, 1, 1, 0, 0, 1, 1, 0])

    def test_sop_3var_complex(self):
        self._validate_sop(3, [1, 0, 1, 1, 0, 0, 1, 1])

    def test_sop_4var(self):
        self._validate_sop(4, [0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1])

    def test_pos_2var_xor(self):
        self._validate_pos(2, [0, 1, 1, 0])

    def test_pos_2var_and(self):
        self._validate_pos(2, [0, 0, 0, 1])

    def test_pos_3var(self):
        self._validate_pos(3, [0, 1, 1, 0, 0, 1, 1, 0])

    def test_pos_4var(self):
        self._validate_pos(4, [0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1])

    def test_sop_all_zeros(self):
        self._validate_sop(2, [0, 0, 0, 0])

    def test_sop_all_ones(self):
        self._validate_sop(2, [1, 1, 1, 1])

    def test_pos_all_zeros(self):
        self._validate_pos(2, [0, 0, 0, 0])

    def test_pos_all_ones(self):
        self._validate_pos(2, [1, 1, 1, 1])


if __name__ == "__main__":
    unittest.main()
