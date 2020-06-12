import os
import unittest

from mako.cache import CacheImpl
from mako.cache import register_plugin
from mako.template import Template
from .assertions import eq_


def _ensure_environment_variable(key, fallback):
    env_var = os.getenv(key)
    if env_var is None:
        return fallback
    return env_var


def _get_module_base():
    return _ensure_environment_variable(
        "TEST_MODULE_BASE", os.path.abspath("./test/templates/modules")
    )


def _get_template_base():
    return _ensure_environment_variable(
        "TEST_TEMPLATE_BASE", os.path.abspath("./test/templates/")
    )


module_base = _get_module_base()
template_base = _get_template_base()


class TemplateTest(unittest.TestCase):
    def _file_template(self, filename, **kw):
        filepath = self._file_path(filename)
        return Template(
            uri=filename, filename=filepath, module_directory=module_base, **kw
        )

    def _file_path(self, filename):
        name, ext = os.path.splitext(filename)
        py3k_path = os.path.join(template_base, name + "_py3k" + ext)
        if os.path.exists(py3k_path):
            return py3k_path

        return os.path.join(template_base, filename)

    def _do_file_test(
        self,
        filename,
        expected,
        filters=None,
        unicode_=True,
        template_args=None,
        **kw,
    ):
        t1 = self._file_template(filename, **kw)
        self._do_test(
            t1,
            expected,
            filters=filters,
            unicode_=unicode_,
            template_args=template_args,
        )

    def _do_memory_test(
        self,
        source,
        expected,
        filters=None,
        unicode_=True,
        template_args=None,
        **kw,
    ):
        t1 = Template(text=source, **kw)
        self._do_test(
            t1,
            expected,
            filters=filters,
            unicode_=unicode_,
            template_args=template_args,
        )

    def _do_test(
        self,
        template,
        expected,
        filters=None,
        template_args=None,
        unicode_=True,
    ):
        if template_args is None:
            template_args = {}
        if unicode_:
            output = template.render_unicode(**template_args)
        else:
            output = template.render(**template_args)

        if filters:
            output = filters(output)
        eq_(output, expected)


class PlainCacheImpl(CacheImpl):
    """Simple memory cache impl so that tests which
    use caching can run without beaker."""

    def __init__(self, cache):
        self.cache = cache
        self.data = {}

    def get_or_create(self, key, creation_function, **kw):
        if key in self.data:
            return self.data[key]
        else:
            self.data[key] = data = creation_function(**kw)
            return data

    def put(self, key, value, **kw):
        self.data[key] = value

    def get(self, key, **kw):
        return self.data[key]

    def invalidate(self, key, **kw):
        del self.data[key]


register_plugin("plain", __name__, "PlainCacheImpl")
