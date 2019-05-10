
from mako.lookup import TemplateLookup
from mako.exceptions import MakoException, html_error_template

template_lookup = TemplateLookup()
def run():
    tpl = template_lookup.get_template('not_found.html')

