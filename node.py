class Node:
    """
    Highly optimized data architecture wrapping structural, geometric, 
    and topological metadata for binary prefix-code tree generation.
    """
    __slots__ = ('freq', 'val', 'left', 'right', 'x', 'y', 'depth', 'oid', 'path')
    
    def __init__(self, freq, val=None, left=None, right=None):
        self.freq = freq
        self.val = val
        self.left = left
        self.right = right
        self.x = 0
        self.y = 0
        self.depth = 0
        self.oid = None
        self.path = ''

    def __lt__(self, other):
        return self.freq < other.freq

    def is_leaf(self):
        return self.left is None and self.right is None