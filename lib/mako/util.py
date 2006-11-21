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

