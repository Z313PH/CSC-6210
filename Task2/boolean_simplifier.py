from __future__ import annotations
import sys
import itertools
from typing import Optional


def get_variable_names(n: int) -> list[str]:
    #Generate variable names A, B, C, ... for n variables
    return [chr(ord('A') + i) for i in range(n)]


def parse_truth_table_interactive(n: int) -> list[tuple[tuple[int, ...], int]]:
    num_rows = 2 ** n
    var_names = get_variable_names(n)
    header = " ".join(var_names) + " | F"
    print(f"\nEnter the truth table ({num_rows} rows).")
    print(f"Format per row: {' '.join(['0/1'] * n)} <output 0/1>")
    print(f"  {header}")
    print(f"  {'-' * len(header)}")

    rows: list[tuple[tuple[int, ...], int]] = []
    for i in range(num_rows):
        while True:
            try:
                line = input(f"  Row {i + 1}: ").strip()
                parts = line.split()
                if len(parts) != n + 1:
                    print(f"    Error: expected {n + 1} values (got {len(parts)}). Try again.")
                    continue
                values = [int(p) for p in parts]
                if any(v not in (0, 1) for v in values):
                    print("    Error: all values must be 0 or 1. Try again.")
                    continue
                inputs = tuple(values[:n])
                output = values[n]
                rows.append((inputs, output))
                break
            except ValueError:
                print("    Error: enter only 0 or 1. Try again.")
    return rows


