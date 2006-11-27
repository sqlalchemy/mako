# exceptions.py
# Copyright (C) 2006 Michael Bayer mike_mp@zzzcomputing.com
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

"""exception classes"""

import traceback, sys, re

class MakoException(Exception):
    pass

class RuntimeException(MakoException):
    pass

def _format_filepos(lineno, pos, filename):
    if filename is None:
        return " at line: %d char: %d" % (lineno, pos)
    else:
        return " in file '%s' at line: %d char: %d" % (filename, lineno, pos)     
class CompileException(MakoException):
    def __init__(self, message, lineno, pos, filename):
        MakoException.__init__(self, message + _format_filepos(lineno, pos, filename))
        self.lineno =lineno
        self.pos = pos
        self.filename = filename
                    
class SyntaxException(MakoException):
    def __init__(self, message, lineno, pos, filename):
        MakoException.__init__(self, message + _format_filepos(lineno, pos, filename))
        self.lineno =lineno
        self.pos = pos
        self.filename = filename
        
class TemplateLookupException(MakoException):
    pass
    
def rich_traceback():
    """format a traceback from sys.exc_info() into 7-item tuples, containing
    the regular four traceback tuple items, plus the original template 
    filename, the line number adjusted relative to the template source, and
    code line from that line number of the template."""
    import mako.template
    mods = {}
    (type, value, trcback) = sys.exc_info()
    rawrecords = traceback.extract_tb(trcback)
    # this line extends the stack all the way back....shouldnt be needed...
    # rawrecords = traceback.extract_stack() + rawrecords 
    new_trcback = []
    for filename, lineno, function, line in rawrecords:
        try:
            (line_map, template_lines) = mods[filename]
        except KeyError:
            try:
                info = mako.template._get_module_info(filename)
                module_source = info.code
                template_source = info.source
                template_filename = info.template_filename
            except KeyError:
                new_trcback.append((filename, lineno, function, line, None, None, None))
                continue

            template_ln = module_ln = 1
            line_map = {}
            for line in module_source.split("\n"):
                match = re.match(r'\s*# SOURCE LINE (\d+)', line)
                if match:
                    template_ln = int(match.group(1))
                else:
                    template_ln += 1
                module_ln += 1
                line_map[module_ln] = template_ln
            template_lines = [line for line in template_source.split("\n")]
            mods[filename] = (line_map, template_lines)

        template_ln = line_map[lineno]
        if template_ln <= len(template_lines):
            template_line = template_lines[template_ln - 1]
        else:
            template_line = None
        new_trcback.append((filename, lineno, function, line, template_filename, template_ln, template_line))
    return (type, value, new_trcback)
    
# TODO: this is scratch, make a module for exception reporting templates
def get_error_template():
    import mako.template
    return mako.template.Template("""
<%!
    from mako.exceptions import rich_traceback
%>
<html>
<body>
    Error !
<%
    (type, value, trcback) = rich_traceback()
%>

${str(type)} - ${value}

% for (filename, lineno, function, line, template_filename, template_ln, template_line) in trcback:
        % if template_line:
        ${template_filename} ${template_ln} ${template_line} <br/>
        % else:
        ${filename} ${lineno} ${line} ${template_filename} ${template_ln}<br/>
        % endif
% endfor
</body>
</html>
""")