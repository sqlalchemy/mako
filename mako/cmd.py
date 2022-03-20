# mako/cmd.py
# Copyright 2006-2021 the Mako authors and contributors <see AUTHORS file>
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php
from argparse import ArgumentParser
from os.path import dirname
from os.path import isfile
import sys

from mako import exceptions
from mako.lookup import TemplateLookup
from mako.template import Template


def varsplit(var):
    if "=" not in var:
        return (var, "")
    return var.split("=", 1)


def _exit():
    sys.stderr.write(exceptions.text_error_template().render())
    sys.exit(1)


def cmdline(argv=None):

    parser = ArgumentParser()
    parser.add_argument(
        "--var",
        default=[],
        action="append",
        help="variable (can be used multiple times, use name=value)",
    )
    parser.add_argument(
        "--template-dir",
        default=[],
        action="append",
        help="Directory to use for template lookup (multiple "
        "directories may be provided). If not given then if the "
        "template is read from stdin, the value defaults to be "
        "the current directory, otherwise it defaults to be the "
        "parent directory of the file provided.",
    )
    parser.add_argument(
        "--output-encoding", default=None, help="force output encoding"
    )
    parser.add_argument(
        "--output-file",
        default=None,
        help="Write to file upon successful render instead of stdout",
    )
    parser.add_argument(
        "--strip-shebang", "-s", action="store_true",
        help="Strip a shebang in the first line of given input file",
    )
    parser.add_argument(
        "--shift-args", "-a", action="store_true",
        help="pass further `args` of this argument parser to the template"
        "as sys.argv - allowing the template to do argparsing again.",
    )
    parser.add_argument("input", nargs="?", default="-",
                        help="file to parse as template. default is stdin.")
    parser.add_argument("args", nargs="*",
                        help=("arguments passed to template's script. "
                              "use '-- args...' when first arg "
                              "starts with - or "))

    options = parser.parse_args(argv)

    output_encoding = options.output_encoding
    output_file = options.output_file

    # strip away mako's original args, so the template can get new args
    # we do this so templates can handle further args on their own
    if options.shift_args:
        saved_sys_argv = sys.argv
        sys.argv = [options.input] + options.args

    if options.input == "-":
        lookup_dirs = options.template_dir or ["."]
        lookup = TemplateLookup(lookup_dirs)
        try:
            template = Template(
                sys.stdin.read(),
                lookup=lookup,
                output_encoding=output_encoding,
            )
        except:
            _exit()
    else:
        filename = options.input
        if not isfile(filename):
            raise SystemExit("error: can't find %s" % filename)
        lookup_dirs = options.template_dir or [dirname(filename)]
        lookup = TemplateLookup(lookup_dirs)

        preprocessor = None
        if options.strip_shebang:
            def preprocessor(content):
                if content.startswith("#!"):
                    lineend = content.find('\n')
                    # without newline after shebang, content will be unchanged
                    content = content[lineend + 1:]
                return content

        try:
            template = Template(
                filename=filename,
                lookup=lookup,
                output_encoding=output_encoding,
                preprocessor=preprocessor,
            )
        except:
            _exit()

    # template rendering args
    kw = {
        "template_argv": options.args,
    } | dict(varsplit(var) for var in options.var)

    try:
        rendered = template.render(**kw)
    except SystemExit:
        pass
    except:
        _exit()
    else:
        if output_file:
            open(output_file, "wt", encoding=output_encoding).write(rendered)
        else:
            sys.stdout.write(rendered)
    finally:
        if options.shift_args:
            sys.argv = saved_sys_argv


if __name__ == "__main__":
    cmdline()
