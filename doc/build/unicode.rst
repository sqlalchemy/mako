.. _unicode_toplevel:

===================
The Unicode Chapter
===================

.. note:: this chapter was written many years ago and is very Python-2
   centric. As of Mako 1.1.3, the default template encoding is ``utf-8``.

The Python language supports two ways of representing what we
know as "strings", i.e. series of characters. In Python 2, the
two types are ``string`` and ``unicode``, and in Python 3 they are
``bytes`` and ``string``. A key aspect of the Python 2 ``string`` and
Python 3 ``bytes`` types are that they contain no information
regarding what **encoding** the data is stored in. For this
reason they were commonly referred to as **byte strings** on
Python 2, and Python 3 makes this name more explicit. The
origins of this come from Python's background of being developed
before the Unicode standard was even available, back when
strings were C-style strings and were just that, a series of
bytes. Strings that had only values below 128 just happened to
be **ASCII** strings and were printable on the console, whereas
strings with values above 128 would produce all kinds of
graphical characters and bells.

Contrast the "byte-string" type with the "unicode/string" type.
Objects of this latter type are created whenever you say something like
``u"hello world"`` (or in Python 3, just ``"hello world"``). In this
case, Python represents each character in the string internally
using multiple bytes per character (something similar to
UTF-16). What's important is that when using the
``unicode``/``string`` type to store strings, Python knows the
data's encoding; it's in its own internal format. Whereas when
using the ``string``/``bytes`` type, it does not.

When Python 2 attempts to treat a byte-string as a string, which
means it's attempting to compare/parse its characters, to coerce
it into another encoding, or to decode it to a unicode object,
it has to guess what the encoding is. In this case, it will
pretty much always guess the encoding as ``ascii``... and if the
byte-string contains bytes above value 128, you'll get an error.
Python 3 eliminates much of this confusion by just raising an
error unconditionally if a byte-string is used in a
character-aware context.

There is one operation that Python *can* do with a non-ASCII
byte-string, and it's a great source of confusion: it can dump the
byte-string straight out to a stream or a file, with nary a care
what the encoding is. To Python, this is pretty much like
dumping any other kind of binary data (like an image) to a
stream somewhere. In Python 2, it is common to see programs that
embed all kinds of international characters and encodings into
plain byte-strings (i.e. using ``"hello world"`` style literals)
can fly right through their run, sending reams of strings out to
wherever they are going, and the programmer, seeing the same
output as was expressed in the input, is now under the illusion
that his or her program is Unicode-compliant. In fact, their
program has no unicode awareness whatsoever, and similarly has
no ability to interact with libraries that *are* unicode aware.
Python 3 makes this much less likely by defaulting to unicode as
the storage format for strings.

The "pass through encoded data" scheme is what template
languages like Cheetah and earlier versions of Myghty do by
default. In Python 3 Mako only allows 
usage of native, unicode strings.

In normal Mako operation, all parsed template constructs and
output streams are handled internally as Python ``unicode``
objects. It's only at the point of :meth:`~.Template.render` that this unicode
stream may be rendered into whatever the desired output encoding
is. The implication here is that the template developer must
:ensure that :ref:`the encoding of all non-ASCII templates is explicit
<set_template_file_encoding>` (still required in Python 3),
that :ref:`all non-ASCII-encoded expressions are in one way or another
converted to unicode <handling_non_ascii_expressions>`
(not much of a burden in Python 3), and that :ref:`the output stream of the
template is handled as a unicode stream being encoded to some
encoding <defining_output_encoding>` (still required in Python 3).

.. _set_template_file_encoding:

Specifying the Encoding of a Template File
==========================================

.. versionchanged:: 1.1.3

    As of Mako 1.1.3, the default template encoding is "utf-8".  Previously, a
    Python "magic encoding comment" was required for templates that were not
    using ASCII.

Mako templates support Python's "magic encoding comment" syntax
described in  `pep-0263 <http://www.python.org/dev/peps/pep-0263/>`_:

.. sourcecode:: mako

    ## -*- coding: utf-8 -*-

    Alors vous imaginez ma surprise, au lever du jour, quand
    une drôle de petite voix m’a réveillé. Elle disait:
     « S’il vous plaît… dessine-moi un mouton! »

As an alternative, the template encoding can be specified
programmatically to either :class:`.Template` or :class:`.TemplateLookup` via
the ``input_encoding`` parameter:

