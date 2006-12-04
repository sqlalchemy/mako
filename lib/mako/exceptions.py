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

class TopLevelLookupException(TemplateLookupException):
    pass
    
class RichTraceback(object):
    """pulls the current exception from the sys traceback and extracts Mako-specific information."""
    def __init__(self):
        (self.source, self.lineno) = ("", 0)
        (t, self.error, self.records) = self._init()
        if self.error is None:
            self.error = t
        if isinstance(self.error, CompileException) or isinstance(self.error, SyntaxException):
            self.source = file(self.error.filename).read()
            self.lineno = self.error.lineno
        self.reverse_records = [r for r in self.records]
        self.reverse_records.reverse()
    def _init(self):
        """format a traceback from sys.exc_info() into 7-item tuples, containing
        the regular four traceback tuple items, plus the original template 
        filename, the line number adjusted relative to the template source, and
        code line from that line number of the template."""
        import mako.template
        mods = {}
        (type, value, trcback) = sys.exc_info()
        rawrecords = traceback.extract_tb(trcback)
        # this line extends the stack all the way back....shouldnt be needed...
        #rawrecords = traceback.extract_stack() + rawrecords 
        new_trcback = []
        for filename, lineno, function, line in rawrecords:
            #print "TB", filename, lineno, function, line
            try:
                (line_map, template_lines) = mods[filename]
            except KeyError:
                try:
                    info = mako.template._get_module_info(filename)
                    module_source = info.code
                    template_source = info.source
                    template_filename = info.template_filename or filename
                except KeyError:
                    new_trcback.append((filename, lineno, function, line, None, None, None, None))
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
                self.source = template_source
                self.lineno = template_ln
            else:
                template_line = None
            new_trcback.append((filename, lineno, function, line, template_filename, template_ln, template_line, template_source))
        return (type, value, new_trcback)

                
def text_error_template(lookup=None):
    import mako.template
    return mako.template.Template(r"""
<%!
    from mako.exceptions import RichTraceback
%>
Error !
<%
    (type, value, trcback) = rich_traceback()
%>

${str(type)} - ${value}

% for (filename, lineno, function, line, template_filename, template_ln, template_line) in trcback:
    % if template_line:
    ${template_filename} ${template_ln} ${template_line}
    % else:
    ${filename} ${lineno} ${line}
    % endif
% endfor
""", lookup=lookup)

def html_error_template(lookup=None):
    import mako.template
    return mako.template.Template(r"""
<%!
    from mako.exceptions import RichTraceback
%>
<html>
<head>
    <title>Mako Runtime Error</title>
    <style>
        body {
            font-family:verdana;
        }
        .stacktrace {
            margin:10px 30px 10px 30px;
        }
        .highlight {
            padding:0px 10px 0px 10px;
            background-color:#9F9FDF;
        }
        .nonhighlight {
            padding:0px;
            background-color:#DFDFDF;
        }
        .sample {
            padding:10px;
            margin:10px 40px 10px 40px;
            font-family:monospace;
        }
        .sampleline {
            padding:0px 10px 0px 10px;
        }
        .sourceline {
            font-size:80%;
            margin-bottom:10px;
        }
        .location {
            font-size:80%;
        }
    </style>
</head>
<body>

        <h2>Error !</h2>
<%
    tback = RichTraceback()
    src = tback.source
    line = tback.lineno
    if src:
        lines = src.split('\n')
    else:
        lines = None
%>
<p>
${str(tback.error.__class__.__name__)}: ${str(tback.error)}
</p>

% if lines:
    <div class="sample">
    <div class="nonhighlight">
% for index in range(max(0, line-4),min(len(lines), line+5)):
    % if index + 1 == line:
<div class="highlight">${index + 1} ${lines[index] | h}</div>
    % else:
<div class="sampleline">${index + 1} ${lines[index] | h}</div>
    % endif
% endfor
    </div>
    </div>
% endif

<%def name="traceline(filename, lineno, source)">
    <div class="location">${filename} ${lineno}:</div>
    <div class="sourceline">${source}</div>
</%def>

<div class="stacktrace">
% for (filename, lineno, function, line, template_filename, template_ln, template_line, src) in tback.reverse_records:
        % if template_line:
            ${traceline(template_filename, template_ln, template_line)}
        % else:
            ${traceline(filename, lineno, line)}
        % endif
% endfor
</div>

</body>
</html>
""", lookup=lookup)