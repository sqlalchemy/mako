from StringIO import StringIO

class TemplateGenerator(object):
    def __init__(self, node):
        self.node = node
    def render(self):
        module_code = []
        class FindPyDecls(object):
            def visitCode(self, node):
                if node.ismodule:
                    module_code.append(node)
        f = FindPyDecls()
        node.accept_visitor(f)
        self._write_module_header()
        
        components = []
        class FindTLComponenents(object):
            def visitComponentTag(self, node):
                components.append(node)
        self.node.accept_visitor(FindTopLevelComponents())
        
        printer = PythonPrinter(StringIO())
        for n in module_code:
            printer.write_indented_block(n.text)
    
        printer.writeline("def render(context):")
        class GenerateRender(object):
            def visitExpression(self, node):
                printer.writeline("context.write('%s')" % node.text)
            def visitControlLine(self, node):
                if node.isend:
                    printer.writeline(None)
                else:
                    printer.writeline(node.text)
            def visitText(self, node):
                printer.writeline("context.write(%s)" % repr(node.text))
            def visitCode(self, node):
                if not node.ismodule:
                    printer.write_indented_block(node.text)
