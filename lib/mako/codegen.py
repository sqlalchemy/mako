# codegen.py
# Copyright (C) 2006 Michael Bayer mike_mp@zzzcomputing.com
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

"""provides the Compiler object for generating module source code."""

import time
import re
from mako.pygen import PythonPrinter
from mako import util, ast, parsetree

MAGIC_NUMBER = 1

class Compiler(object):
    def __init__(self, node, filename=None):
        self.node = node
        self.filename = filename
    def render(self):
        buf = util.FastEncodingBuffer()
        printer = PythonPrinter(buf)
        
        # module-level names, python code
        printer.writeline("from mako import runtime")
        printer.writeline("_magic_number = %s" % repr(MAGIC_NUMBER))
        printer.writeline("_modified_time = %s" % repr(time.time()))
        printer.writeline("_template_filename=%s" % repr(self.filename))
        printer.write("\n\n")

        module_code = []
        class FindPyDecls(object):
            def visitCode(self, node):
                if node.ismodule:
                    module_code.append(node)
        f = FindPyDecls()
        self.node.accept_visitor(f)
        
        module_identifiers = _Identifiers()
        for n in module_code:
            module_identifiers = module_identifiers.branch(n)
            printer.writeline("# SOURCE LINE %d" % n.lineno, is_comment=True)
            printer.write_indented_block(n.text)

        main_identifiers = module_identifiers.branch(self.node)
        module_identifiers.toplevelcomponents = module_identifiers.toplevelcomponents.union(main_identifiers.toplevelcomponents)

        # print main render() method
        _GenerateRenderMethod(printer, module_identifiers, self.node)

        # print render() for each top-level component
        for node in main_identifiers.toplevelcomponents:
            _GenerateRenderMethod(printer, module_identifiers, node)
            
        return buf.getvalue()

