# Multi-precision Helpers
def to_mp(x, limbs, wbw):
    """Convert int -> fixed-length list of limbs (LSB first)."""
    words = []
    word_mask = (1 << wbw) - 1
    
    for _ in range(limbs):
        words.append(x & word_mask)
        x >>= wbw
    return words

def from_mp(mp_x, limbs, wbw):
    """Convert list of limbs (LSB first) -> int."""
    val = 0
    for i in reversed(range(limbs)):
        val <<= wbw
        val |= mp_x[i]
    return val