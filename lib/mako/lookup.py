# lookup.py
# Copyright (C) 2006 Michael Bayer mike_mp@zzzcomputing.com
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

import posixpath
import os
from mako import exceptions
from mako.template import Template

class TemplateCollection(object):
    def has_template(self, uri):
        try:
            self.get_template(uri)
            return True
        except exceptions.TemplateLookupException, e:
            return False
    def get_template(self, uri):
        raise NotImplementedError()
        
class TemplateLookup(TemplateCollection):
    def __init__(self, directories=None, module_directory=None, filesystem_checks=True, collection_size=-1, format_exceptions=False, error_handler=None, output_encoding=None):
        self.directories = directories or []
        self.module_directory = module_directory
        self.filesystem_checks = filesystem_checks
        self.collection_size = collection_size
        self.template_args = {'format_exceptions':format_exceptions, 'error_handler':error_handler, 'output_encoding':output_encoding}
        self._collection = {}
    def get_template(self, uri):
        try:
            return self._collection[uri]
        except KeyError:
            for dir in self.directories:
                srcfile = posixpath.join(dir, uri)
                if os.access(srcfile, os.F_OK):
                    self._collection[uri] = Template(file(srcfile).read(), description=uri, filename=srcfile, lookup=self, **self.template_args)
                    return self._collection[uri]
            else:
                raise exceptions.TemplateLookupException("Cant locate template for uri '%s'" % uri)
    def put_string(self, uri, text):
        self._collection[uri] = Template(text, lookup=self, description=uri, **self.template_args)
    def put_template(self, uri, template):
        self._collection[uri] = template