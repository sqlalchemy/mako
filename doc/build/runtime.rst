.. _runtime_toplevel:

=============================
The Mako Runtime Environment 
=============================

This section describes a little bit about the objects and
built-in functions that are available in templates.

.. _context:

Context
=======

The :class:`.Context` is the central object that is created when
a template is first executed, and is responsible for handling
all communication with the outside world.  Within the template
environment, it is available via the name ``context``.  The :class:`.Context`
includes two
major components, one of which is the output buffer, which is a
file-like object such as Python's ``StringIO`` or similar, and
the other a dictionary of variables that can be freely
referenced within a template; this dictionary is a combination
of the arguments sent to the :meth:`~.Template.render` function and
some built-in variables provided by Mako's runtime environment.

The Buffer
----------

The buffer is stored within the :class:`.Context`, and writing
to it is achieved by calling the :meth:`~.Context.write` method -
in a template this looks like ``context.write('some string')``.
You usually don't need to care about this, as all text within a template, as
well as all expressions provided by ``${}``, automatically send
everything to this method. The cases you might want to be aware
of its existence are if you are dealing with various
filtering/buffering scenarios, which are described in
:ref:`filtering_toplevel`, or if you want to programmatically
send content to the output stream, such as within a ``<% %>``
block.

.. sourcecode:: mako

    <%
        context.write("some programmatic text")
    %>

The actual buffer may or may not be the original buffer sent to
the :class:`.Context` object, as various filtering/caching
scenarios may "push" a new buffer onto the context's underlying
buffer stack. For this reason, just stick with
``context.write()`` and content will always go to the topmost
buffer.

Context Variables
------------------

When your template is compiled into a Python module, the body
content is enclosed within a Python function called
``render_body``. Other top-level defs defined in the template are
defined within their own function bodies which are named after
the def's name with the prefix ``render_`` (i.e. ``render_mydef``).
One of the first things that happens within these functions is
that all variable names that are referenced within the function
which are not defined in some other way (i.e. such as via
assignment, module level imports, etc.) are pulled from the
:class:`.Context` object's dictionary of variables. This is how you're
able to freely reference variable names in a template which
automatically correspond to what was passed into the current
:class:`.Context`.

* **What happens if I reference a variable name that is not in
  the current context?** - the value you get back is a special
  value called ``UNDEFINED``, or if the ``strict_undefined=True`` flag
  is used a ``NameError`` is raised. ``UNDEFINED`` is just a simple global
  variable with the class ``mako.runtime.Undefined``. The
  ``UNDEFINED`` object throws an error when you call ``str()`` on
  it, which is what happens if you try to use it in an
  expression.
* **UNDEFINED makes it hard for me to find what name is missing** - An alternative 
  introduced in version 0.3.6 is to specify the option
  ``strict_undefined=True``
  to the :class:`.Template` or :class:`.TemplateLookup`.   This will cause
  any non-present variables to raise an immediate ``NameError``
  which includes the name of the variable in its message
  when :meth:`~.Template.render` is called - ``UNDEFINED`` is not used.
* **Why not just return None?** Using ``UNDEFINED``, or 
  raising a ``NameError`` is more
  explicit and allows differentiation between a value of ``None``
  that was explicitly passed to the :class:`.Context` and a value that
  wasn't present at all.
* **Why raise an exception when you call str() on it ? Why not
  just return a blank string?** - Mako tries to stick to the
  Python philosophy of "explicit is better than implicit". In
  this case, its decided that the template author should be made
  to specifically handle a missing value rather than
  experiencing what may be a silent failure. Since ``UNDEFINED``
  is a singleton object just like Python's ``True`` or ``False``,
  you can use the ``is`` operator to check for it:

 .. sourcecode:: mako
 
        % if someval is UNDEFINED:
            someval is: no value
        % else:
            someval is: ${someval}
        % endif
 
Another facet of the :class:`.Context` is that its dictionary of
variables is **immutable**. Whatever is set when
:meth:`~.Template.render` is called is what stays. Of course, since
its Python, you can hack around this and change values in the
context's internal dictionary, but this will probably will not
work as well as you'd think. The reason for this is that Mako in
many cases creates copies of the :class:`.Context` object, which
get sent to various elements of the template and inheriting
templates used in an execution. So changing the value in your
local :class:`.Context` will not necessarily make that value
available in other parts of the template's execution. Examples
of where Mako creates copies of the :class:`.Context` include
within top-level def calls from the main body of the template
(the context is used to propagate locally assigned variables
into the scope of defs; since in the template's body they appear
as inlined functions, Mako tries to make them act that way), and
within an inheritance chain (each template in an inheritance
chain has a different notion of ``parent`` and ``next``, which
are all stored in unique :class:`.Context` instances).