def parse_truth_table_from_string(n: int, table_str: str) -> list[tuple[tuple[int, ...], int]]:
    rows: list[tuple[tuple[int, ...], int]] = []
    for line_no, line in enumerate(table_str.strip().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        if len(parts) != n + 1:
            raise ValueError(f"Line {line_no}: expected {n + 1} values, got {len(parts)}")
        values = [int(p) for p in parts]
        if any(v not in (0, 1) for v in values):
            raise ValueError(f"Line {line_no}: all values must be 0 or 1")
        inputs = tuple(values[:n])
        output = values[n]
        rows.append((inputs, output))
    return rows


def validate_truth_table(n: int, rows: list[tuple[tuple[int, ...], int]]) -> None:
    expected = 2 ** n

    if len(rows) != expected:
        raise ValueError(
            f"Truth table must have exactly {expected} rows for {n} variables "
            f"(got {len(rows)})."
        )

    inputs_seen: set[tuple[int, ...]] = set()
    for inputs, output in rows:
        if inputs in inputs_seen:
            raise ValueError(f"Duplicate input combination: {inputs}")
        inputs_seen.add(inputs)

    all_combos = set(itertools.product((0, 1), repeat=n))
    missing = all_combos - inputs_seen
    if missing:
        raise ValueError(f"Missing input combinations: {missing}")

    for inputs, output in rows:
        if output not in (0, 1):
            raise ValueError(f"Invalid output value {output} for input {inputs}")


def sort_truth_table(rows: list[tuple[tuple[int, ...], int]]) -> list[tuple[tuple[int, ...], int]]:
    return sorted(rows, key=lambda r: r[0])


def row_to_minterm_index(inputs: tuple[int, ...]) -> int:
    val = 0
    for bit in inputs:
        val = (val << 1) | bit
    return val


def get_minterms(rows: list[tuple[tuple[int, ...], int]]) -> list[int]:
    return sorted(row_to_minterm_index(inp) for inp, out in rows if out == 1)


def get_maxterms(rows: list[tuple[tuple[int, ...], int]]) -> list[int]:
    return sorted(row_to_minterm_index(inp) for inp, out in rows if out == 0)


def canonical_sop(n: int, rows: list[tuple[tuple[int, ...], int]]) -> str:

    var_names = get_variable_names(n)
    minterms = get_minterms(rows)

    if not minterms:
        return "0"
    if len(minterms) == 2 ** n:
        return "1"

    terms = []
    sorted_rows = sort_truth_table(rows)
    for inputs, output in sorted_rows:
        if output == 1:
            literals = []
            for i, bit in enumerate(inputs):
                if bit == 1:
                    literals.append(var_names[i])
                else:
                    literals.append(f"{var_names[i]}'")
            terms.append("".join(literals))
    return " + ".join(terms)


def canonical_pos(n: int, rows: list[tuple[tuple[int, ...], int]]) -> str:
    var_names = get_variable_names(n)
    maxterms = get_maxterms(rows)

    if not maxterms:
        return "1"
    if len(maxterms) == 2 ** n:
        return "0"

    terms = []
    sorted_rows = sort_truth_table(rows)
    for inputs, output in sorted_rows:
        if output == 0:
            literals = []
            for i, bit in enumerate(inputs):
                if bit == 0:
                    literals.append(var_names[i])
                else:
                    literals.append(f"{var_names[i]}'")
            terms.append("(" + " + ".join(literals) + ")")
    return "".join(terms)


GRAY2 = [0, 1, 3, 2]   # 00, 01, 11, 10
GRAY1 = [0, 1]          # 0, 1


def build_kmap(n: int, rows: list[tuple[tuple[int, ...], int]]) -> dict:
    sorted_rows = sort_truth_table(rows)
    output_map = {inp: out for inp, out in sorted_rows}
    var_names = get_variable_names(n)

    if n == 2:
        row_vars = [var_names[0]]
        col_vars = [var_names[1]]
        row_gray = GRAY1
        col_gray = GRAY1
    elif n == 3:
        row_vars = [var_names[0]]
        col_vars = [var_names[1], var_names[2]]
        row_gray = GRAY1
        col_gray = GRAY2
    elif n == 4:
        row_vars = [var_names[0], var_names[1]]
        col_vars = [var_names[2], var_names[3]]
        row_gray = GRAY2
        col_gray = GRAY2
    else:
        return {}

    grid = []
    row_labels = []
    col_labels = []

    for rg in row_gray:
        row_bits = tuple(int(b) for b in format(rg, f'0{len(row_vars)}b'))
        row_labels.append("".join(str(b) for b in row_bits))
        grid_row = []
        for cg in col_gray:
            col_bits = tuple(int(b) for b in format(cg, f'0{len(col_vars)}b'))
            full_input = row_bits + col_bits
            grid_row.append(output_map[full_input])
        grid.append(grid_row)

    for cg in col_gray:
        col_bits = tuple(int(b) for b in format(cg, f'0{len(col_vars)}b'))
        col_labels.append("".join(str(b) for b in col_bits))

    return {
        'grid': grid,
        'row_vars': row_vars,
        'col_vars': col_vars,
        'row_labels': row_labels,
        'col_labels': col_labels,
        'row_gray': row_gray,
        'col_gray': col_gray,
    }


def format_kmap(kmap: dict) -> str:
    #Format K-Map as a printable string
    if not kmap:
        return "  (K-Map display is available for 2-4 variables only)"

    row_vars_str = "".join(kmap['row_vars'])
    col_vars_str = "".join(kmap['col_vars'])
    header_label = f"{row_vars_str}\\{col_vars_str}"

    col_labels = kmap['col_labels']
    row_labels = kmap['row_labels']
    grid = kmap['grid']

    col_w = max(len(cl) for cl in col_labels)
    row_w = max(len(header_label), max(len(rl) for rl in row_labels))

    lines = []
    header = f"  {header_label:>{row_w}}  " + "  ".join(f"{cl:>{col_w}}" for cl in col_labels)
    lines.append(header)
    lines.append("  " + "-" * (len(header) - 2))

    for i, rl in enumerate(row_labels):
        row_str = f"  {rl:>{row_w}}  " + "  ".join(f"{grid[i][j]:>{col_w}}" for j in range(len(col_labels)))
        lines.append(row_str)

    return "\n".join(lines)


def count_ones(x: int) -> int:
    c = 0
    while x:
        c += x & 1
        x >>= 1
    return c


def combine_implicants(a: tuple[int, ...], b: tuple[int, ...], n: int) -> Optional[tuple[int, ...]]:
    diff_pos = -1
    for i in range(n):
        if a[i] != b[i]:
            if diff_pos != -1:
                return None
            diff_pos = i
    if diff_pos == -1:
        return None
    result = list(a)
    result[diff_pos] = -1
    return tuple(result)


def implicant_covers(impl: tuple[int, ...], minterm_bits: tuple[int, ...]) -> bool:
    for i in range(len(impl)):
        if impl[i] != -1 and impl[i] != minterm_bits[i]:
            return False
    return True


def minterm_to_bits(m: int, n: int) -> tuple[int, ...]:
    return tuple(int(b) for b in format(m, f'0{n}b'))


def quine_mccluskey(n: int, minterms: list[int]) -> list[tuple[int, ...]]:
    if not minterms:
        return []

    current = set()
    for m in minterms:
        bits = minterm_to_bits(m, n)
        current.add(bits)

    all_prime = set()

    while current:
        groups: dict[int, set[tuple[int, ...]]] = {}
        for impl in current:
            ones = sum(1 for x in impl if x == 1)
            groups.setdefault(ones, set()).add(impl)

        next_gen = set()
        used = set()

        sorted_keys = sorted(groups.keys())
        for i in range(len(sorted_keys) - 1):
            k1 = sorted_keys[i]
            k2 = sorted_keys[i + 1]
            if k2 - k1 != 1:
                continue
            for a in groups[k1]:
                for b in groups[k2]:
                    combined = combine_implicants(a, b, n)
                    if combined is not None:
                        next_gen.add(combined)
                        used.add(a)
                        used.add(b)

        for impl in current:
            if impl not in used:
                all_prime.add(impl)

        current = next_gen

    return list(all_prime)


def essential_prime_implicants(
    n: int,
    minterms: list[int],
    primes: list[tuple[int, ...]]
) -> list[tuple[int, ...]]:

    if not minterms or not primes:
        return []

    minterm_bits = {m: minterm_to_bits(m, n) for m in minterms}

    coverage: dict[int, list[int]] = {m: [] for m in minterms}
    for pi, prime in enumerate(primes):
        for m in minterms:
            if implicant_covers(prime, minterm_bits[m]):
                coverage[m].append(pi)

    selected: set[int] = set()
    uncovered = set(minterms)

    for m in list(uncovered):
        if len(coverage[m]) == 1:
            pi = coverage[m][0]
            if pi not in selected:
                selected.add(pi)
                to_remove = set()
                for um in uncovered:
                    if implicant_covers(primes[pi], minterm_bits[um]):
                        to_remove.add(um)
                uncovered -= to_remove

    while uncovered:
        best_pi = -1
        best_count = 0
        for pi, prime in enumerate(primes):
            if pi in selected:
                continue
            count = sum(1 for m in uncovered if implicant_covers(prime, minterm_bits[m]))
            if count > best_count:
                best_count = count
                best_pi = pi
        if best_pi == -1:
            break
        selected.add(best_pi)
        to_remove = set()
        for m in uncovered:
            if implicant_covers(primes[best_pi], minterm_bits[m]):
                to_remove.add(m)
        uncovered -= to_remove

    return [primes[pi] for pi in sorted(selected)]


def implicant_to_sop_term(impl: tuple[int, ...], var_names: list[str]) -> str:
    literals = []
    for i, val in enumerate(impl):
        if val == 1:
            literals.append(var_names[i])
        elif val == 0:
            literals.append(f"{var_names[i]}'")
    if not literals:
        return "1"
    return "".join(literals)


def implicant_to_pos_term(impl: tuple[int, ...], var_names: list[str]) -> str:
    literals = []
    for i, val in enumerate(impl):
        if val == 0:
            literals.append(var_names[i])
        elif val == 1:
            literals.append(f"{var_names[i]}'")
    if not literals:
        return "0"
    return "(" + " + ".join(literals) + ")"


def simplify_sop(n: int, rows: list[tuple[tuple[int, ...], int]]) -> tuple[str, list[tuple[int, ...]]]:

    minterms = get_minterms(rows)
    var_names = get_variable_names(n)

    if not minterms:
        return "0", []
    if len(minterms) == 2 ** n:
        return "1", []

    primes = quine_mccluskey(n, minterms)
    essentials = essential_prime_implicants(n, minterms, primes)

    terms = [implicant_to_sop_term(e, var_names) for e in essentials]
    expr = " + ".join(terms) if terms else "0"
    return expr, essentials


def simplify_pos(n: int, rows: list[tuple[tuple[int, ...], int]]) -> tuple[str, list[tuple[int, ...]]]:
    maxterms = get_maxterms(rows)
    var_names = get_variable_names(n)

    if not maxterms:
        return "1", []
    if len(maxterms) == 2 ** n:
        return "0", []

    primes = quine_mccluskey(n, maxterms)
    essentials = essential_prime_implicants(n, maxterms, primes)

    terms = [implicant_to_pos_term(e, var_names) for e in essentials]
    expr = "".join(terms) if terms else "1"
    return expr, essentials


def describe_kmap_groups(
    n: int,
    essentials: list[tuple[int, ...]],
    minterms: list[int],
    var_names: list[str],
    form: str
) -> str:
    #Describe K-Map grouping in human-readable format
    if n < 2 or n > 4:
        return "  (K-Map grouping shown for 2-4 variables only)"

    lines = []
    for i, impl in enumerate(essentials):
        covered = []
        for m in minterms:
            bits = minterm_to_bits(m, n)
            if implicant_covers(impl, bits):
                covered.append(m)

        size = 2 ** sum(1 for v in impl if v == -1)
        if form == "SOP":
            term = implicant_to_sop_term(impl, var_names)
            term_type = "minterms"
        else:
            term = implicant_to_pos_term(impl, var_names)
            term_type = "maxterms"

        lines.append(
            f"  Group {i + 1}: {term}  "
            f"(size {size}, covers {term_type} {covered})"
        )
    return "\n".join(lines) if lines else "  No groups (constant function)"


def evaluate_implicant(impl: tuple[int, ...], inputs: tuple[int, ...]) -> bool:
    for i, val in enumerate(impl):
        if val == -1:
            continue
        if val != inputs[i]:
            return False
    return True


def evaluate_simplified_sop(
    essentials: list[tuple[int, ...]],
    inputs: tuple[int, ...],
    is_constant: Optional[int] = None
) -> int:
    if is_constant is not None:
        return is_constant
    if not essentials:
        return 0
    for impl in essentials:
        if evaluate_implicant(impl, inputs):
            return 1
    return 0


def evaluate_simplified_pos(
    essentials: list[tuple[int, ...]],
    inputs: tuple[int, ...],
    is_constant: Optional[int] = None
) -> int:
    if is_constant is not None:
        return is_constant
    if not essentials:
        return 1
    for impl in essentials:
        if evaluate_implicant(impl, inputs):
            return 0
    return 1


def validate_simplification(
    n: int,
    rows: list[tuple[tuple[int, ...], int]],
    essentials: list[tuple[int, ...]],
    form: str,
    simplified_expr: str = ""
) -> tuple[bool, list[tuple[tuple[int, ...], int, int]]]:
    sorted_rows = sort_truth_table(rows)
    mismatches = []

    is_constant = None
    if simplified_expr == "0":
        is_constant = 0
    elif simplified_expr == "1":
        is_constant = 1

    for inputs, expected in sorted_rows:
        if form == "SOP":
            actual = evaluate_simplified_sop(essentials, inputs, is_constant)
        else:
            actual = evaluate_simplified_pos(essentials, inputs, is_constant)

        if actual != expected:
            mismatches.append((inputs, expected, actual))

    return (len(mismatches) == 0, mismatches)


def display_truth_table(n: int, rows: list[tuple[tuple[int, ...], int]]) -> str:
    var_names = get_variable_names(n)
    sorted_rows = sort_truth_table(rows)

    header = "  " + " | ".join(var_names) + " | F"
    sep = "  " + "-" * len(header.strip())
    lines = [header, sep]
    for inputs, output in sorted_rows:
        row_str = "  " + " | ".join(str(b) for b in inputs) + " | " + str(output)
        lines.append(row_str)
    return "\n".join(lines)


def display_full_output(
    n: int,
    rows: list[tuple[tuple[int, ...], int]],
    form: str
) -> None:
    var_names = get_variable_names(n)
    sorted_rows = sort_truth_table(rows)

    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)

    print("\n1. Truth Table:")
    print(display_truth_table(n, sorted_rows))

    minterms = get_minterms(sorted_rows)
    maxterms = get_maxterms(sorted_rows)

    if form == "SOP":
        canon = canonical_sop(n, sorted_rows)
        print(f"\n2. Canonical SOP Expression:")
        print(f"  F = {canon}")
        print(f"\n3. Minterms: m({', '.join(str(m) for m in minterms)})")
        simplified, essentials = simplify_sop(n, sorted_rows)
        relevant_terms = minterms
    else:
        canon = canonical_pos(n, sorted_rows)
        print(f"\n2. Canonical POS Expression:")
        print(f"  F = {canon}")
        print(f"\n3. Maxterms: M({', '.join(str(m) for m in maxterms)})")
        simplified, essentials = simplify_pos(n, sorted_rows)
        relevant_terms = maxterms

    print(f"\n4. K-Map:")
    if 2 <= n <= 4:
        kmap = build_kmap(n, sorted_rows)
        print(format_kmap(kmap))
        print(f"\n  K-Map Grouping:")
        print(describe_kmap_groups(n, essentials, relevant_terms, var_names, form))
    else:
        print(f"  (K-Map display for 2-4 variables; n={n} uses algebraic simplification)")

    print(f"\n5. Simplified Boolean Expression ({form}):")
    print(f"  F = {simplified}")

    passed, mismatches = validate_simplification(n, sorted_rows, essentials, form, simplified)
    print(f"\n6. Validation: {'PASS' if passed else 'FAIL'}")
    if not passed:
        print(f"  Mismatches found ({len(mismatches)}):")
        for inputs, expected, actual in mismatches:
            print(f"    Input {inputs}: expected {expected}, got {actual}")

    print("\n" + "=" * 60)


