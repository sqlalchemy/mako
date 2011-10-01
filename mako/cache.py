# mako/cache.py
# Copyright (C) 2006-2011 the Mako authors and contributors <see AUTHORS file>
#
# This module is part of Mako and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

from mako import exceptions


def register_plugin(name, modulename, attrname):
    """Register the given :class:`.CacheImpl` under the given 
    name.

    This is an alternative to using a setuptools-installed entrypoint.

    """
    import pkg_resources
    dist = pkg_resources.get_distribution("mako")
    entry_map = dist.get_entry_map()
    if 'mako.cache' not in entry_map:
        entry_map['mako.cache'] = cache_map = {}
    else:
        cache_map = entry_map['mako.cache']
    cache_map[name] = \
            pkg_resources.EntryPoint.parse('%s = %s:%s' % (name, modulename, attrname), dist=dist)

register_plugin("beaker", "mako.ext.beaker_cache", "BeakerCacheImpl")

class Cache(object):
    """Represents a data content cache made available to the module
    space of a specific :class:`.Template` object.
 
    As of Mako 0.5.1, :class:`.Cache` by itself is mostly a 
    container for a :class:`.CacheImpl` object, which implements
    a fixed API to provide caching services; specific subclasses exist to 
    implement different
    caching strategies.   Mako includes a backend that works with 
    the Beaker caching system.   Beaker itself then supports
    a number of backends (i.e. file, memory, memcached, etc.)

    The construction of a :class:`.Cache` is part of the mechanics
    of a :class:`.Template`, and programmatic access to this
    cache is typically via the :attr:`.Template.cache` attribute.
 
    """

    impl = None
    """Provide the :class:`.CacheImpl` in use by this :class:`.Cache`.

    This accessor allows a :class:`.CacheImpl` with additional
    methods beyond that of :class:`.Cache` to be used programmatically.

    """

    id = None
    """Return the 'id' that identifies this cache.

    This is a value that should be globally unique to the 
    :class:`.Template` associated with this cache, and can
    be used by a caching system to name a local container
    for data specific to this template.

    """

    starttime = None
    """Epochal time value for when the owning :class:`.Template` was
    first compiled.

    A cache implementation may wish to invalidate data earlier than
    this timestamp; this has the effect of the cache for a specific
    :class:`.Template` starting clean any time the :class:`.Template`
    is recompiled, such as when the original template file changed on 
    the filesystem.

    """

    def __init__(self, template):
        self.template = template
        self.impl = self._load_impl(self.template.cache_impl)
        self.id = template.module.__name__
        self.starttime = template.module._modified_time
        self._def_regions = {}

    def _load_impl(self, name):
        import pkg_resources
        for impl in pkg_resources.iter_entry_points(
                                "mako.cache", 
                                name):
            return impl.load()(self)
        else:
            raise exceptions.RuntimeException(
                    "Cache implementation '%s' not present" % 
                    name)

    def get_and_replace(self, key, creation_function, **kw):
        """Retrieve a value from the cache, using the given creation function 
        to generate a new value."""

        if not self.template.cache_enabled:
            return creation_function()

        return self.impl.get_and_replace(key, creation_function, **self._get_cache_kw(kw))

    def put(self, key, value, **kw):
        """Place a value in the cache.
 
        :param key: the value's key.
        :param value: the value
        :param \**kw: cache configuration arguments.
 
        """

        self.impl.put(key, value, **self._get_cache_kw(kw))

    def get(self, key, **kw):
        """Retrieve a value from the cache.
 
        :param key: the value's key.
        :param \**kw: cache configuration arguments.  The 
         backend is configured using these arguments upon first request.
         Subsequent requests that use the same series of configuration
         values will use that same backend.
 
        """
        return self.impl.get(key, **self._get_cache_kw(kw))
 
    def invalidate(self, key, **kw):
        """Invalidate a value in the cache.
 
        :param key: the value's key.
        :param \**kw: cache configuration arguments.  The 
         backend is configured using these arguments upon first request.
         Subsequent requests that use the same series of configuration
         values will use that same backend.
 
        """
        self.impl.invalidate(key, **self._get_cache_kw(kw))
 
    def invalidate_body(self):
        """Invalidate the cached content of the "body" method for this template.
 
        """
        self.invalidate('render_body', __M_defname='render_body')
 
    def invalidate_def(self, name):
        """Invalidate the cached content of a particular <%def> within this template."""
 
        self.invalidate('render_%s' % name, __M_defname='render_%s' % name)
 
    def invalidate_closure(self, name):
        """Invalidate a nested <%def> within this template.
 
        Caching of nested defs is a blunt tool as there is no
        management of scope - nested defs that use cache tags
        need to have names unique of all other nested defs in the 
        template, else their content will be overwritten by 
        each other.
 
        """
 
        self.invalidate(name, __M_defname=name)
 
    def _get_cache_kw(self, kw):
        defname = kw.pop('__M_defname', None)
        if not defname:
            tmpl_kw = self.template.cache_args.copy()
            tmpl_kw.update(kw)
            return tmpl_kw
        elif defname in self._def_regions:
            return self._def_regions[defname]
        else:
            tmpl_kw = self.template.cache_args.copy()
            tmpl_kw.update(kw)
            self._def_regions[defname] = tmpl_kw
            return tmpl_kw

class CacheImpl(object):
    """Provide a cache implementation for use by :class:`.Cache`."""

    def __init__(self, cache):
        self.cache = cache

    def get_and_replace(self, key, creation_function, **kw):
        """Retrieve a value from the cache, using the given creation function 
        to generate a new value.

        This function *must* return a value, either from 
        the cache, or via the given creation function.
        If the creation function is called, the newly 
        created value should be populated into the cache 
        under the given key before being returned.

        :param key: the value's key.
        :param creation_function: function that when called generates
         a new value.
        :param \**kw: cache configuration arguments. 

        """
        raise NotImplementedError()

    def put(self, key, value, **kw):
        """Place a value in the cache.
 
        :param key: the value's key.
        :param value: the value
        :param \**kw: cache configuration arguments.
 
        """
        raise NotImplementedError()
 
    def get(self, key, **kw):
        """Retrieve a value from the cache.
 
        :param key: the value's key.
        :param \**kw: cache configuration arguments. 
 
        """
        raise NotImplementedError()
 
    def invalidate(self, key, **kw):
        """Invalidate a value in the cache.
 
        :param key: the value's key.
        :param \**kw: cache configuration arguments. 
 
        """
        raise NotImplementedError()
