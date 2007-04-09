import re
from mako.lookup import TemplateLookup
from mako.template import Template

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
            elif k in ['directories', 'filesystem_checks', 'module_directory']:
                tmpl_options[k] = v
        self.tmpl_options = tmpl_options
        self.lookup = TemplateLookup(**tmpl_options)

    def load_template(self, templatename, template_string=None):
        """Loads a template from a file or a string"""
        if template_string is not None:
            return Template(template_string, **self.tmpl_options)
        # Translate TG dot notation to normal / template path
        if '/' not in templatename and '.' not in templatename:
            templatename = '/' + templatename.replace('.', '/') + '.' + self.extension

        # Lookup template
        return self.lookup.get_template(templatename)

    def render(self, info, format="html", fragment=False, template=None):
        if isinstance(template, basestring):
            template = self.load_template(template)

        # Load extra vars func if provided
        if self.extra_vars_func:
            info.update(self.extra_vars_func())

        return template.render(**info)

