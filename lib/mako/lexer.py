# lexer.py
# Copyright (C) 2006 Michael Bayer mike_mp@zzzcomputing.com
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

"""provides the Lexer class for parsing template strings into parse trees."""

import re
from mako import parsetree, exceptions
from mako.pygen import adjust_whitespace

class Lexer(object):
    def __init__(self, text, filename=None):
        self.text = text
        self.filename = filename
        self.template = parsetree.TemplateNode(self.filename)
        self.matched_lineno = 1
        self.matched_charpos = 0
        self.lineno = 1
        self.match_position = 0
        self.tag = []
        self.control_line = []
        
    def match(self, regexp, flags=None):
        """match the given regular expression string and flags to the current text position.
        
        if a match occurs, update the current text and line position."""
        mp = self.match_position
        if flags:
            reg = re.compile(regexp, flags)
        else:
            reg = re.compile(regexp)
        match = reg.match(self.text, self.match_position)
        if match:
            (start, end) = match.span()
            if end == start:
                self.match_position = end + 1
            else:
                self.match_position = end
            self.matched_lineno = self.lineno
            lines = re.findall(r"\n", self.text[mp:self.match_position])
            cp = mp - 1
            while (cp >= 0 and cp<len(self.text) and self.text[cp] != '\n'):
                cp -=1
            self.matched_charpos = mp - cp
            self.lineno += len(lines)
            #print "MATCHED:", match.group(0), "LINE START:", self.matched_lineno, "LINE END:", self.lineno
        #print "MATCH:", regexp, "\n", self.text[mp : mp + 15], (match and "TRUE" or "FALSE")
        return match
    
    def parse_until_text(self, *text):
        startpos = self.match_position
        while True:
            match = self.match(r'(\"\"\"|\'\'\'|\"|\')')
            if match:
                m = self.match(r'.*?%s' % match.group(1), re.S)
                if not m:
                    raise exceptions.SyntaxException("Unmatched '%s'" % match.group(1), self.matched_lineno, self.matched_charpos, self.filename)
            else:
                match = self.match(r'(%s)' % r'|'.join(text))
                if match:
                    return (self.text[startpos:self.match_position-len(match.group(1))], match.group(1))
                else:
                    match = self.match(r".*?(?=\"|\'|%s)" % r'|'.join(text), re.S)
                    if not match:
                        raise exceptions.SyntaxException("Expected: %s" % ','.join(text), self.matched_lineno, self.matched_charpos, self.filename)
                
    def append_node(self, nodecls, *args, **kwargs):
        kwargs.setdefault('lineno', self.matched_lineno)
        kwargs.setdefault('pos', self.matched_charpos)
        kwargs['filename'] = self.filename
        node = nodecls(*args, **kwargs)
        if len(self.tag):
            self.tag[-1].nodes.append(node)
        else:
            self.template.nodes.append(node)
        if isinstance(node, parsetree.Tag):
            if len(self.tag):
                node.parent = self.tag[-1]
            self.tag.append(node)
        elif isinstance(node, parsetree.ControlLine):
            if node.isend:
                self.control_line.pop()
            elif node.is_primary:
                self.control_line.append(node)
            elif len(self.control_line) and not self.control_line[-1].is_ternary(node.keyword):
                raise exceptions.SyntaxException("Keyword '%s' not a legal ternary for keyword '%s'" % (node.keyword, self.control_line[-1].keyword), self.matched_lineno, self.matched_charpos, self.filename)

    def parse(self):
        encoding = self.match_encoding()
        if encoding:
            self.text = self.text.decode(encoding)

        length = len(self.text)
            
        while (True):
            if self.match_position > length: 
                break
        
            if self.match_end():
                break
            if self.match_expression():
                continue
            if self.match_control_line():
                continue
            if self.match_tag_start(): 
                continue
            if self.match_tag_end():
                continue
            if self.match_python_block():
                continue
            if self.match_text(): 
                continue
            
            if (self.current.match_position > len(self.current.source)):
                break
            raise "assertion failed"
            
        if len(self.tag):
            raise exceptions.SyntaxException("Unclosed tag: <%%%s>" % self.tag[-1].keyword, self.matched_lineno, self.matched_charpos, self.filename)
        return self.template

    def match_encoding(self):
        match = self.match(r'#\s*-\*- encoding: (.+?) -\*-\n')
        if match:
            return match.group(1)
        else:
            return None
            
    def match_tag_start(self):
        match = self.match(r'''
            \<%     # opening tag
            
            (\w+)   # keyword
            
            ((?:\s+\w+|=|".*?"|'.*?')*)  # attrname, = sign, string expression
            
            \s*     # more whitespace
            
            (/)?>   # closing
            
            ''', 
            
            re.I | re.S | re.X)
            
        if match:
            (keyword, attr, isend) = (match.group(1).lower(), match.group(2), match.group(3))
            self.keyword = keyword
            attributes = {}
            if attr:
                for att in re.findall(r"\s*(\w+)\s*=\s*(?:'([^']*)'|\"([^\"]*)\")", attr):
                    (key, val1, val2) = att
                    attributes[key] = val1 or val2
            self.append_node(parsetree.Tag, keyword, attributes)
            if isend:
                self.tag.pop()
            else:
                if keyword == 'text':
                    match = self.match(r'(.*?)(?=\</%text>)',  re.S)
                    if not match:
                        raise exceptions.SyntaxException("Unclosed tag: <%%%s>" % self.tag[-1].keyword, self.matched_lineno, self.matched_charpos, self.filename)
                    self.append_node(parsetree.Text, match.group(1))
                    return self.match_tag_end()
            return True
        else: 
            return False
        
    def match_tag_end(self):
        match = self.match(r'\</%\s*(.+?)\s*>')
        if match:
            if not len(self.tag):
                raise exceptions.SyntaxException("Closing tag without opening tag: </%%%s>" % match.group(1), self.matched_lineno, self.matched_charpos, self.filename)
            elif self.tag[-1].keyword != match.group(1):
                raise exceptions.SyntaxException("Closing tag </%%%s> does not match tag: <%%%s>" % (match.group(1), self.tag[-1].keyword), self.matched_lineno, self.matched_charpos, self.filename)
            self.tag.pop()
            return True
        else:
            return False
            
    def match_end(self):
        match = self.match(r'\Z', re.S)
        if match:
            string = match.group()
            if string:
                return string
            else:
                return True
        else:
            return False
    
    def match_text(self):
        match = self.match(r"""
                (.*?)         # anything, followed by:
                (
                 (?<=\n)(?=\s*[%#]) # an eval or comment line, preceded by a consumed \n and whitespace
                 |
                 (?=\${)   # an expression
                 |
                 (?=</?[%&])  # a substitution or block or call start or end
                                              # - don't consume
                 |
                 (\\\n)         # an escaped newline  - throw away
                 |
                 \Z           # end of string
                )""", re.X | re.S)
        
        if match:
            text = match.group(1)
            self.append_node(parsetree.Text, text)
            return True
        else:
            return False
    
    def match_python_block(self):
        match = self.match(r"<%(!)?")
        if match:
            (line, pos) = (self.matched_lineno, self.matched_charpos)
            (text, end) = self.parse_until_text(r'%>')
            text = adjust_whitespace(text)
            self.append_node(parsetree.Code, text, match.group(1)=='!', lineno=line, pos=pos)
            return True
        else:
            return False
            
    def match_expression(self):
        match = self.match(r"\${")
        if match:
            (line, pos) = (self.matched_lineno, self.matched_charpos)
            (text, end) = self.parse_until_text(r'\|', r'}')
            if end == '|':
                (escapes, end) = self.parse_until_text(r'}')
            else:
                escapes = ""
            self.append_node(parsetree.Expression, text, escapes.strip(), lineno=line, pos=pos)
            return True
        else:
            return False

    def match_control_line(self):
        match = self.match(r"(?<=^)\s*([%#])\s*([^\n]*)(?:\n|\Z)", re.M)
        if match:
            operator = match.group(1)
            text = match.group(2)
            if operator == '%':
                m2 = re.match(r'(end)?(\w+)\s*(.*)', text)
                if not m2:
                    raise exceptions.SyntaxException("Invalid control line: '%s'" % text, self.matched_lineno, self.matched_charpos, self.filename)
                (isend, keyword) = m2.group(1, 2)
                isend = (isend is not None)
                
                if isend:
                    if not len(self.control_line):
                        raise exceptions.SyntaxException("No starting keyword '%s' for '%s'" % (keyword, text), self.matched_lineno, self.matched_charpos, self.filename)
                    elif self.control_line[-1].keyword != keyword:
                        raise exceptions.SyntaxException("Keyword '%s' doesn't match keyword '%s'" % (text, self.control_line[-1].keyword), self.matched_lineno, self.matched_charpos, self.filename)
                self.append_node(parsetree.ControlLine, keyword, isend, text)
            else:
                self.append_node(parsetree.Comment, text)
            return True
        else:
            return False
            
    def _count_lines(self, text):
        return len(re.findall(r"\n", text)) 
