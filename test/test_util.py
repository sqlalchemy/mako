# -*- coding: utf-8 -*-

import unittest
from mako import util
from test import eq_

class UtilTest(unittest.TestCase):
    def test_fast_buffer_write(self):
        buf = util.FastEncodingBuffer()
        buf.write("string a ")
        buf.write("string b")
        eq_(buf.getvalue(), "string a string b")

    def test_fast_buffer_truncate(self):
        buf = util.FastEncodingBuffer()
        buf.write("string a ")
        buf.write("string b")
        buf.truncate()
        buf.write("string c ")
        buf.write("string d")
        eq_(buf.getvalue(), "string c string d")

    def test_fast_buffer_encoded(self):
        s = u"drôl m’a rée « S’il"
        buf = util.FastEncodingBuffer(encoding='utf-8')
        buf.write(s[0:10])
        buf.write(s[10:])
        q = buf.getvalue()
        eq_(buf.getvalue(), s.encode('utf-8'))