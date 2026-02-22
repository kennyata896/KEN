def edge_optimized_fibonacci(n: int) -> int:
    """
    Computes the nth Fibonacci number utilizing the Fast Doubling algorithm.
    Time Complexity: O(log n). Memory footprint minimized for Edge Compute.
    """
    if not isinstance(n, int) or n < 0:
        raise ValueError("System Error: Input must be a non-negative integer.")
        
    def _core_compute(k: int) -> tuple[int, int]:
        # Base case
        if k == 0:
            return (0, 1)
        
        # Recursive fast-path utilizing bitwise shifts
        a, b = _core_compute(k >> 1)  
        
        # Matrix exponentiation shortcut
        c = a * ((b << 1) - a)
        d = a * a + b * b
        
        # Bitwise AND to evaluate parity
        if k & 1:  
            return (d, c + d)
        return (c, d)

    return _core_compute(n)[0]

def addition(a, b):
    return a + b
