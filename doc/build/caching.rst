.. _caching_toplevel:

========
Caching
========

Any template or component can be cached using the ``cache``
argument to the ``<%page>``, ``<%def>`` or ``<%block>`` directives:

.. sourcecode:: mako

    <%page cached="True"/>
 
    template text
 
The above template, after being executed the first time, will
store its content within a cache that by default is scoped
within memory. Subsequent calls to the template's :meth:`~.Template.render`
method will return content directly from the cache. When the
:class:`.Template` object itself falls out of scope, its corresponding
cache is garbage collected along with the template.

By default, caching requires that the ``beaker`` package be installed on the
system, however the mechanism of caching can be customized to use 
any third party or user defined system - see :ref:`cache_plugins`.

In addition to being available on the ``<%page>`` tag, the caching flag and all 
its options can be used with the ``<%def>`` tag as well:

.. sourcecode:: mako

    <%def name="mycomp" cached="True" cache_timeout="30" cache_type="memory">
        other text
    </%def>

... and equivalently with the ``<%block>`` tag, anonymous or named:

.. sourcecode:: mako

    <%block cached="True" cache_timeout="30" cache_type="memory">
        other text
    </%block>

Cache arguments
================

The various cache arguments are cascaded from their default
values, to the arguments specified programmatically to the
:class:`.Template` or its originating :class:`.TemplateLookup`, then to those
defined in the ``<%page>`` tag of an individual template, and
finally to an individual ``<%def>`` or ``<%block>`` tag within the template. This
means you can define, for example, a cache type of ``dbm`` on your
:class:`.TemplateLookup`, a cache timeout of 60 seconds in a particular
template's ``<%page>`` tag, and within one of that template's
``<%def>`` tags ``cache=True``, and that one particular def will
then cache its data using a ``dbm`` cache and a data timeout of 60
seconds.

The caching options always available include:

* ``cached="False|True"`` - turn caching on
* ``cache_key`` - the "key" used to uniquely identify this content
  in the cache.  The total namespace of keys within the cache is
  local to the current template, and the default value of "key"
  is the name of the def which is storing its data. It is an
  evaluable tag, so you can put a Python expression to calculate
  the value of the key on the fly. For example, heres a page
  that caches any page which inherits from it, based on the
  filename of the calling template:
 
.. sourcecode:: mako

    <%page cached="True" cache_key="${self.filename}"/>

    ${next.body()}
 
    ## rest of template

As of 0.5.1, the ``<%page>``, ``<%def>``, and ``<%block>`` tags 
accept any named argument that starts with the prefix ``"cache_"``.
Those arguments are then packaged up and passed along to the
underlying caching implementation, minus the ``"cache_"`` prefix.

On :class:`.Template` and :class:`.TemplateLookup`, these additional
arguments are accepted:

* ``cache_impl`` - Name of the caching implementation to use, defaults
  to ``beaker``.  New in 0.5.1.
* ``cache_args`` - dictionary of default arguments to send to the 
  caching system.  The arguments specified on the ``<%page>``, ``<%def>``,
  and ``<%block>`` tags will supersede what is specified in this dictionary.
  The names in the dictionary should not have the ``cache_`` prefix.
  New in 0.5.1.

Prior to version 0.5.1, the following arguments were instead used.  Note
these arguments remain available and are copied into the newer ``cache_args``
dictionary when present on :class:`.Template` or :class:`.TemplateLookup`:

* ``cache_dir`` - Equivalent to the ``dir`` argument in the ``cache_args``
  dictionary.  See the section on Beaker cache options for a description
  of this argument.
* ``cache_url`` - Equivalent to the ``url`` argument in the ``cache_args``
  dictionary.  See the section on Beaker cache options for a description
  of this argument.
* ``cache_type`` - Equivalent to the ``type`` argument in the ``cache_args``
  dictionary.  See the section on Beaker cache options for a description
  of this argument.
* ``cache_timeout`` - Equivalent to the ``timeout`` argument in the ``cache_args``
  dictionary.  See the section on Beaker cache options for a description
  of this argument.

Beaker Cache Options
---------------------

When using the default caching implementation based on Beaker,
the following options are also available
on the ``<%page>``, ``<%def>``, and ``<%block>`` tags, as well
as within the ``cache_args`` dictionary of :class:`.Template` and
:class:`.TemplateLookup` without the ``"cache_"`` prefix:

* ``cache_timeout`` - number of seconds in which to invalidate the
  cached data.  After this timeout, the content is re-generated
  on the next call.  Available as ``timeout`` in the ``cache_args``
  dictionary.
* ``cache_type`` - type of caching. ``memory``, ``file``, ``dbm``, or
  ``memcached``.  Available as ``type`` in the ``cache_args`` 
  dictionary.
* ``cache_url`` - (only used for ``memcached`` but required) a single
  IP address or a semi-colon separated list of IP address of
  memcache servers to use.  Available as ``url`` in the ``cache_args``
  dictionary.
* ``cache_dir`` - In the case of the ``file`` and ``dbm`` cache types,
  this is the filesystem directory with which to store data
  files. If this option is not present, the value of
  ``module_directory`` is used (i.e. the directory where compiled
  template modules are stored). If neither option is available
  an exception is thrown.  Available as ``dir`` in the
  ``cache_args`` dictionary.
 
Accessing the Cache
===================

