import re, string

class PythonPrinter(object):
    def __init__(self, stream):
        # indentation counter
        self.indent = 0
        
        # a stack storing information about why we incremented 
        # the indentation counter, to help us determine if we
        # should decrement it
        self.indent_detail = []
        
        # the string of whitespace multiplied by the indent
        # counter to produce a line
        self.indentstring = "    "
        
        # the stream we are writing to
        self.stream = stream
        
        # a list of lines that represents a buffered "block" of code,
        # which can be later printed relative to an indent level 
        self.line_buffer = []
        
        self.in_indent_lines = False
        
        self._reset_multi_line_flags()

    def print_adjusted_line(self, line):
        """print a line or lines of python which already contains indentation.
        
        The indentation of the total block of lines will be adjusted to that of
        the current indent level.""" 
        self.in_indent_lines = False
        for l in re.split(r'\r?\n', line):
            self.line_buffer.append(l)
        
    def print_python_line(self, line, is_comment=False):
        """print a line of python, indenting it according to the current indent level.
        
        this also adjusts the indentation counter according to the content of the line."""

        if not self.in_indent_lines:
            self._flush_adjusted_lines()
            self.in_indent_lines = True

        decreased_indent = False
    
        if (line is None or 
            re.match(r"^\s*#",line) or
            re.match(r"^\s*$", line)
            ):
            hastext = False
        else:
            hastext = True

        # see if this line should decrease the indentation level
        if (not decreased_indent and 
            not is_comment and 
            (not hastext or self._is_unindentor(line))
            ):
            
            if self.indent > 0: 
                self.indent -=1
                # if the indent_detail stack is empty, the user
                # probably put extra closures - the resulting
                # module wont compile.  
                if len(self.indent_detail) == 0:  
                    raise "Too many whitespace closures"
                self.indent_detail.pop()
        
        if line is None:
            return
                
        # write the line
        self.stream.write(self._indent_line(line) + "\n")
        
        # see if this line should increase the indentation level.
        # note that a line can both decrase (before printing) and 
        # then increase (after printing) the indentation level.

        if re.search(r":[ \t]*(?:#.*)?$", line):
            # increment indentation count, and also
            # keep track of what the keyword was that indented us,
            # if it is a python compound statement keyword
            # where we might have to look for an "unindent" keyword
            match = re.match(r"^\s*(if|try|elif|while|for)", line)
            if match:
                # its a "compound" keyword, so we will check for "unindentors"
                indentor = match.group(1)
                self.indent +=1
                self.indent_detail.append(indentor)
            else:
                indentor = None
                # its not a "compound" keyword.  but lets also
                # test for valid Python keywords that might be indenting us,
                # else assume its a non-indenting line
                m2 = re.match(r"^\s*(def|class|else|elif|except|finally)", line)
                if m2:
                    self.indent += 1
                    self.indent_detail.append(indentor)

    def close(self):
        """close this printer, flushing any remaining lines."""
        self._flush_adjusted_lines()
    
    def _is_unindentor(self, line):
        """return true if the given line is an 'unindentor', relative to the last 'indent' event received."""
                
        # no indentation detail has been pushed on; return False
        if len(self.indent_detail) == 0: 
            return False

        indentor = self.indent_detail[-1]
        
        # the last indent keyword we grabbed is not a 
        # compound statement keyword; return False
        if indentor is None: 
            return False
        
        # if the current line doesnt have one of the "unindentor" keywords,
        # return False
        match = re.match(r"^\s*(else|elif|except|finally)", line)
        if not match: 
            return False
        
        # whitespace matches up, we have a compound indentor,
        # and this line has an unindentor, this
        # is probably good enough
        return True
        
        # should we decide that its not good enough, heres
        # more stuff to check.
        #keyword = match.group(1)
        
        # match the original indent keyword 
        #for crit in [
        #   (r'if|elif', r'else|elif'),
        #   (r'try', r'except|finally|else'),
        #   (r'while|for', r'else'),
        #]:
        #   if re.match(crit[0], indentor) and re.match(crit[1], keyword): return True
        
        #return False
        
    def _indent_line(self, line, stripspace = ''):
        """indent the given line according to the current indent level.
        
        stripspace is a string of space that will be truncated from the start of the line
        before indenting."""
        return re.sub(r"^%s" % stripspace, self.indentstring * self.indent, line)

    def _reset_multi_line_flags(self):
        """reset the flags which would indicate we are in a backslashed or triple-quoted section."""
        (self.backslashed, self.triplequoted) = (False, False) 
        
    def _in_multi_line(self, line):
        """return true if the given line is part of a multi-line block, via backslash or triple-quote."""
        # we are only looking for explicitly joined lines here,
        # not implicit ones (i.e. brackets, braces etc.).  this is just
        # to guard against the possibility of modifying the space inside 
        # of a literal multiline string with unfortunately placed whitespace
         
        current_state = (self.backslashed or self.triplequoted) 
                        
        if re.search(r"\\$", line):
            self.backslashed = True
        else:
            self.backslashed = False
            
        triples = len(re.findall(r"\"\"\"|\'\'\'", line))
        if triples == 1 or triples % 2 != 0:
            self.triplequoted = not self.triplequoted
            
        return current_state

    def _flush_adjusted_lines(self):
        stripspace = None
        self._reset_multi_line_flags()
        
        for entry in self.line_buffer:
            if self._in_multi_line(entry):
                self.stream.write(entry + "\n")
            else:
                entry = string.expandtabs(entry)
                if stripspace is None and re.search(r"^[ \t]*[^# \t]", entry):
                    stripspace = re.match(r"^([ \t]*)", entry).group(1)
                self.stream.write(self._indent_line(entry, stripspace) + "\n")
            
        self.line_buffer = []
        self._reset_multi_line_flags()