* **So what if I want to set values that are global to everyone
  within a template request?** - All you have to do is provide a
  dictionary to your :class:`.Context` when the template first
  runs, and everyone can just get/set variables from that. Lets
  say its called ``attributes``.

  Running the template looks like:

  .. sourcecode:: python

      output = template.render(attributes={})

  Within a template, just reference the dictionary:

  .. sourcecode:: mako

      <%
          attributes['foo'] = 'bar'
      %>
      'foo' attribute is: ${attributes['foo']}
 
* **Why can't "attributes" be a built-in feature of the
  Context?** - This is an area where Mako is trying to make as
  few decisions about your application as it possibly can.
  Perhaps you don't want your templates to use this technique of
  assigning and sharing data, or perhaps you have a different
  notion of the names and kinds of data structures that should
  be passed around. Once again Mako would rather ask the user to
  be explicit.

Context Methods and Accessors
------------------------------

Significant members off of :class:`.Context` include:

* ``context[key]`` / ``context.get(key, default=None)`` -
  dictionary-like accessors for the context. Normally, any
  variable you use in your template is automatically pulled from
  the context if it isnt defined somewhere already. Use the
  dictionary accessor and/or ``get`` method when you want a
  variable that *is* already defined somewhere else, such as in
  the local arguments sent to a %def call. If a key is not
  present, like a dictionary it raises ``KeyError``.
* ``keys()`` - all the names defined within this context.
* ``kwargs`` - this returns a **copy** of the context's
  dictionary of variables. This is useful when you want to
  propagate the variables in the current context to a function
  as keyword arguments, i.e.:

.. sourcecode:: mako

        ${next.body(**context.kwargs)}

* ``write(text)`` - write some text to the current output
  stream.
* ``lookup`` - returns the :class:`.TemplateLookup` instance that is
  used for all file-lookups within the current execution (even
  though individual :class:`.Template` instances can conceivably have
  different instances of a :class:`.TemplateLookup`, only the
  :class:`.TemplateLookup` of the originally-called :class:`.Template` gets
  used in a particular execution).

All the built-in names
======================

A one-stop shop for all the names Mako defines. Most of these
names are instances of :class:`.Namespace`, which are described
in the next section, :ref:`namespaces_toplevel`. Also, most of
these names other than :class:`.Context` and ``UNDEFINED`` are
also present *within* the :class:`.Context` itself.

* ``context`` - this is the :class:`.Context` object, introduced
  at :ref:`context`.
* ``local`` - the namespace of the current template, described
  in :ref:`namespaces_builtin`.
* ``self`` - the namespace of the topmost template in an
  inheritance chain (if any, otherwise the same as ``local``),
  mostly described in :ref:`inheritance_toplevel`.
* ``parent`` - the namespace of the parent template in an
  inheritance chain (otherwise undefined); see
  :ref:`inheritance_toplevel`.
* ``next`` - the namespace of the next template in an
  inheritance chain (otherwise undefined); see
  :ref:`inheritance_toplevel`.
* ``caller`` - a "mini" namespace created when using the
  ``<%call>`` tag to define a "def call with content"; described
  in :ref:`defs_with_content`.
* ``capture`` - a function that calls a given def and captures
  its resulting content into a string, which is returned. Usage
  is described in :ref:`filtering_toplevel`.
* ``UNDEFINED`` - a global singleton that is applied to all
  otherwise uninitialized template variables that were not
  located within the :class:`.Context` when rendering began,
  unless the :class:`.Template` flag ``strict_undefined`` 
  is set to ``True``. ``UNDEFINED`` is
  an instance of :class:`.Undefined`, and raises an
  exception when its ``__str__()`` method is called.
* ``pageargs`` - this is a dictionary which is present in a
  template which does not define any \**kwargs section in its
  ``<%page>`` tag. All keyword arguments sent to the ``body()``
  function of a template (when used via namespaces) go here by
  default unless otherwise defined as a page argument. If this
  makes no sense, it shouldn't; read the section
  :ref:`namespaces_body`.

API Reference
==============

.. autoclass:: mako.runtime.Context
    :show-inheritance:
    :members:

.. autoclass:: mako.runtime.Undefined
    :show-inheritance:
 


