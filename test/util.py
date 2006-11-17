import unittest

from mako import util

class WhitespaceTest(unittest.TestCase):
    def test_basic(self):
        text = """
        for x in range(0,15):
            print x
        print "hi"
        """
        assert util.adjust_whitespace(text) == \
"""
for x in range(0,15):
    print x
print "hi"

"""

    def test_quotes(self):
        text = """
        print ''' aslkjfnas kjdfn
askdjfnaskfd fkasnf dknf sadkfjn asdkfjna sdakjn
asdkfjnads kfajns '''
        if x:
            print y
"""
        assert util.adjust_whitespace(text) == \
"""
print ''' aslkjfnas kjdfn
askdjfnaskfd fkasnf dknf sadkfjn asdkfjna sdakjn
asdkfjnads kfajns '''
if x:
    print y

"""
if __name__ == '__main__':
    unittest.main()