The :class:`.Template`, as well as any template-derived :class:`.Namespace`, has
an accessor called ``cache`` which returns the ``Cache`` object
for that template. This object is a facade on top of the underlying
:class:`.CacheImpl` object, and provides some very rudimental
capabilities, such as the ability to get and put arbitrary
values:

.. sourcecode:: mako

    <%
        local.cache.put("somekey", type="memory", "somevalue")
    %>
 
Above, the cache associated with the ``local`` namespace is
accessed and a key is placed within a memory cache.

More commonly the ``cache`` object is used to invalidate cached
sections programmatically:

.. sourcecode:: python

    template = lookup.get_template('/sometemplate.html')
 
    # invalidate the "body" of the template
    template.cache.invalidate_body()
 
    # invalidate an individual def
    template.cache.invalidate_def('somedef')
 
    # invalidate an arbitrary key
    template.cache.invalidate('somekey')

You can access any special method or attribute of the :class:`.CacheImpl`
itself using the ``impl`` attribute::

    template.cache.impl.do_something_special()

But note using implementation-specific methods will mean you can't 
swap in a different kind of :class:`.CacheImpl` implementation at a 
later time.

.. _cache_plugins:

Cache Plugins
==============

As of 0.5.1, the mechanism used by caching can be plugged in
using a :class:`.CacheImpl` subclass.    This class implements
the rudimental methods Mako needs to implement the caching
API.   Mako includes the :class:`.BeakerCacheImpl` class to 
provide the default implementation.  A :class:`.CacheImpl` class
is acquired by Mako using a ``pkg_resources`` entrypoint, using 
the name given as the ``cache_impl`` argument to :class:`.Template`
or :class:`.TemplateLookup`.    This entry point can be
installed via the standard setuptools/``setup()`` procedure, underneath
the EntryPoint group named ``"mako.cache"``.  It can also be
installed at runtime via a convenience installer :func:`.register_plugin`
which accomplishes essentially the same task.

An example plugin that implements a local dictionary cache::

    from mako.cache import Cacheimpl, register_plugin

    class SimpleCacheImpl(CacheImpl):
        def __init__(self, cache):
            super(SimpleCacheImpl, self).__init__(cache)
            self._cache = {}

        def get_and_replace(self, key, creation_function, **kw):
            if key in self._cache:
                return self._cache[key]
            else:
                self._cache[key] = value = creation_function()
                return value

        def put(self, key, value, **kwargs):
            self._cache[key] = value
 
        def get(self, key, **kwargs):
            return self._cache.get(key)
 
        def invalidate(self, key, **kwargs):
            self._cache.pop(key, None)

    # optional - register the class locally
    register_plugin("simple", __name__, "SimpleCacheImpl")

Enabling the above plugin in a template would look like::

    t = Template("mytemplate", 
                    file="mytemplate.html", 
                    cache_impl='simple')

Guidelines for writing cache plugins
------------------------------------

* The :class:`.CacheImpl` is created on a per-:class:`.Template` basis.  The 
  class should ensure that only data for the parent :class:`.Template` is
  persisted or returned by the cache methods.    The actual :class:`.Template`
  is available via the ``self.cache.template`` attribute.   The ``self.cache.id``
  attribute, which is essentially the unique modulename of the template, is 
  a good value to use in order to represent a unique namespace of keys specific
  to the template.
* Templates only use the :meth:`.CacheImpl.get_and_replace()` method.  
  The :meth:`.CacheImpl.put`,
  :meth:`.CacheImpl.get`, and :meth:`.CacheImpl.invalidate` methods are 
  only used in response to end-user programmatic access to the corresponding
  methods on the :class:`.Cache` object.
* :class:`.CacheImpl` will be accessed in a multithreaded fashion if the
  :class:`.Template` itself is used multithreaded.  Care should be taken
  to ensure caching implementations are threadsafe.
* A library like `Dogpile <http://pypi.python.org/pypi/Dogpile>`_, which
  is a minimal locking system derived from Beaker, can be used to help
  implement the :meth:`.CacheImpl.get_and_replace` method in a threadsafe
  way that can maximize effectiveness across multiple threads as well
  as processes. :meth:`.CacheImpl.get_and_replace` is the
  key method used by templates.
* All arguments passed to ``**kw`` come directly from the parameters
  inside the ``<%def>``, ``<%block>``, or ``<%page>`` tags directly,
  minus the ``"cache_"`` prefix, as strings, with the exception of 
  the argument ``cache_timeout``, which is passed to the plugin 
  as the name ``timeout`` with the value converted to an integer.
  Arguments present in ``cache_args`` on :class:`.Template` or 
  :class:`.TemplateLookup` are passed directly, but are superseded
  by those present in the most specific template tag.
* The directory where :class:`.Template` places module files can
  be acquired using the accessor ``self.cache.template.module_directory``.
  This directory can be a good place to throw cache-related work
  files, underneath a prefix like "_my_cache_work" so that name
  conflicts with generated modules don't occur.

API Reference
==============

.. autoclass:: mako.cache.Cache
    :members:
    :show-inheritance:

.. autoclass:: mako.cache.CacheImpl
    :members:
    :show-inheritance:    

.. autofunction:: mako.cache.register_plugin

.. autoclass:: mako.ext.beaker_cache.BeakerCacheImpl
    :members:
    :show-inheritance:
