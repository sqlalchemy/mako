# util.py
# Copyright (C) 2006, 2007, 2008 Michael Bayer mike_mp@zzzcomputing.com
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

import sys
try:
    Set = set
except:
    import sets
    Set = sets.Set

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

import weakref, os, time

try:
    import threading
    import thread
except ImportError:
    import dummy_threading as threading
    import dummy_thread as thread

if sys.platform.startswith('win') or sys.platform.startswith('java'):
    time_func = time.clock
else:
    time_func = time.time 
   
def verify_directory(dir):
    """create and/or verify a filesystem directory."""
    
    tries = 0
    
    while not os.access(dir, os.F_OK):
        try:
            tries += 1
            os.makedirs(dir, 0750)
        except:
            if tries > 5:
                raise

class SetLikeDict(dict):
    """a dictionary that has some setlike methods on it"""
    def union(self, other):
        """produce a 'union' of this dict and another (at the key level).
        
        values in the second dict take precedence over that of the first"""
        x = SetLikeDict(**self)
        x.update(other)
        return x

class FastEncodingBuffer(object):
    """a very rudimentary buffer that is faster than StringIO, but doesnt crash on unicode data like cStringIO."""
    
    def __init__(self, encoding=None, errors='strict'):
        self.data = []
        self.encoding = encoding
        self.errors = errors
    
    def write(self, text):
        self.data.append(text)
    
    def getvalue(self):
        if self.encoding:
            return u''.join(self.data).encode(self.encoding, self.errors)
        else:
            return u''.join(self.data)

class LRUCache(dict):
    """A dictionary-like object that stores a limited number of items, discarding
    lesser used items periodically.
    
    this is a rewrite of LRUCache from Myghty to use a periodic timestamp-based
    paradigm so that synchronization is not really needed.  the size management 
    is inexact.
    """
    
    class _Item(object):
        def __init__(self, key, value):
            self.key = key
            self.value = value
            self.timestamp = time_func()
        def __repr__(self):
            return repr(self.value)
    
    def __init__(self, capacity, threshold=.5):
        self.capacity = capacity
        self.threshold = threshold
    
    def __getitem__(self, key):
        item = dict.__getitem__(self, key)
        item.timestamp = time_func()
        return item.value
    
    def values(self):
        return [i.value for i in dict.values(self)]
    
    def setdefault(self, key, value):
        if key in self:
            return self[key]
        else:
            self[key] = value
            return value
    
    def __setitem__(self, key, value):
        item = dict.get(self, key)
        if item is None:
            item = self._Item(key, value)
            dict.__setitem__(self, key, item)
        else:
            item.value = value
        self._manage_size()
    
    def _manage_size(self):
        while len(self) > self.capacity + self.capacity * self.threshold:
            bytime = dict.values(self)
            bytime.sort(lambda a, b: cmp(b.timestamp, a.timestamp))
            for item in bytime[self.capacity:]:
                try:
                    del self[item.key]
                except KeyError:
                    # if we couldnt find a key, most likely some other thread broke in 
                    # on us. loop around and try again
                    break

def restore__ast(_ast):
    """Attempt to restore the required classes to the _ast module if it
    appears to be missing them
    """
    if hasattr(_ast, 'AST'):
        return
    _ast.PyCF_ONLY_AST = 2 << 9
    m = compile("""\
def foo(): pass
class Bar(object): pass
if False: pass
baz = 'mako'
1 + 2 - 3 * 4 / 5
6 // 7 % 8 << 9 >> 10
11 & 12 ^ 13 | 14
15 and 16 or 17
-baz + (not +18) - ~17
baz and 'foo' or 'bar'
(mako is baz == baz) is not baz != mako
mako > baz < mako >= baz <= mako
mako in baz not in mako""", '<unknown>', 'exec', _ast.PyCF_ONLY_AST)
    _ast.Module = type(m)

    for cls in _ast.Module.__mro__:
        if cls.__name__ == 'mod':
            _ast.mod = cls
        elif cls.__name__ == 'AST':
            _ast.AST = cls

    _ast.FunctionDef = type(m.body[0])
    _ast.ClassDef = type(m.body[1])
    _ast.If = type(m.body[2])

    _ast.Name = type(m.body[3].targets[0])
    _ast.Store = type(m.body[3].targets[0].ctx)
    _ast.Str = type(m.body[3].value)

    _ast.Sub = type(m.body[4].value.op)
    _ast.Add = type(m.body[4].value.left.op)
    _ast.Div = type(m.body[4].value.right.op)
    _ast.Mult = type(m.body[4].value.right.left.op)

    _ast.RShift = type(m.body[5].value.op)
    _ast.LShift = type(m.body[5].value.left.op)
    _ast.Mod = type(m.body[5].value.left.left.op)
    _ast.FloorDiv = type(m.body[5].value.left.left.left.op)

    _ast.BitOr = type(m.body[6].value.op)
    _ast.BitXor = type(m.body[6].value.left.op)
    _ast.BitAnd = type(m.body[6].value.left.left.op)

    _ast.Or = type(m.body[7].value.op)
    _ast.And = type(m.body[7].value.values[0].op)

    _ast.Invert = type(m.body[8].value.right.op)
    _ast.Not = type(m.body[8].value.left.right.op)
    _ast.UAdd = type(m.body[8].value.left.right.operand.op)
    _ast.USub = type(m.body[8].value.left.left.op)

    _ast.Or = type(m.body[9].value.op)
    _ast.And = type(m.body[9].value.values[0].op)

    _ast.IsNot = type(m.body[10].value.ops[0])
    _ast.NotEq = type(m.body[10].value.ops[1])
    _ast.Is = type(m.body[10].value.left.ops[0])
    _ast.Eq = type(m.body[10].value.left.ops[1])

    _ast.Gt = type(m.body[11].value.ops[0])
    _ast.Lt = type(m.body[11].value.ops[1])
    _ast.GtE = type(m.body[11].value.ops[2])
    _ast.LtE = type(m.body[11].value.ops[3])

    _ast.In = type(m.body[12].value.ops[0])
    _ast.NotIn = type(m.body[12].value.ops[1])