def main():
    print("=" * 60)
    print("  Task 2")
    print("=" * 60)

    while True:
        try:
            n = int(input("\nEnter number of input variables (n >= 2): ").strip())
            if n < 2:
                print("  Error: n must be >= 2.")
                continue
            break
        except ValueError:
            print("  Error: enter a valid integer.")

    print(f"\n  Variables: {', '.join(get_variable_names(n))}")
    print(f"  Truth table will have {2 ** n} rows.")

    print("\nInput method:")
    print("  1) Interactive (enter row by row)")
    print("  2) Paste all rows at once")
    choice = input("  Choice [1/2]: ").strip()

    if choice == "2":
        print(f"\nPaste {2 ** n} rows (each: {' '.join(['0/1'] * n)} <output>), then press Enter twice:")
        lines = []
        while True:
            line = input()
            if line.strip() == "":
                break
            lines.append(line)
        table_str = "\n".join(lines)
        rows = parse_truth_table_from_string(n, table_str)
    else:
        rows = parse_truth_table_interactive(n)

    try:
        validate_truth_table(n, rows)
        print("\n  Truth table validated successfully.")
    except ValueError as e:
        print(f"\n  Validation error: {e}")
        sys.exit(1)

    print("\nSelect canonical form:")
    print("  1) SOP (Sum of Products)")
    print("  2) POS (Product of Sums)")
    form_choice = input("  Choice [1/2]: ").strip()
    form = "POS" if form_choice == "2" else "SOP"

    display_full_output(n, rows, form)


if __name__ == "__main__":
    main()
