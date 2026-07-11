import heapq
import math
import collections
from node import Node

def build_huffman(freqs):
    """
    Assembles a minimum priority queue heap structure to output 
    the root node of an optimal prefix code sequence.
    """
    heap = [Node(f, v) for v, f in freqs.items()]
    heapq.heapify(heap)
    
    if len(heap) == 1:
        leaf = heap[0]
        return Node(leaf.freq, left=leaf)
        
    while len(heap) > 1:
        a = heapq.heappop(heap)
        b = heapq.heappop(heap)
        parent = Node(a.freq + b.freq, left=a, right=b)
        heapq.heappush(heap, parent)
        
    return heap[0]

def gen_codes(node, prefix='', codes=None):
    if codes is None:
        codes = {}
    if node.is_leaf():
        codes[node.val] = prefix or '0'
        return codes
    if node.left:
        gen_codes(node.left, prefix + '0', codes)
    if node.right:
        gen_codes(node.right, prefix + '1', codes)
    return codes

def encode_bytes(data, codes):
    bits = ''.join(codes[b] for b in data)
    pad = (8 - len(bits) % 8) % 8
    padded = bits + '0' * pad
    out = bytearray(int(padded[i:i + 8], 2) for i in range(0, len(padded), 8))
    return bytes(out), pad, bits

def decode_bits(bits, root):
    out = bytearray()
    node = root
    for bit in bits:
        node = node.left if bit == '0' else node.right
        if node.is_leaf():
            out.append(node.val)
            node = root
    return bytes(out)

def shannon_entropy(data):
    if not data:
        return 0.0
    n = len(data)
    freqs = collections.Counter(data)
    return -sum((c / n) * math.log2(c / n) for c in freqs.values())

def bit_entropy(bits):
    n = len(bits)
    if n == 0:
        return 0.0
    c0 = bits.count('0')
    c1 = n - c0
    return -sum((c / n) * math.log2(c / n) for c in (c0, c1) if c > 0)

# =====================================================================
# AUTOMATED UNIT TESTS FOR HUFFMAN ENCODING/DECODING
# =====================================================================

def test_frequency_table():
    """Test that the frequency map is generated correctly using collections.Counter."""
    print("Running: test_frequency_table...")
    
    # Input data as bytes
    text1 = b"BABAAB"
    freq_table1 = collections.Counter(text1) 
    assert freq_table1.get(b'A'[0]) == 3, f"Expected 3 'A's, got {freq_table1.get(b'A'[0])}"
    assert freq_table1.get(b'B'[0]) == 3, f"Expected 3 'B's, got {freq_table1.get(b'B'[0])}"

    text2 = b"hello"
    freq_table2 = collections.Counter(text2)
    assert freq_table2.get(b'l'[0]) == 2, f"Expected 2 'l's, got {freq_table2.get(b'l'[0])}"
    assert freq_table2.get(b'o'[0]) == 1, f"Expected 1 'o', got {freq_table2.get(b'o'[0])}"
    
    print("✓ test_frequency_table passed!")


def test_encode_decode_round_trip():
    """Test that encoding then decoding a string yields the identical original data."""
    print("Running: test_encode_decode_round_trip...")
    
    test_cases = [
        b"hello huffman",
        b"A",
        b"BABAAB",
        b"The quick brown fox jumps over the lazy dog.",
        b"12345678900000----!!!!"
    ]
    
    for idx, original_bytes in enumerate(test_cases):
        # 1. Build frequency counter and tree structure
        freq_table = collections.Counter(original_bytes)
        tree = build_huffman(freq_table)
        codes = gen_codes(tree)
        
        # 2. Encode the original message data
        _, _, bits = encode_bytes(original_bytes, codes)
        
        # 3. Decode back to bytes using the pure bit string representation
        decoded_bytes = decode_bits(bits, tree)
        
        # 4. Assert exact parity
        assert original_bytes == decoded_bytes, (
            f"Round-trip failed for case {idx}!\n"
            f"Original: {original_bytes}\n"
            f"Decoded:  {decoded_bytes}"
        )
        
    print(f"✓ All {len(test_cases)} encode/decode round-trips passed!")


if __name__ == "__main__":
    print("Starting automated verification tests...")
    print("-" * 45)
    try:
        test_frequency_table()
        test_encode_decode_round_trip()
        print("-" * 45)
        print("ALL TESTS PASSED SUCCESSFULLY 🎉")
    except AssertionError as e:
        print("-" * 45)
        print(f"❌ TEST FAILED: {e}")