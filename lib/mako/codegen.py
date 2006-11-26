# codegen.py
# Copyright (C) 2006 Michael Bayer mike_mp@zzzcomputing.com
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

"""provides the Compiler object for generating module source code."""

import time
import re
from mako.pygen import PythonPrinter
from mako import util, ast, parsetree, filters

MAGIC_NUMBER = 1

class Compiler(object):
    def __init__(self, node, filename=None):
        self.node = node
        self.filename = filename
    def render(self):
        buf = util.FastEncodingBuffer()
        printer = PythonPrinter(buf)

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

        main_identifiers = module_identifiers.branch(self.node)
        module_identifiers.topleveldefs = module_identifiers.topleveldefs.union(main_identifiers.topleveldefs)

        # module-level names, python code
        printer.writeline("from mako import runtime")
        printer.writeline("_magic_number = %s" % repr(MAGIC_NUMBER))
        printer.writeline("_modified_time = %s" % repr(time.time()))
        printer.writeline("_template_filename=%s" % repr(self.filename))
        printer.writeline("UNDEFINED = runtime.UNDEFINED")
        printer.writeline("from mako import filters")
        [module_identifiers.declared.add(x) for x in ["UNDEFINED"]]
        printer.writeline("_exports = %s" % repr([n.name for n in main_identifiers.topleveldefs]))
        printer.write("\n\n")

        
        for n in module_code:
            printer.writeline("# SOURCE LINE %d" % n.lineno, is_comment=True)
            printer.write_indented_block(n.text)

        # print main render() method
        _GenerateRenderMethod(printer, module_identifiers, self.node)

        # print render() for each top-level def
        for node in main_identifiers.topleveldefs:
            _GenerateRenderMethod(printer, module_identifiers, node)
            
        return buf.getvalue()

        
