# exceptions.py
# Copyright (C) 2006 Michael Bayer mike_mp@zzzcomputing.com
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

"""exception classes"""

class MakoException(Exception):
    pass

class RuntimeException(MakoException):
    pass
class CompileException(MakoException):
    def __init__(self, message, lineno, pos):
        MakoException.__init__(self, message + " at line: %d char: %d" % (lineno, pos))
        self.lineno =lineno
        self.pos = pos

                    
class SyntaxException(MakoException):
    def __init__(self, message, lineno, pos):
        MakoException.__init__(self, message + " at line: %d char: %d" % (lineno, pos))
        self.lineno =lineno
        self.pos = pos
        
class TemplateLookupException(MakoException):
    pass