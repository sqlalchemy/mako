# util.py
# Copyright (C) 2006 Michael Bayer mike_mp@zzzcomputing.com
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

import weakref, os

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

class ThreadLocalRegistry(object):
    """a registry that stores instances keyed to the current thread.  if a requested
    instance does not exist for a particular thread, it is created by a creation function.
    """
    def __init__(self, createfunc):
        self.__createfunc = createfunc
        self.__scopefunc = thread.get_ident
        self.__registry = {}
    def __call__(self):
        key = self.__scopefunc()
        try:
            return self.__registry[key]
        except KeyError:
            return self.__registry.setdefault(key, self.__createfunc())
    def set(self, obj):
        self.registry[self.__scopefunc()] = obj
    def clear(self):
        try:
            del self.registry[self.__scopefunc()]
        except KeyError:
            pass

class LRUCache(dict):
    """A dictionary-like object that stores only a certain number of items, and
    discards its least recently used item when full.

    this is Chris Lenz' cleanup of Mike Bayer's version from Myghty.
    """

    class _Item(object):
        def __init__(self, key, value):
            self.previous = self.next = None
            self.key = key
            self.value = value
        def __repr__(self):
            return repr(self.value)

    def __init__(self, capacity):
        self._dict = dict()
        self.capacity = capacity
        self.head = None
        self.tail = None

    def __contains__(self, key):
        return key in self._dict

    def __iter__(self):
        cur = self.head
        while cur:
            yield cur.key
            cur = cur.next

    def __len__(self):
        return len(self._dict)

    def __getitem__(self, key):
        item = self._dict[key]
        self._update_item(item)
        return item.value

    def __setitem__(self, key, value):
        item = self._dict.get(key)
        if item is None:
            item = self._Item(key, value)
            self._dict[key] = item
            self._insert_item(item)
        else:
            item.value = value
            self._update_item(item)
            self._manage_size()

    def __repr__(self):
        return repr(self._dict)

    def _insert_item(self, item):
        item.previous = None
        item.next = self.head
        if self.head is not None:
            self.head.previous = item
        else:
            self.tail = item
        self.head = item
        self._manage_size()

    def _manage_size(self):
        while len(self._dict) > self.capacity:
            olditem = self._dict[self.tail.key]
            del self._dict[self.tail.key]
            if self.tail != self.head:
                self.tail = self.tail.previous
                self.tail.next = None
            else:
                self.head = self.tail = None

    def _update_item(self, item):
        if self.head == item:
            return

        previous = item.previous
        previous.next = item.next
        if item.next is not None:
            item.next.previous = previous
        else:
            self.tail = previous

        item.previous = None
        item.next = self.head
        self.head.previous = self.head = item
