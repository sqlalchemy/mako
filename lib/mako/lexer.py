import re
from mako import parsetree, exceptions

class Lexer(object):
    def __init__(self, text):
        self.text = text
        self.nodes = []
        self.matched_lineno = 1
        self.matched_charpos = 0
        self.lineno = 1
        self.match_position = 0
        self.tag = []
        
    def match(self, regexp, flags=None):
        """return a matching function that will operate on this Lexer's text and current match position"""
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
    
    def append_node(self, nodecls, *args, **kwargs):
        kwargs['lineno'] = self.matched_lineno
        kwargs['pos'] = self.matched_charpos
        node = nodecls(*args, **kwargs)
        if len(self.tag):
            self.tag[-1].nodes.append(node)
        else:
            self.nodes.append(node)
        if isinstance(node, parsetree.Tag):
            self.tag.append(node)
            
    def parse(self):
        length = len(self.text)
        while (True):
            if self.match_position > length: 
                break
        
            if self.match_end():
                break
            
            if self.match_tag_start(): 
                continue
            if self.match_tag_end():
                continue
                
            if self.match_text(): 
                continue
            
            if (self.current.match_position > len(self.current.source)):
                break
        
            raise exceptions.Compiler("Infinite parsing loop encountered - Lexer bug?")
        if len(self.tag):
            raise exceptions.SyntaxException("Unclosed tag: <%%%s>" % self.tag[-1].keyword, self.matched_lineno)
        return self.nodes    

    def match_tag_start(self):
        match = self.match(r'\<%(\w+)(\s+[^>]*)?\s*>', re.I | re.S )
        if match:
            (keyword, attr) = (match.group(1).lower(), match.group(2))
            self.keyword = keyword
            attributes = {}
            if attr:
                for att in re.findall(r"\s*((\w+)\s*=\s*('[^']*'|\"[^\"]*\"|\w+))\s*", attr):
                    (full, key, val) = att
                    attributes[key] = val

            self.append_node(parsetree.Tag, keyword, attributes)
            return True
        else: 
            return False
        
    def match_tag_end(self):
        if not len(self.tag):
            return False
        match = self.match(r'\</%\s*' + self.tag[-1].keyword + '\s*>')
        if match:
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
                 (?<=\n)\s*(?=[%#]) # an eval or comment line, preceded by a consumed \n and whitespace
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
                
    def _count_lines(self, text):
        return len(re.findall(r"\n", text)) 