import re
try:
    set
except NameError:
    from sets import Set as set

from pygments.lexers.web import \
     HtmlLexer, XmlLexer, JavascriptLexer, CssLexer
from pygments.lexers.agile import PythonLexer
from pygments.lexer import Lexer, DelegatingLexer, RegexLexer, bygroups, \
     include, using, this
from pygments.token import Error, Punctuation, \
     Text, Comment, Operator, Keyword, Name, String, Number, Other
from pygments.util import html_doctype_matches, looks_like_xml

class MakoLexer(RegexLexer):
    name = 'Mako'
    aliases = ['mako']
    filenames = ['*.mao']

    tokens = {
        'root': [
            (r'\s+', Text),
            (r'(<%(def))(\s*)(.*?)(>)(.*?)(</%\2\s*>)(?s)',
             bygroups(Name.Tag, None, Text, Name.Function, Name.Tag,
                      using(this), Name.Tag)),
            (r'(<%(\w+))(.*?)(>)(.*?)(</%\2\s*>)(?s)',
             bygroups(Name.Tag, None, Name.Function, Name.Tag,
                      using(PythonLexer), Name.Tag)),
            (r'(\$\{)(.*?)(\})',
             bygroups(Name.Tag, using(PythonLexer), Name.Tag)),
            (r'(?<=^)\s*?(\%)([^\n]*)(\n|\Z)',
             bygroups(Name.Tag, using(PythonLexer), Other)),
            (r'''(?sx)
                (.+?)               # anything, followed by:
                (?:
                 (?<=\n)(?=[%#]) |  # an eval or comment line
                 (?=</?[%&]) |      # a substitution or block or
                                    # call start or end
                                    # - don't consume
                 (\\\n) |           # an escaped newline
                 \Z                 # end of string
                )
            ''', bygroups(Other, Operator)),
        ]
    }


class MakoHtmlLexer(DelegatingLexer):
    name = 'HTML+Mako'
    aliases = ['html+mako']

    def __init__(self, **options):
        super(MakoHtmlLexer, self).__init__(HtmlLexer, MakoLexer,
                                              **options)

class MakoXmlLexer(DelegatingLexer):
    name = 'XML+Mako'
    aliases = ['xml+mako']

    def __init__(self, **options):
        super(MakoXmlLexer, self).__init__(XmlLexer, MakoLexer,
                                             **options)

class MakoJavascriptLexer(DelegatingLexer):
    name = 'JavaScript+Mako'
    aliases = ['js+mako', 'javascript+mako']

    def __init__(self, **options):
        super(MakoJavascriptLexer, self).__init__(JavascriptLexer,
                                                    MakoLexer, **options)

class MakoCssLexer(DelegatingLexer):
    name = 'CSS+Mako'
    aliases = ['css+mako']

    def __init__(self, **options):
        super(MakoCssLexer, self).__init__(CssLexer, MakoLexer,
                                             **options)
