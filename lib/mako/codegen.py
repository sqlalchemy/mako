"""provides the Compiler object for generating module source code."""

from StringIO import StringIO
import time
from mako.pygen import PythonPrinter
from mako import util, ast

MAGIC_NUMBER = 1

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
        
        components = _find_top_level_components(self.node)
        
        (module_declared, module_undeclared) = (util.Set(), util.Set())
        
        buf = StringIO()
        printer = PythonPrinter(buf)
        
        # module-level names, python code
        printer.writeline("from mako import runtime")
        printer.writeline("_magic_number = %s" % repr(MAGIC_NUMBER))
        printer.writeline("_modified_time = %s" % repr(time.time()))
        printer.writeline("_template_filename=%s" % repr(self.filename))
        buf.write("\n\n")
        for n in module_code:
            (module_declared, module_undeclared) = _find_declared_identifiers([n], module_declared, module_undeclared)
            printer.writeline("# SOURCE LINE %d" % n.lineno, is_comment=True)
            printer.write_indented_block(n.text)
        
        # print main render() method
        (declared, undeclared) = _find_declared_identifiers(self.node.nodes, module_declared)
        self.node.accept_visitor(_GenerateRenderMethod(printer, declared, undeclared, components))
        printer.writeline(None)
        buf.write("\n\n")

        # print render() for each top-level component
        for node in components:
            declared = util.Set(node.declared_identifiers()).union(module_declared)
            (declared, undeclared) = _find_declared_identifiers(node.nodes, declared)
            local_components = _find_top_level_components(node.nodes)
            render = _GenerateRenderMethod(printer, declared, undeclared, components + local_components, name="render_%s" % node.name, args=node.function_decl.get_argument_expressions())
            for n in node.nodes:
                n.accept_visitor(render)
            printer.writeline("return ''")
            printer.writeline(None)
            buf.write("\n\n")
            
        return buf.getvalue()
    

class _GenerateRenderMethod(object):
    def __init__(self, printer, declared, undeclared, components, name='render', in_component=False, args=None):
        self.printer = printer
        self.in_component = in_component
        self.last_source_line = -1
        if args is None:
            args = ['context']
        else:
            args = [a for a in ['context'] + args]
        printer.writeline("def %s(%s):" % (name, ','.join(args)))
        
        self.write_variable_declares(declared, undeclared, components)

    def write_variable_declares(self, declared, undeclared, components):
        comp_idents = dict([(c.name, c) for c in components])
        for ident in undeclared:
            if ident in comp_idents:
                comp = comp_idents[ident]
                if comp.is_root():
                    self.write_component_decl(comp)
                else:
                    self.write_inline_component(comp, declared.union(undeclared), None)
            else:
                self.printer.writeline("%s = context.get(%s, None)" % (ident, repr(ident)))
        
    def write_source_comment(self, node):
        if self.last_source_line != node.lineno:
            self.printer.writeline("# SOURCE LINE %d" % node.lineno, is_comment=True)
            self.last_source_line = node.lineno

    def write_component_decl(self, node):
        funcname = node.function_decl.funcname
        namedecls = node.function_decl.get_argument_expressions()
        nameargs = node.function_decl.get_argument_expressions(include_defaults=False)
        nameargs.insert(0, 'context')
        self.printer.writeline("def %s(%s):" % (funcname, ",".join(namedecls)))
        self.printer.writeline("return render_%s(%s)" % (funcname, ",".join(nameargs)))
        self.printer.writeline(None)
        
    def write_inline_component(self, node, declared, undeclared):
        namedecls = node.function_decl.get_argument_expressions()
        self.printer.writeline("def %s(%s):" % (node.name, ",".join(namedecls)))
        components = _find_top_level_components(node.nodes)
        (declared, undeclared) = _find_declared_identifiers(node.nodes, declared, undeclared)
        self.write_variable_declares(declared, undeclared, components)
        for n in node.nodes:
            n.accept_visitor(self)
        self.printer.writeline("return ''")
        self.printer.writeline(None)

    def visitExpression(self, node):
        self.write_source_comment(node)
        self.printer.writeline("context.write(unicode(%s))" % node.text)
    def visitControlLine(self, node):
        if node.isend:
            self.printer.writeline(None)
        else:
            self.write_source_comment(node)
            self.printer.writeline(node.text)
    def visitText(self, node):
        self.write_source_comment(node)
        self.printer.writeline("context.write(%s)" % repr(node.content))
    def visitCode(self, node):
        if not node.ismodule:
            self.write_source_comment(node)
            self.printer.write_indented_block(node.text)
    def visitIncludeTag(self, node):
        self.write_source_comment(node)
        self.printer.writeline("context.include_file(%s, import=%s)" % (repr(node.attributes['file']), repr(node.attributes.get('import', False))))
    def visitNamespaceTag(self, node):
        self.write_source_comment(node)
        self.printer.writeline("def make_namespace():")
        export = []
        class NSComponentVisitor(object):
            def visitComponentTag(s, node):
                self.write_inline_component(node, None, None)
                export.append(node.name)
        vis = NSComponentVisitor()
        for n in node.nodes:
            n.accept_visitor(vis)
        self.printer.writeline("return %s" % (repr(export)))
        self.printer.writeline(None)
        self.printer.writeline("class %sNamespace(runtime.Namespace):" % node.name)
        self.printer.writeline("def __getattr__(self, key):")
        self.printer.writeline("return self.contextual_callable(context, key)")
        self.printer.writeline(None)
        self.printer.writeline(None)
        self.printer.writeline("%s = %sNamespace(%s, callables=make_namespace())" % (node.name, node.name))
        
    def visitComponentTag(self, node):
        pass
    def visitCallTag(self, node):
        pass
    def visitInheritTag(self, node):
        pass

def _find_top_level_components(nodes):
    components = []
    class FindTopLevelComponents(object):
        def visitComponentTag(self, node):
            components.append(node)
    ftl = FindTopLevelComponents()
    if isinstance(nodes, list):
        for n in nodes:
            n.accept_visitor(ftl)
    else:
        nodes.accept_visitor(ftl)
    return components

def _find_declared_identifiers(nodes, declared=None, undeclared=None):
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
            pass
            #check_declared(node)
        def visitIncludeTag(self, node):
            # TODO: expressions for attributes
            pass        
        def visitNamespaceTag(self, node):
            check_declared(node)
    fd = FindUndeclared()
    for n in nodes:
        n.accept_visitor(FindUndeclared())        
    return (declared, undeclared)
