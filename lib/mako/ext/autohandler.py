"""adds autohandler functionality to Mako templates"""

import posixpath, os, re

def autohandler(context, _template_filename, name='autohandler'):
    lookup = context.lookup
    uri = lookup.filename_to_uri(_template_filename)
    tokens = list(posixpath.split(posixpath.dirname(uri) + "/" + name))
    if posixpath.basename(uri) == name:
        tokens[-2:] = [name]
    while len(tokens):
        path = posixpath.join(*tokens)
        psub = re.sub(r'^/', '',path)
        print "TOKENS", tokens
        for d in lookup.directories:
            print "FILE", posixpath.join(d, psub)
            if os.access(posixpath.join(d, psub), os.F_OK):
                return path
        if len(tokens) == 1:
            break
        tokens[-2:] = [name]
        print "NOW THE TOKENS ARE:", tokens