class _GenerateRenderMethod(object):
    def __init__(self, printer, identifiers, node):
        self.printer = printer
        self.last_source_line = -1
        
        self.node = node
        if isinstance(node, parsetree.DefTag):
            name = "render_" + node.name
            args = node.function_decl.get_argument_expressions()
            self.in_def = True
            filtered = len(node.filter_args.args) > 0 
            buffered = eval(node.attributes.get('buffered', 'False'))
        else:
            name = "render"
            args = None
            self.in_def = False
            buffered = filtered = False
            
        if args is None:
            args = ['context']
        else:
            args = [a for a in ['context'] + args]

        if not self.in_def:
            self._inherit()

        printer.writeline("def %s(%s):" % (name, ','.join(args)))
        if buffered or filtered:
            printer.writeline("context.push_buffer()")
            printer.writeline("try:")
            
        self.identifiers = identifiers.branch(node)
        if len(self.identifiers.locally_assigned) > 0:
            printer.writeline("__locals = {}")

        self.write_variable_declares(self.identifiers)

        for n in node.nodes:
            n.accept_visitor(self)

        self.write_def_finish(node, buffered, filtered)

        printer.write("\n\n")

    def _inherit(self):
        class FindInherit(object):
            def visitInheritTag(s, node):
                self.printer.writeline("def _inherit(context):")
                self.printer.writeline("return runtime.inherit_from(context, %s)" % (repr(node.attributes['file'])))
                self.printer.writeline(None)
        f = FindInherit()
        for n in self.node.nodes:
            n.accept_visitor(f)

    def write_variable_declares(self, identifiers, first=None):
        """write variable declarations at the top of a function.
        
        the variable declarations are in the form of callable definitions for defs and/or
        name lookup within the function's context argument.  the names declared are based on the
        names that are referenced in the function body, which don't otherwise have any explicit
        assignment operation.  names that are assigned within the body are assumed to be 
        locally-scoped variables and are not separately declared.
        
        for def callable definitions, if the def is a top-level callable then a 
        'stub' callable is generated which wraps the current Context into a closure.  if the def
        is not top-level, it is fully rendered as a local closure."""
        
        # collection of all defs available to us in this scope
        comp_idents = dict([(c.name, c) for c in identifiers.defs])

        to_write = util.Set()
        
        # write "context.get()" for all variables we are going to need that arent in the namespace yet
        to_write = to_write.union(identifiers.undeclared)
        
        # write closure functions for closures that we define right here
        to_write = to_write.union(util.Set([c.name for c in identifiers.closuredefs]))

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
                    self.write_def_decl(comp, identifiers)
                else:
                    self.write_inline_def(comp, identifiers)
            else:
                if first is not None:
                    self.printer.writeline("%s = %s.get(%s, context.get(%s, UNDEFINED))" % (ident, first, repr(ident), repr(ident)))
                else:
                    self.printer.writeline("%s = context.get(%s, UNDEFINED)" % (ident, repr(ident)))
        
    def write_source_comment(self, node):
        if self.last_source_line != node.lineno:
            self.printer.writeline("# SOURCE LINE %d" % node.lineno, is_comment=True)
            self.last_source_line = node.lineno

    def write_def_decl(self, node, identifiers):
        """write a locally-available callable referencing a top-level def"""
        funcname = node.function_decl.funcname
        namedecls = node.function_decl.get_argument_expressions()
        nameargs = node.function_decl.get_argument_expressions(include_defaults=False)
        if len(self.identifiers.locally_assigned) > 0:
            nameargs.insert(0, 'context.locals_(__locals)')
        else:
            nameargs.insert(0, 'context')
        self.printer.writeline("def %s(%s):" % (funcname, ",".join(namedecls)))
        self.printer.writeline("return render_%s(%s)" % (funcname, ",".join(nameargs)))
        self.printer.writeline(None)
        
    def write_inline_def(self, node, identifiers):
        """write a locally-available def callable inside an enclosing def."""
        namedecls = node.function_decl.get_argument_expressions()
        self.printer.writeline("def %s(%s):" % (node.name, ",".join(namedecls)))
        filtered = len(node.filter_args.args) > 0 
        buffered = eval(node.attributes.get('buffered', 'False'))
        if buffered or filtered:
            printer.writeline("context.push_buffer()")
            printer.writeline("try:")

        identifiers = identifiers.branch(node)
        self.write_variable_declares(identifiers)

        for n in node.nodes:
            n.accept_visitor(self)

        self.write_def_finish(node, buffered, filtered)
        
    def write_def_finish(self, node, buffered, filtered):
        if not buffered:
            self.printer.writeline("return ''")
        if buffered or filtered:
            self.printer.writeline("finally:")
            self.printer.writeline("_buf = context.pop_buffer()")
            s = "_buf.getvalue()"
            if filtered:
                s = self.create_filter_callable(node.filter_args.args, s)
            if buffered:
                self.printer.writeline("return %s" % s)
            else:
                self.printer.writeline("context.write(%s)" % s)
        self.printer.writeline(None)
    
    def create_filter_callable(self, args, target):
        d = dict([(k, "filters." + v.func_name) for k, v in filters.DEFAULT_ESCAPES.iteritems()])
        for e in args:
            e = d.get(e, e)
            target = "%s(%s)" % (e, target)
        return target
        
    def visitExpression(self, node):
        self.write_source_comment(node)
        if len(node.escapes):
            s = self.create_filter_callable(node.escapes_code.args, node.text)
            self.printer.writeline("context.write(unicode(%s))" % s)
        else:
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

            if not self.in_def:
                # if we are the "template" def, fudge locally declared/modified variables into the "__locals" dictionary,
                # which is used for def calls within the same template, to simulate "enclosing scope"
                self.printer.writeline('__locals.update(%s)' % (",".join(["%s=%s" % (x, x) for x in node.declared_identifiers()])))

    def visitIncludeTag(self, node):
        self.write_source_comment(node)
        self.printer.writeline("runtime.include_file(context, %s, import_symbols=%s)" % (node.parsed_attributes['file'], repr(node.attributes.get('import', False))))

    def visitNamespaceTag(self, node):
        self.write_source_comment(node)
        self.printer.writeline("def make_namespace():")
        export = []
        identifiers = self.identifiers.branch(node)
        class NSDefVisitor(object):
            def visitDefTag(s, node):
                self.write_inline_def(node, identifiers)
                export.append(node.name)
        vis = NSDefVisitor()
        for n in node.nodes:
            n.accept_visitor(vis)
        self.printer.writeline("return [%s]" % (','.join(export)))
        self.printer.writeline(None)
        self.printer.writeline("%s = runtime.Namespace(%s, context.clean_inheritance_tokens(), templateuri=%s, callables=make_namespace())" % (node.name, repr(node.name), node.parsed_attributes.get('file', 'None')))
        if eval(node.attributes.get('inheritable', "False")):
            self.printer.writeline("self.%s = %s" % (node.name, node.name))
        
    def visitDefTag(self, node):
        pass

    def visitCallTag(self, node):
        self.write_source_comment(node)
        self.printer.writeline("def ccall(context):")
        export = ['body']
        identifiers = self.identifiers.branch(node)
        class DefVisitor(object):
            def visitDefTag(s, node):
                self.write_inline_def(node, identifiers)
                export.append(node.name)
        vis = DefVisitor()
        for n in node.nodes:
            n.accept_visitor(vis)
        self.printer.writeline("def body(**kwargs):")
        body_identifiers = identifiers.branch(node, includedefs=False, includenode=False)
        self.write_variable_declares(body_identifiers, first="kwargs")
        for n in node.nodes:
            n.accept_visitor(self)
        self.printer.writeline("return ''")
        self.printer.writeline(None)
        self.printer.writeline("return [%s]" % (','.join(export)))
        self.printer.writeline(None)
        self.printer.writeline("__cl = context.locals_({})")
        self.printer.writeline("context.push({'caller':runtime.Namespace('caller', __cl, callables=ccall(__cl))})")
        self.printer.writeline("try:")
        self.printer.writeline("context.write(unicode(%s))" % node.attributes['expr'])
        self.printer.writeline("finally:")
        self.printer.writeline("context.pop()")
        self.printer.writeline(None)

