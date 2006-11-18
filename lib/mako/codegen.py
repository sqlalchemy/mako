from StringIO import StringIO
from mako.pygen import PythonPrinter
from mako import util, ast

class Compiler(object):
    def __init__(self, node):
        self.node = node
    def render(self):
        module_code = []
        class FindPyDecls(object):
            def visitCode(self, node):
                if node.ismodule:
                    module_code.append(node)
        f = FindPyDecls()
        self.node.accept_visitor(f)
        
        components = []
        class FindTopLevelComponents(object):
            def visitComponentTag(self, node):
                components.append(node)
        self.node.accept_visitor(FindTopLevelComponents())
        
        declared = util.Set()
        undeclared = util.Set()
        def check_declared(node):
            for ident in node.declared_identifiers():
                declared.add(ident)
            for ident in node.undeclared_identifiers():
                if ident not in declared:
                    undeclared.add(ident)

        buf = StringIO()
        printer = PythonPrinter(buf)
        for n in module_code:
            check_declared(n)
            printer.writeline("# SOURCE LINE %d" % n.lineno, is_comment=True)
            printer.write_indented_block(n.text)
        
        class FindUndeclared(object):
            def visitExpression(self, node):
                check_declared(node)
            def visitControlLine(self, node):
                check_declared(node)
            def visitCode(self, node):
                if not node.ismodule:
                    check_declared(node)
            def visitComponentTag(self, node):
                check_declared(node)
            def visitIncludeTag(self, node):
                # TODO: expressions for attributes
                pass        
            def visitNamespaceTag(self, node):
                # TODO: expressions for attributes
                pass
        self.node.accept_visitor(FindUndeclared())        
        self.node.accept_visitor(GenerateRenderMethod(printer, undeclared))
        return buf.getvalue()

class GenerateRenderMethod(object):
    def __init__(self, printer, undeclared, name='render', in_component=False):
        self.printer = printer
        self.in_component = in_component
        self.last_source_line = -1
        printer.writeline("def %s(context):" % name)
        for ident in undeclared:
            printer.writeline("%s = context.get(%s, None)" % (ident, repr(ident)))
    def writeSourceComment(self, node):
        if self.last_source_line != node.lineno:
            self.printer.writeline("# SOURCE LINE %d" % node.lineno, is_comment=True)
            self.last_source_line = node.lineno
    def visitExpression(self, node):
        self.writeSourceComment(node)
        self.printer.writeline("context.write(%s)" % node.text)
    def visitControlLine(self, node):
        if node.isend:
            self.printer.writeline(None)
        else:
            self.writeSourceComment(node)
            self.printer.writeline(node.text)
    def visitText(self, node):
        self.writeSourceComment(node)
        self.printer.writeline("context.write(%s)" % repr(node.content))
    def visitCode(self, node):
        if not node.ismodule:
            self.writeSourceComment(node)
            self.printer.write_indented_block(node.text)
    def visitIncludeTag(self, node):
        self.writeSourceComment(node)
        self.printer.writeline("context.include_file(%s, import=%s)" % (repr(node.attributes['file']), repr(node.attributes.get('import', False))))
    def visitNamespaceTag(self, node):
        pass
    def visitComponentTag(self, node):
        self.writeSourceComment(node)
        funcname = node.function_decl.funcname
        namedecls = node.function_decl.get_argument_expressions()
        nameargs = node.function_decl.get_argument_expressions(include_defaults=False)
        nameargs.insert(0, 'context')
        self.printer.writeline("def %s(%s):" % (funcname, ",".join(namedecls)))
        self.printer.writeline("return render_%s(%s)" % (funcname, ",".join(nameargs)))
        self.printer.writeline(None)
    def visitCallTag(self, node):
        pass
    def visitInheritTag(self, node):
        pass