class _GenerateRenderMethod(object):
    def __init__(self, printer, identifiers, node):
        self.printer = printer
        self.last_source_line = -1
        
        self.node = node
        if isinstance(node, parsetree.ComponentTag):
            name = "render_" + node.name
            args = node.function_decl.get_argument_expressions()
            self.in_component = True
        else:
            name = "render"
            args = None
            self.in_component = False
            
        if args is None:
            args = ['context']
        else:
            args = [a for a in ['context'] + args]
            
        printer.writeline("def %s(%s):" % (name, ','.join(args)))
        self.identifiers = identifiers.branch(node)
        if len(self.identifiers.locally_declared) > 0:
            printer.writeline("__locals = {}")

        self.write_variable_declares(self.identifiers)
        for n in node.nodes:
            n.accept_visitor(self)
        printer.writeline("return ''")
        printer.writeline(None)
        printer.write("\n\n")

    def write_variable_declares(self, identifiers):
        """write variable declarations at the top of a function.
        
        the variable declarations are generated based on the names that are referenced
        in the function body before they are assigned.  names that are re-assigned 
        from an enclosing scope are also declared as local variables so that the assignment 
        can proceed.
        
        locally defined components (i.e. closures) are also generated, as well as 'stub' callables 
        referencing top-level components which are referenced in the function body."""
        
        # collection of all components available to us in this scope
        comp_idents = dict([(c.name, c) for c in identifiers.components])

        to_write = util.Set()
        
        # write "context.get()" for all variables we are going to need that arent in the namespace yet
        to_write = to_write.union(identifiers.undeclared)
        
        # write closure functions for closures that we define right here
        to_write = to_write.union(util.Set([c.name for c in identifiers.closurecomponents]))

        # remove identifiers that are declared in the argument signature of the callable
        to_write = to_write.difference(identifiers.argument_declared)

        # remove identifiers that we are going to assign to.  in this way we mimic Python's behavior,
        # i.e. assignment to a variable within a block means that variable is now a "locally declared" var,
        # which cannot be referenced beforehand.  
        to_write = to_write.difference(identifiers.locally_declared)
        
        for ident in to_write:
            if ident in comp_idents:
                comp = comp_idents[ident]
                if comp.is_root():
                    self.write_component_decl(comp, identifiers)
                else:
                    self.write_inline_component(comp, identifiers)
            else:
                self.printer.writeline("%s = context.get(%s, runtime.UNDEFINED)" % (ident, repr(ident)))
        
    def write_source_comment(self, node):
        if self.last_source_line != node.lineno:
            self.printer.writeline("# SOURCE LINE %d" % node.lineno, is_comment=True)
            self.last_source_line = node.lineno

    def write_component_decl(self, node, identifiers):
        """write a locally-available callable referencing a top-level component"""
        funcname = node.function_decl.funcname
        namedecls = node.function_decl.get_argument_expressions()
        nameargs = node.function_decl.get_argument_expressions(include_defaults=False)
        if len(self.identifiers.locally_declared) > 0:
            nameargs.insert(0, 'context.locals_(__locals)')
        else:
            nameargs.insert(0, 'context')
        self.printer.writeline("def %s(%s):" % (funcname, ",".join(namedecls)))
        self.printer.writeline("return render_%s(%s)" % (funcname, ",".join(nameargs)))
        self.printer.writeline(None)
        
    def write_inline_component(self, node, identifiers):
        """write a locally-available component callable inside an enclosing component."""
        namedecls = node.function_decl.get_argument_expressions()
        self.printer.writeline("def %s(%s):" % (node.name, ",".join(namedecls)))
        
        #print "INLINE NAME", node.name
        identifiers = identifiers.branch(node)
        
        # if we assign to variables in this closure, then we have to nest inside
        # of another callable so that the "context" variable is copied into the local scope
        #make_closure = len(identifiers.locally_declared) > 0
        
        #if make_closure:
        #    self.printer.writeline("try:")
        #    self.printer.writeline("context.push()")
        self.write_variable_declares(identifiers)

        for n in node.nodes:
            n.accept_visitor(self)
        self.printer.writeline("return ''")
        self.printer.writeline(None)

        #if make_closure:
        #    self.printer.writeline("finally:")
        #    self.printer.writeline("context.pop()")
        #    self.printer.writeline(None)
        #    self.printer.writeline(None)
            
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

            if not self.in_component:
                # if we are the "template" component, fudge locally declared/modified variables into the "__locals" dictionary,
                # which is used for component calls within the same template, to simulate "enclosing scope"
                self.printer.writeline('__locals.update(%s)' % (",".join(["%s=%s" % (x, x) for x in node.declared_identifiers()])))

    def visitIncludeTag(self, node):
        self.write_source_comment(node)
        self.printer.writeline("runtime.include_file(context, %s, import_symbols=%s)" % (repr(node.attributes['file']), repr(node.attributes.get('import', False))))
    def visitNamespaceTag(self, node):
        self.write_source_comment(node)
        self.printer.writeline("def make_namespace():")
        export = []
        identifiers = self.identifiers.branch(node)
        class NSComponentVisitor(object):
            def visitComponentTag(s, node):
                self.write_inline_component(node, identifiers)
                export.append(node.name)
        vis = NSComponentVisitor()
        for n in node.nodes:
            n.accept_visitor(vis)
        self.printer.writeline("return [%s]" % (','.join(export)))
        self.printer.writeline(None)
        self.printer.writeline("class %sNamespace(runtime.Namespace):" % node.name)
        self.printer.writeline("def __getattr__(self, key):")
        self.printer.writeline("return self.contextual_callable(context, key)")
        self.printer.writeline(None)
        self.printer.writeline(None)
        self.printer.writeline("%s = %sNamespace(%s, callables=make_namespace())" % (node.name, node.name, repr(node.name)))
        
    def visitComponentTag(self, node):
        pass
    def visitCallTag(self, node):
        self.write_source_comment(node)
        self.printer.writeline("def ccall():")
        export = ['body']
        identifiers = self.identifiers.branch(node)
        self.write_variable_declares(identifiers)
        class ComponentVisitor(object):
            def visitComponentTag(s, node):
                export.append(node.name)
        vis = ComponentVisitor()
        for n in node.nodes:
            n.accept_visitor(vis)
        self.printer.writeline("def body():")
        for n in node.nodes:
            n.accept_visitor(self)
        self.printer.writeline("return ''")
        self.printer.writeline(None)
        self.printer.writeline("context.push(**{%s})" % 
            (','.join(["%s:%s" % (repr(x), x) for x in export] + ["'callargs':runtime.AttrDict(**{%s})" % ','.join(["%s:%s" % (repr(x), x) for x in export])]) )
        )
        self.printer.writeline("context.write(unicode(%s))" % node.attributes['expr'])
        self.printer.writeline("context.pop()")
        self.printer.writeline(None)
        self.printer.writeline("ccall()")

    def visitInheritTag(self, node):
        pass

