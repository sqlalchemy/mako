# lookup.py
# Copyright (C) 2006 Michael Bayer mike_mp@zzzcomputing.com
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

import os, stat, posixpath, re
from mako import exceptions, util
from mako.template import Template

try:
    import threading
except:
    import dummy_threading as threading
    
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
    def __init__(self, directories=None, module_directory=None, filesystem_checks=False, collection_size=-1, format_exceptions=False, error_handler=None, output_encoding=None):
        self.directories = directories or []
        self.module_directory = module_directory
        self.filesystem_checks = filesystem_checks
        self.collection_size = collection_size
        self.template_args = {'format_exceptions':format_exceptions, 'error_handler':error_handler, 'output_encoding':output_encoding}
        if collection_size == -1:
            self.__collection = {}
        else:
            self.__collection = util.LRUCache(collection_size)
        self._mutex = threading.Lock()
        
    def get_template(self, uri):
        try:
            if self.filesystem_checks:
                return self.__check(uri, self.__collection[uri])
            else:
                return self.__collection[uri]
        except KeyError:
            self._mutex.acquire()
            try:
                try:
                    return self.__collection[uri]
                except KeyError:
                    for dir in self.directories:
                        srcfile = posixpath.join(dir, uri)
                        if os.access(srcfile, os.F_OK):
                            return self.__load(srcfile, uri)
                    else:
                        raise exceptions.TemplateLookupException("Cant locate template for uri '%s'" % uri)
            finally:
                self._mutex.release()

    def __ident_from_uri(self, uri):
        return re.sub(r"\W", "_", uri)
        
    def __load(self, filename, uri):
        try:
            self.__collection[uri] = Template(file(filename).read(), identifier=self.__ident_from_uri(uri), description=uri, filename=filename, lookup=self, **self.template_args)
            return self.__collection[uri]
        except:
            self.__collection.pop(uri, None)
            raise
            
    def __check(self, uri, template):
        if template.filename is None:
            return template
        if not os.access(template.filename, os.F_OK):
            self.__collection.pop(uri, None)
            raise exceptions.TemplateLookupException("Cant locate template for uri '%s'" % uri)
        elif template.module._modified_time < os.stat(template.filename)[stat.ST_MTIME]:
            return __load(template.filename, uri)
        else:
            return template
            
    def put_string(self, uri, text):
        lock = sync.NameLock(uri)
        lock.acquire()
        try:
            self.__collection[uri] = Template(text, lookup=self, description=uri, **self.template_args)
        finally:
            lock.release()
    def put_template(self, uri, template):
        lock = sync.NameLock(uri)
        lock.acquire()
        try:
            self.__collection[uri] = template
        finally:
            lock.release()
        
            
            