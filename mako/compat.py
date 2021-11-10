# mako/compat.py
# Copyright 2006-2021 the Mako authors and contributors <see AUTHORS file>
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

import collections
from importlib import util
import inspect
import sys

win32 = sys.platform.startswith("win")
pypy = hasattr(sys, "pypy_version_info")
py38 = sys.version_info >= (3, 8)

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


def load_module(module_id, path):
    spec = util.spec_from_file_location(module_id, path)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exception_as():
    return sys.exc_info()[1]


def exception_name(exc):
    return exc.__class__.__name__


if py38:
    from importlib import metadata as importlib_metadata
else:
    import importlib_metadata  # noqa


def importlib_metadata_get(group):
    ep = importlib_metadata.entry_points()
    if hasattr(ep, "select"):
        return ep.select(group=group)
    else:
        return ep.get(group, ())
