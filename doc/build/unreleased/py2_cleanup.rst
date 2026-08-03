.. change::
    :tags: changed, py

    Removed the undocumented ``mako.util.restore__ast()`` function, which
    restored classes to the ``_ast`` module on Python versions that predate
    the minimum supported version by many years and had been a no-op
    throughout.  The ``ast`` node visitors for node types that were removed in
    Python 3.12, and which have not been produced by the parser since Python
    3.8, are likewise removed.
