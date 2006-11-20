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