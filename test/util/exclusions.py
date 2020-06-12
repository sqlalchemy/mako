import unittest

from mako.util import update_wrapper


def skip_if(predicate, reason=None):
    """Skip a test if predicate is true."""
    reason = reason or predicate.__name__

    def decorate(fn):
        fn_name = fn.__name__

        def maybe(*args, **kw):
            if predicate():
                msg = "'%s' skipped: %s" % (fn_name, reason)
                raise unittest.SkipTest(msg)
            else:
                return fn(*args, **kw)

        return update_wrapper(maybe, fn)

    return decorate


def requires_pygments_14(fn):
    try:
        import pygments

        version = pygments.__version__
    except:
        version = "0"
    return skip_if(
        lambda: version < "1.4", "Requires pygments 1.4 or greater"
    )(fn)


def requires_no_pygments_exceptions(fn):
    def go(*arg, **kw):
        from mako import exceptions

        exceptions._install_fallback()
        try:
            return fn(*arg, **kw)
        finally:
            exceptions._install_highlighting()

    return update_wrapper(go, fn)
