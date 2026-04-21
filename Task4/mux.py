"""
Multiplexer (MUX) Module
-------------------------
Implements a 2-to-1 multiplexer used in the datapath for:
  - Selecting ALU input (normal vs inverted)
  - Any other datapath routing controlled by control signals
"""


def mux2to1(input_0: int, input_1: int, select: bool) -> int:
    """
    2-to-1 Multiplexer.

    Parameters:
        input_0: Value when select = 0 (False)
        input_1: Value when select = 1 (True)
        select:  Control signal

    Returns:
        input_1 if select is True, else input_0
    """
    return input_1 if select else input_0
