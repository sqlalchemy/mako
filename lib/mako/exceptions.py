"""exception classes"""

class MakoException(Exception):
    pass
class CompileException(MakoException):
    pass
class SyntaxException(MakoException):
    def __init__(self, message, lineno):
        MakoException.__init__(self, message + " at line: %d" % lineno)
        self.lineno =lineno