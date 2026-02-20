
'''
Elie Wamana

Implements:
    1. A 32-bit signed decimal input parser
    2. Decimal → Binary (Two’s Complement) conversion logic
    3. Binary → Hexadecimal conversion logic
    4. Binary → Decimal conversion logic
    5. Overflow detection for out-of-range inputs
    6. Saturation logic to prevent wrap-around
    7. Configurable output format selection 
'''


from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from typing import Literal

MIN_INT32 = -(2**31)
MAX_INT32 = (2**31) - 1
MOD32 = 2**32

FormatSel = Literal["DEC", "BIN", "HEX"]


@dataclass(frozen=True)
class Result:
    value_out: str
    overflow: int
    saturated: int
    x_input: int
    x_sat: int
    bin32: str
    hex8: str


_DEC_PATTERN = re.compile(r"^[+-]?\d+$")


def parse_decimal_signed(s: str) -> int:
    """
    Parse a decimal signed integer string into a Python int.
    """
    if s is None:
        raise ValueError("Missing input value.")
    s = s.strip()
    if not s:
        raise ValueError("Empty input value.")
    if not _DEC_PATTERN.match(s):
        raise ValueError(f"Invalid decimal integer: {s!r}")
    return int(s, 10)


def detect_overflow(x: int) -> int:
    return 1 if (x < MIN_INT32 or x > MAX_INT32) else 0


def saturate_int32(x: int) -> tuple[int, int]:
    """
    Saturate/clamp x into signed 32-bit range.
    """
    if x > MAX_INT32:
        return MAX_INT32, 1
    if x < MIN_INT32:
        return MIN_INT32, 1
    return x, 0


def int32_to_bin32(x_sat: int) -> str:
    """
    Convert a signed 32-bit int into its 32-bit two's complement binary string.
    Must be exactly 32 bits.
    """
    # Map to unsigned 32-bit pattern
    u = x_sat if x_sat >= 0 else (MOD32 + x_sat)
    return format(u, "032b")


def bin32_to_hex8(bin32: str, prefix_0x: bool = False) -> str:
    """
    Convert a 32-bit binary string to an 8-digit hexadecimal string.
    """
    if len(bin32) != 32 or any(c not in "01" for c in bin32):
        raise ValueError("bin32 must be a 32-character string of 0/1.")
    u = int(bin32, 2)
    hx = format(u, "08X")  # 8 digits, uppercase
    return ("0x" + hx) if prefix_0x else hx


def bin32_to_int32(bin32: str) -> int:
    """
    Interpret a 32-bit binary string as a signed two's complement integer.
    """
    if len(bin32) != 32 or any(c not in "01" for c in bin32):
        raise ValueError("bin32 must be a 32-character string of 0/1.")
    u = int(bin32, 2)
    # If sign bit is 1, it's negative: x = u - 2^32
    return u if bin32[0] == "0" else (u - MOD32)


def convert(x_str: str, fmt: FormatSel, hex_prefix: bool = False) -> Result:

    x = parse_decimal_signed(x_str)

    overflow = detect_overflow(x)
    x_sat, saturated = saturate_int32(x)

    bin32 = int32_to_bin32(x_sat)
    hex8 = bin32_to_hex8(bin32, prefix_0x=hex_prefix)

    if fmt == "DEC":
        value_out = str(x_sat)
    elif fmt == "BIN":
        value_out = bin32
    elif fmt == "HEX":
        value_out = hex8
    else:
        raise ValueError(f"Unknown format selector: {fmt!r}")

    return Result(
        value_out=value_out,
        overflow=overflow,
        saturated=saturated,
        x_input=x,
        x_sat=x_sat,
        bin32=bin32,
        hex8=hex8,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Data Systems — 32-bit signed conversions with overflow + saturation."
    )
    parser.add_argument("x", help='Decimal signed integer input (e.g., "123", "-45", "0")')
    parser.add_argument("fmt", help="Output format selector: DEC, BIN, or HEX")
    parser.add_argument(
        "--hex-prefix",
        action="store_true",
        help="If set, HEX output will include 0x prefix (e.g., 0xFFFFFFF4).",
    )

    args = parser.parse_args()

    fmt_upper = args.fmt.strip().upper()
    if fmt_upper not in {"DEC", "BIN", "HEX"}:
        raise SystemExit('Format must be one of: DEC, BIN, HEX')

    res = convert(args.x, fmt_upper, hex_prefix=args.hex_prefix)

    print(res.value_out)
    print(f"overflow={res.overflow}")
    print(f"saturated={res.saturated}")


if __name__ == "__main__":
    main()