class _Identifiers(object):
    """tracks the status of identifier names as template code is rendered."""
    def __init__(self, node=None, parent=None, includedefs=True, includenode=True):
        if parent is not None:
            # things that have already been declared in an enclosing namespace (i.e. names we can just use)
            self.declared = util.Set(parent.declared).union([c.name for c in parent.closuredefs]).union(parent.locally_declared)
            
            # top level defs that are available
            self.topleveldefs = util.Set(parent.topleveldefs)
        else:
            self.declared = util.Set()
            self.topleveldefs = util.Set()
        
        # things within this level that are referenced before they are declared (e.g. assigned to)
        self.undeclared = util.Set()
        
        # things that are declared locally.  some of these things could be in the "undeclared"
        # list as well if they are referenced before declared
        self.locally_declared = util.Set()
    
        # assignments made in explicit python blocks.  these will be propigated to 
        # the context of local def calls.
        self.locally_assigned = util.Set()
        
        # things that are declared in the argument signature of the def callable
        self.argument_declared = util.Set()
        
        # closure defs that are defined in this level
        self.closuredefs = util.Set()
        
        self.node = node
        self.includedefs = includedefs
        if node is not None:
            if includenode:
                node.accept_visitor(self)
            else:
                for n in node.nodes:
                    n.accept_visitor(self)
        
    def branch(self, node, **kwargs):
        """create a new Identifiers for a new Node, with this Identifiers as the parent."""
        return _Identifiers(node, self, **kwargs)
        
    defs = property(lambda s:s.topleveldefs.union(s.closuredefs))
    
    def __repr__(self):
        return "Identifiers(%s, %s, %s, %s, %s)" % (repr(list(self.declared)), repr(list(self.locally_declared)), repr(list(self.undeclared)), repr([c.name for c in self.topleveldefs]), repr([c.name for c in self.closuredefs]))
        
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
            self.locally_assigned = self.locally_assigned.union(node.declared_identifiers())
    def visitDefTag(self, node):
        if not self.includedefs:
            return
        if node.is_root():
            self.topleveldefs.add(node)
        elif node is not self.node:
            self.closuredefs.add(node)
        for ident in node.undeclared_identifiers():
            if ident != 'context' and ident not in self.declared.union(self.locally_declared):
                self.undeclared.add(ident)
        for ident in node.declared_identifiers():
            self.argument_declared.add(ident)
        # visit defs only one level deep
        if node is self.node:
            for n in node.nodes:
                n.accept_visitor(self)
    def visitIncludeTag(self, node):
        self.check_declared(node)
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