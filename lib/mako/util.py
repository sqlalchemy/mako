# util.py
# Copyright (C) 2006, 2007 Michael Bayer mike_mp@zzzcomputing.com
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

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
    def __init__(self, encoding=None):
        self.data = []
        self.encoding = encoding
    def write(self, text):
        self.data.append(text)
    def getvalue(self):
        if self.encoding:
            return u''.join(self.data).encode(self.encoding)
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
            self.timestamp = time.time()
        def __repr__(self):
            return repr(self.value)

    def __init__(self, capacity, threshold=.5):
        self.capacity = capacity
        self.threshold = threshold

    def __getitem__(self, key):
        item = dict.__getitem__(self, key)
        item.timestamp = time.time()
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
