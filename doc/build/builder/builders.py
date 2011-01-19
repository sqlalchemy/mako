from sphinx.application import TemplateBridge
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.highlighting import PygmentsBridge
from pygments import highlight
from pygments.lexer import RegexLexer, bygroups, using
from pygments.token import *
from pygments.filter import Filter, apply_filters
from pygments.lexers import PythonLexer, PythonConsoleLexer
from pygments.formatters import HtmlFormatter, LatexFormatter
import re
from mako.lookup import TemplateLookup
from mako.template import Template
from mako.ext.pygmentplugin import MakoLexer

class MakoBridge(TemplateBridge):
    def init(self, builder, *args, **kw):
        self.layout = builder.config.html_context.get('mako_layout', 'html')
 
        self.lookup = TemplateLookup(directories=builder.config.templates_path,
            format_exceptions=True, 
            imports=[
                "from builder import util"
            ]
        )
 
    def render(self, template, context):
        template = template.replace(".html", ".mako")
        context['prevtopic'] = context.pop('prev', None)
        context['nexttopic'] = context.pop('next', None)
        context['mako_layout'] = self.layout == 'html' and 'static_base.mako' or 'site_base.mako'
        # sphinx 1.0b2 doesn't seem to be providing _ for some reason...
        context.setdefault('_', lambda x:x)
        return self.lookup.get_template(template).render_unicode(**context)
 
 
    def render_string(self, template, context):
        context['prevtopic'] = context.pop('prev', None)
        context['nexttopic'] = context.pop('next', None)
        context['mako_layout'] = self.layout == 'html' and 'static_base.mako' or 'site_base.mako'
        # sphinx 1.0b2 doesn't seem to be providing _ for some reason...
        context.setdefault('_', lambda x:x)
        return Template(template, lookup=self.lookup,
            format_exceptions=True, 
            imports=[
                "from builder import util"
            ]
        ).render_unicode(**context)
 
class StripDocTestFilter(Filter):
    def filter(self, lexer, stream):
        for ttype, value in stream:
            if ttype is Token.Comment and re.match(r'#\s*doctest:', value):
                continue
            yield ttype, value


def autodoc_skip_member(app, what, name, obj, skip, options):
    if what == 'class' and skip and name == '__init__':
        return False
    else:
        return skip

def setup(app):
#    app.connect('autodoc-skip-member', autodoc_skip_member)
    # Mako is already in Pygments, adding the local
    # lexer here so that the latest syntax is available
    app.add_lexer('mako', MakoLexer())
 
 