"""adds autohandler functionality to Mako templates"""

import posixpath, os, re

def autohandler(context, _template_filename, name='autohandler'):
    lookup = context.lookup
    
    if not lookup.filesystem_checks:
        try:
            return lookup._uri_cache[(autohandler, _template_filename, name)]
        except KeyError:
            pass

    uri = lookup.filename_to_uri(_template_filename)
    tokens = re.findall(r'([^/]+)', posixpath.dirname(uri)) + [name]
    while len(tokens):
        path = '/' + '/'.join(tokens)
        if path != uri and _file_exists(lookup, path):
            if not lookup.filesystem_checks:
                return lookup._uri_cache.setdefault((autohandler, _template_filename, name), path)
            else:
                return path
        if len(tokens) == 1:
            break
        tokens[-2:] = [name]
        
    if not lookup.filesystem_checks:
        return lookup._uri_cache.setdefault((autohandler, _template_filename, name), None)
    else:
        return None

def _file_exists(lookup, path):
    psub = re.sub(r'^/', '',path)
    for d in lookup.directories:
        if os.access(d + '/' + psub, os.F_OK):
            return True
    else:
        return False
    