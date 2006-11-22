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
    def __init__(self, directories=None, module_directory=None, filesystem_checks=True, collection_size=-1):
        self.directories = directories or []
        self.module_directory = module_directory
        self.filesystem_checks = filesystem_checks
        self.collection_size = collection_size
        self._collection = {}
    def get_template(self, uri):
        try:
            return self._collection[uri]
        except KeyError:
            for dir in self.directories:
                srcfile = posixpath.join(dir, uri)
                if os.access(srcfile, os.F_OK):
                    self._collection[uri] = Template(file(srcfile).read(), lookup=self)
                    return self._collection[uri]
            else:
                raise exceptions.TemplateLookupException("Cant locate template for uri '%s'" % uri)
                