class _Identifiers(object):
    """tracks the status of identifier names as template code is rendered."""
    def __init__(self, node=None, parent=None):
        if parent is not None:
            # things that have already been declared in an enclosing namespace (i.e. names we can just use)
            self.declared = util.Set(parent.declared).union([c.name for c in parent.closurecomponents]).union(parent.locally_declared)
            
            # top level components that are available
            self.toplevelcomponents = util.Set(parent.toplevelcomponents)
        else:
            self.declared = util.Set()
            self.toplevelcomponents = util.Set()
        
        # things within this level that are referenced before they are declared (e.g. assigned to)
        self.undeclared = util.Set()
        
        # things that are declared locally.  some of these things could be in the "undeclared"
        # list as well if they are referenced before declared
        self.locally_declared = util.Set()
    
        # things that are declared in the argument signature of the component callable
        self.argument_declared = util.Set()
        
        # closure components that are defined in this level
        self.closurecomponents = util.Set()
        
        self.node = node
        if node is not None:
            node.accept_visitor(self)
        
    def branch(self, node):
        """create a new Identifiers for a new Node, with this Identifiers as the parent."""
        return _Identifiers(node, self)
        
    components = property(lambda s:s.toplevelcomponents.union(s.closurecomponents))
    
    def __repr__(self):
        return "Identifiers(%s, %s, %s, %s, %s)" % (repr(list(self.declared)), repr(list(self.locally_declared)), repr(list(self.undeclared)), repr([c.name for c in self.toplevelcomponents]), repr([c.name for c in self.closurecomponents]))
        
    def check_declared(self, node):
        """update the state of this Identifiers with the undeclared and declared identifiers of the given node."""
        for ident in node.undeclared_identifiers():
            if ident != 'context' and ident not in self.declared.union(self.locally_declared):
                self.undeclared.add(ident)
        for ident in node.declared_identifiers():
            self.locally_declared.add(ident)
                
    def visitExpression(self, node):
        self.check_declared(node)
    def visitControlLine(self, node):
        self.check_declared(node)
    def visitCode(self, node):
        if not node.ismodule:
            self.check_declared(node)
    def visitComponentTag(self, node):
        if node.is_root():
            self.toplevelcomponents.add(node)
        elif node is not self.node:
            self.closurecomponents.add(node)
        for ident in node.declared_identifiers():
            self.argument_declared.add(ident)
        # visit components only one level deep
        if node is self.node:
            for n in node.nodes:
                n.accept_visitor(self)
    def visitIncludeTag(self, node):
        # TODO: expressions for attributes
        pass        
    def visitNamespaceTag(self, node):
        self.check_declared(node)
        if node is self.node:
            for n in node.nodes:
                n.accept_visitor(self)
                
    def visitCallTag(self, node):
        self.check_declared(node)
        if node is self.node:
            for n in node.nodes:
                n.accept_visitor(self)