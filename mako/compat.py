# mako/compat.py
# Copyright 2006-2020 the Mako authors and contributors <see AUTHORS file>
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

import collections
from importlib import util
import inspect
import sys

win32 = sys.platform.startswith("win")
pypy = hasattr(sys, "pypy_version_info")

ArgSpec = collections.namedtuple(
    "ArgSpec", ["args", "varargs", "keywords", "defaults"]
)


def inspect_getargspec(func):
    """getargspec based on fully vendored getfullargspec from Python 3.3."""

    if inspect.ismethod(func):
        func = func.__func__
    if not inspect.isfunction(func):
        raise TypeError("{!r} is not a Python function".format(func))

    co = func.__code__
    if not inspect.iscode(co):
        raise TypeError("{!r} is not a code object".format(co))

    nargs = co.co_argcount
    names = co.co_varnames
    nkwargs = co.co_kwonlyargcount
    args = list(names[:nargs])

    nargs += nkwargs
    varargs = None
    if co.co_flags & inspect.CO_VARARGS:
        varargs = co.co_varnames[nargs]
        nargs = nargs + 1
    varkw = None
    if co.co_flags & inspect.CO_VARKEYWORDS:
        varkw = co.co_varnames[nargs]

    return ArgSpec(args, varargs, varkw, func.__defaults__)


def octal(lit):
    return eval("0o" + lit)


def load_module(module_id, path):
    spec = util.spec_from_file_location(module_id, path)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reraise(tp, value, tb=None, cause=None):
    if cause is not None:
        value.__cause__ = cause
    if value.__traceback__ is not tb:
        raise value.with_traceback(tb)
    raise value


def exception_as():
    return sys.exc_info()[1]


all = all  # noqa


def exception_name(exc):
    return exc.__class__.__name__


################################################
# cross-compatible metaclass implementation
# Copyright (c) 2010-2012 Benjamin Peterson
def with_metaclass(meta, base=object):
    """Create a base class with a metaclass."""
    return meta("%sBase" % meta.__name__, (base,), {})


################################################


def arg_stringname(func_arg):
    """Gets the string name of a kwarg or vararg
    In Python3.4 a function's args are
    of _ast.arg type not _ast.name
    """
    if hasattr(func_arg, "arg"):
        return func_arg.arg
    else:
        return str(func_arg)