.. sourcecode:: python

    t = TemplateLookup(directories=['./'], input_encoding='utf-8')

The above will assume all located templates specify ``utf-8``
encoding, unless the template itself contains its own magic
encoding comment, which takes precedence.

.. _handling_non_ascii_expressions:

Handling Expressions
====================

The next area that encoding comes into play is in expression
constructs. By default, Mako's treatment of an expression like
this:

.. sourcecode:: mako

    ${"hello world"}

looks something like this:

.. sourcecode:: python

    context.write(unicode("hello world"))

In Python 3, it's just:

.. sourcecode:: python

    context.write(str("hello world"))

That is, **the output of all expressions is run through the
``unicode`` built-in**. This is the default setting, and can be
modified to expect various encodings. The ``unicode`` step serves
both the purpose of rendering non-string expressions into
strings (such as integers or objects which contain ``__str()__``
methods), and to ensure that the final output stream is
constructed as a unicode object. The main implication of this is
that **any raw byte-strings that contain an encoding other than
ASCII must first be decoded to a Python unicode object**. It
means you can't say this in Python 2:

.. sourcecode:: mako

    ${"voix m’a réveillé."}  ## error in Python 2!

You must instead say this:

.. sourcecode:: mako

    ${u"voix m’a réveillé."}  ## OK !

Similarly, if you are reading data from a file that is streaming
bytes, or returning data from some object that is returning a
Python byte-string containing a non-ASCII encoding, you have to
explicitly decode to unicode first, such as:

.. sourcecode:: mako

    ${call_my_object().decode('utf-8')}

Note that filehandles acquired by ``open()`` in Python 3 default
to returning "text", that is the decoding is done for you. See
Python 3's documentation for the ``open()`` built-in for details on
this.

If you want a certain encoding applied to *all* expressions,
override the ``unicode`` builtin with the ``decode`` built-in at the
:class:`.Template` or :class:`.TemplateLookup` level:

.. sourcecode:: python

    t = Template(templatetext, default_filters=['decode.utf8'])

Note that the built-in ``decode`` object is slower than the
``unicode`` function, since unlike ``unicode`` it's not a Python
built-in, and it also checks the type of the incoming data to
determine if string conversion is needed first.

The ``default_filters`` argument can be used to entirely customize
the filtering process of expressions. This argument is described
in :ref:`filtering_default_filters`.

.. _defining_output_encoding:

Defining Output Encoding
========================

Now that we have a template which produces a pure unicode output
stream, all the hard work is done. We can take the output and do
anything with it.

As stated in the :doc:`"Usage" chapter <usage>`, both :class:`.Template` and
:class:`.TemplateLookup` accept ``output_encoding`` and ``encoding_errors``
parameters which can be used to encode the output in any Python
supported codec:

.. sourcecode:: python

    from mako.template import Template
    from mako.lookup import TemplateLookup

    mylookup = TemplateLookup(directories=['/docs'], output_encoding='utf-8', encoding_errors='replace')

    mytemplate = mylookup.get_template("foo.txt")
    print(mytemplate.render())

:meth:`~.Template.render` will return a ``bytes`` object in Python 3 if an output
encoding is specified. By default it performs no encoding and
returns a native string.

:meth:`~.Template.render_unicode` will return the template output as a Python
``unicode`` object (or ``string`` in Python 3):

.. sourcecode:: python

    print(mytemplate.render_unicode())

The above method disgards the output encoding keyword argument;
you can encode yourself by saying:

.. sourcecode:: python

    print(mytemplate.render_unicode().encode('utf-8', 'replace'))

Buffer Selection
----------------

Mako does play some games with the style of buffering used
internally, to maximize performance. Since the buffer is by far
the most heavily used object in a render operation, it's
important!

When calling :meth:`~.Template.render` on a template that does not specify any
output encoding (i.e. it's ``ascii``), Python's ``cStringIO`` module,
which cannot handle encoding of non-ASCII ``unicode`` objects
(even though it can send raw byte-strings through), is used for
buffering. Otherwise, a custom Mako class called
``FastEncodingBuffer`` is used, which essentially is a super
dumbed-down version of ``StringIO`` that gathers all strings into
a list and uses ``''.join(elements)`` to produce the final output
-- it's markedly faster than ``StringIO``.
