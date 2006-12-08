import re
from mako.lookup import TemplateLookup

class TGPlugin(object):
    """TurboGears compatible Template Plugin."""
    extension = 'mak'

    def __init__(self, extra_vars_func=None, options=None):
        self.extra_vars_func = extra_vars_func
        if not options:
            options = {}

        # Pull the options out and initialize the lookup
        tmpl_options = {}
        for k, v in options.iteritems():
            if k.startswith('mako.'):
                tmpl_options[k[5:]] = v
        self.lookup = TemplateLookup(**tmpl_options)

    def load_template(self, templatename):
        """Unused method for TG plug-in API compat"""
        pass

    def render(self, info, format="html", fragment=False, template=None):
        # Translate TG dot notation to normal / template path
        if '/' and '.' not in template:
            template = '/' + template.replace('.', '/') + '.' + self.extension

        if not template.startswith('/'):
            template = '/' + template

        # Load extra vars func if provided
        if self.extra_vars_func:
            info.update(self.extra_vars_func())

        # Lookup template
        template = self.lookup.get_template(template)
        return template.render(**info)

