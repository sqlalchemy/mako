from StringIO import StringIO
import re, string
try:
    Set = set
except:
    import sets
    Set = sets.Set


def adjust_whitespace(text):
    state = [False, False]
    (backslashed, triplequoted) = (0, 1)
    def in_multi_line(line):
        current_state = (state[backslashed] or state[triplequoted]) 
        if re.search(r"\\$", line):
            state[backslashed] = True
        else:
            state[backslashed] = False
        triples = len(re.findall(r"\"\"\"|\'\'\'", line))
        if triples == 1 or triples % 2 != 0:
            state[triplequoted] = not state[triplequoted]
        return current_state

    def _indent_line(line, stripspace = ''):
        return re.sub(r"^%s" % stripspace, '', line)

    stream = StringIO()
    stripspace = None

    for line in re.split(r'\r?\n', text):
        if in_multi_line(line):
            stream.write(line + "\n")
        else:
            line = string.expandtabs(line)
            if stripspace is None and re.search(r"^[ \t]*[^# \t]", line):
                stripspace = re.match(r"^([ \t]*)", line).group(1)
            stream.write(_indent_line(line, stripspace) + "\n")
    return stream.getvalue()
