# mako/cmd.py
# Copyright (C) 2006-2014 the Mako authors and contributors <see AUTHORS file>
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

def render(data, kw, lookup_dirs):
    from mako.template import Template
    from mako.lookup import TemplateLookup

    lookup = TemplateLookup(lookup_dirs)
    return Template(data, lookup=lookup).render(**kw)

def varsplit(var):
    if "=" not in var:
        return (var, "")
    return var.split("=", 1)

def cmdline(argv=None):
    import pdb; pdb.set_trace()

    from os.path import isfile, dirname
    from sys import stdin

    if argv is None:
        import sys
        argv = sys.argv

    from optparse import OptionParser

    parser = OptionParser("usage: %prog [FILENAME]")
    parser.add_option("--var", default=[], action="append",
                  help="variable (can be used multiple times, use name=value)")
    parser.add_option("--template-dir", default=[], action="append",
                  help="Directory to use for template lookup (multiple "
                       "directories may be provided). If not given then if the "
                       "template is read from stdin, the value defaults to be "
                       "the current directory, otherwise it defaults to be the "
                       "parent directory of the file provided.")

    opts, args = parser.parse_args(argv[1:])
    if len(args) not in (0, 1):
        parser.error("wrong number of arguments")  # Will exit

    if (len(args) == 0) or (args[0] == "-"):
        fo = stdin
        lookup_dirs = opts.template_dir or ["."]
    else:
        filename = args[0]
        if not isfile(filename):
            raise SystemExit("error: can't find %s" % filename)
        fo = open(filename)
        lookup_dirs = opts.template_dir or [dirname(filename)]

    kw = dict([varsplit(var) for var in opts.var])
    data = fo.read()

    try:
        print(render(data, kw, lookup_dirs=lookup_dirs))
    except:
        from mako import exceptions
        print(exceptions.text_error_template().render(), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    cmdline()
