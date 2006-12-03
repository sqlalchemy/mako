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
    def get_template(self, uri, relativeto=None):
        raise NotImplementedError()
    def filename_to_uri(self, uri, filename):
        """convert the given filename to a uri relative to this TemplateCollection."""
        return uri
        
    def adjust_uri(self, uri, filename):
        """adjust the given uri based on the calling filename.
        
        when this method is called from the runtime, the 'filename' parameter 
        is taken directly to the 'filename' attribute of the calling 
        template.  Therefore a custom TemplateCollection subclass can place any string 
        identifier desired in the "filename" parameter of the Template objects it constructs
        and have them come back here."""
        return uri
        
class TemplateLookup(TemplateCollection):
    def __init__(self, directories=None, module_directory=None, filesystem_checks=False, collection_size=-1, format_exceptions=False, error_handler=None, output_encoding=None):
        self.directories = [posixpath.normpath(d) for d in directories or []]
        self.module_directory = module_directory
        self.filesystem_checks = filesystem_checks
        self.collection_size = collection_size
        self.template_args = {'format_exceptions':format_exceptions, 'error_handler':error_handler, 'output_encoding':output_encoding, 'module_directory':module_directory}
        if collection_size == -1:
            self.__collection = {}
            self.__uri_convert = {}
        else:
            self.__collection = util.LRUCache(collection_size)
            self.__uri_convert = util.LRUCache(collection_size)
        self._mutex = threading.Lock()
        
    def get_template(self, uri):
        try:
            if self.filesystem_checks:
                return self.__check(uri, self.__collection[uri])
            else:
                return self.__collection[uri]
        except KeyError:
            u = re.sub(r'^\/+', '', uri)
            for dir in self.directories:
                srcfile = posixpath.join(dir, u)
                if os.access(srcfile, os.F_OK):
                    return self.__load(srcfile, uri)
            else:
                raise exceptions.TopLevelLookupException("Cant locate template for uri '%s'" % uri)

    def adjust_uri(self, uri, filename):
        """adjust the given uri based on the calling filename."""
        try:
            return self.__uri_convert[(uri, filename)]
        except KeyError:
            if uri[0] != '/':
                u = posixpath.normpath(uri)
                if filename is not None:
                    rr = self.__relativeize(filename)
                    if rr is not None:
                        u = posixpath.join(posixpath.dirname(rr), u)
                    else:
                        u = posixpath.join('/', u)
                return self.__uri_convert.setdefault((uri, filename), u)
            else:
                return self.__uri_convert.setdefault((uri, filename), uri)
    
    def filename_to_uri(self, filename):
        try:
            return self.__uri_convert[filename]
        except KeyError:
            return self.__uri_convert.setdefault(filename, self.__relativeize(filename))
                    
    def __relativeize(self, filename):
        """return the portion of a filename that is 'relative' to the directories in this lookup."""
        filename = posixpath.normpath(filename)
        for dir in self.directories:
            if filename[0:len(dir)] == dir:
                return filename[len(dir):]
        else:
            return None
            
    def __load(self, filename, uri):
        self._mutex.acquire()
        try:
            try:
                # try returning from collection one more time in case concurrent thread already loaded
                return self.__collection[uri]
            except KeyError:
                pass
            try:
                self.__collection[uri] = Template(identifier=self.__relativeize(filename), description=uri, filename=posixpath.normpath(filename), lookup=self, **self.template_args)
                return self.__collection[uri]
            except:
                self.__collection.pop(uri, None)
                raise
        finally:
            self._mutex.release()
            
    def __check(self, uri, template):
        if template.filename is None:
            return template
        if not os.access(template.filename, os.F_OK):
            self.__collection.pop(uri, None)
            raise exceptions.TemplateLookupException("Cant locate template for uri '%s'" % uri)
        elif template.module._modified_time < os.stat(template.filename)[stat.ST_MTIME]:
            self.__collection.pop(uri, None)
            return self.__load(template.filename, uri)
        else:
            return template
            
    def put_string(self, uri, text):
        self.__collection[uri] = Template(text, lookup=self, description=uri, **self.template_args)
    def put_template(self, uri, template):
        self.__collection[uri] = template
            