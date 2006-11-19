"""provides the Compiler object for generating module source code."""

from StringIO import StringIO
from mako.pygen import PythonPrinter
from mako import util, ast

class Compiler(object):
    def __init__(self, node, filename=None):
        self.node = node
        self.filename = filename
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
        
        (module_declared, module_undeclared) = (util.Set(), util.Set())
        
        buf = StringIO()
        printer = PythonPrinter(buf)
        
        printer.writeline("_template_filename=%s" % repr(self.filename))
        for n in module_code:
            (module_declared, module_undeclared) = self._get_declared([n], module_declared, module_undeclared)
            printer.writeline("# SOURCE LINE %d" % n.lineno, is_comment=True)
            printer.write_indented_block(n.text)
        
        (declared, undeclared) = self._get_declared(self.node.nodes, module_declared)
        self.node.accept_visitor(_GenerateRenderMethod(printer, undeclared))
        printer.writeline(None)
        buf.write("\n\n")

        for node in components:
            declared = util.Set(node.declared_identifiers()).union(module_declared)
            (declared, undeclared) = self._get_declared(node.nodes, declared)
            render = _GenerateRenderMethod(printer, undeclared, name="render_%s" % node.name, args=node.function_decl.get_argument_expressions())
            for n in node.nodes:
                n.accept_visitor(render)
            printer.writeline(None)
            buf.write("\n\n")
            
        return buf.getvalue()
    
    def _get_declared(self, nodes, declared=None, undeclared=None):
        if declared is None:
            declared = util.Set()
        else:
            declared = util.Set(declared)
        if undeclared is None:
            undeclared = util.Set()
        else:
            undeclared = util.Set(undeclared)
        def check_declared(node):
            for ident in node.declared_identifiers():
                declared.add(ident)
            for ident in node.undeclared_identifiers():
                if ident != 'context' and ident not in declared:
                    undeclared.add(ident)
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
        fd = FindUndeclared()
        for n in nodes:
            n.accept_visitor(FindUndeclared())        
        return (declared, undeclared)
        
class _GenerateRenderMethod(object):
    def __init__(self, printer, undeclared, name='render', in_component=False, args=None):
        self.printer = printer
        self.in_component = in_component
        self.last_source_line = -1
        if args is None:
            args = ['context']
        else:
            args = [a for a in ['context'] + args]
        printer.writeline("def %s(%s):" % (name, ','.join(args)))
        for ident in undeclared:
            printer.writeline("%s = context.get(%s, None)" % (ident, repr(ident)))
    def writeSourceComment(self, node):
        if self.last_source_line != node.lineno:
            self.printer.writeline("# SOURCE LINE %d" % node.lineno, is_comment=True)
            self.last_source_line = node.lineno
    def visitExpression(self, node):
        self.writeSourceComment(node)
        self.printer.writeline("context.write(unicode(%s))" % node.text)
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
