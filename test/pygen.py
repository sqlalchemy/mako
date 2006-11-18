import unittest

from mako.pygen import PythonPrinter, adjust_whitespace
from StringIO import StringIO

class GeneratePythonTest(unittest.TestCase):
    def test_generate_normal(self):
        stream = StringIO()
        printer = PythonPrinter(stream)
        printer.print_python_line("import lala")
        printer.print_python_line("for x in foo:")
        printer.print_python_line("print x")
        printer.print_python_line(None)
        printer.print_python_line("print y")
        assert stream.getvalue() == \
"""import lala
for x in foo:
    print x
print y
"""
    def test_generate_adjusted(self):
        block = """
        x = 5 +6
        if x > 7:
            for y in range(1,5):
                print "<td>%s</td>" % y
"""
        stream = StringIO()
        printer = PythonPrinter(stream)
        printer.print_adjusted_line(block)
        printer.close()
        #print stream.getvalue()
        assert stream.getvalue() == \
"""
x = 5 +6
if x > 7:
    for y in range(1,5):
        print "<td>%s</td>" % y

"""
    def test_generate_combo(self):
        block = \
"""
                x = 5 +6
                if x > 7:
                    for y in range(1,5):
                        print "<td>%s</td>" % y
                    print "hi"
                print "there"
                foo(lala)
        """
        stream = StringIO()
        printer = PythonPrinter(stream)
        printer.print_python_line("import lala")
        printer.print_python_line("for x in foo:")
        printer.print_python_line("print x")
        printer.print_adjusted_line(block)
        printer.print_python_line(None)
        printer.print_python_line("print y")
        printer.close()
        #print "->" + stream.getvalue().replace(' ', '#') + "<-"
        assert stream.getvalue() == \
"""import lala
for x in foo:
    print x

    x = 5 +6
    if x > 7:
        for y in range(1,5):
            print "<td>%s</td>" % y
        print "hi"
    print "there"
    foo(lala)
        
print y
"""
    def test_multi_line(self):
        block = \
"""
    if test:
        print ''' this is a block of stuff.
this is more stuff in the block.
and more block.
'''
        do_more_stuff(g)
"""
        stream = StringIO()
        printer = PythonPrinter(stream)
        printer.print_adjusted_line(block)
        printer.close()
        #print stream.getvalue()
        assert stream.getvalue() == \
"""
if test:
    print ''' this is a block of stuff.
this is more stuff in the block.
and more block.
'''
    do_more_stuff(g)

"""

    def test_backslash_line(self):
        block = \
"""
            # comment
    if test:
        if (lala + hoho) + \\
(foobar + blat) == 5:
            print "hi"
    print "more indent"
"""
        stream = StringIO()
        printer = PythonPrinter(stream)
        printer.print_adjusted_line(block)
        printer.close()
        assert stream.getvalue() == \
"""
            # comment
if test:
    if (lala + hoho) + \\
(foobar + blat) == 5:
        print "hi"
print "more indent"

"""

class WhitespaceTest(unittest.TestCase):
    def test_basic(self):
        text = """
        for x in range(0,15):
            print x
        print "hi"
        """
        assert adjust_whitespace(text) == \
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
        assert adjust_whitespace(text) == \
"""
print ''' aslkjfnas kjdfn
askdjfnaskfd fkasnf dknf sadkfjn asdkfjna sdakjn
asdkfjnads kfajns '''
if x:
    print y

"""

if __name__ == '__main__':
    unittest.main()
