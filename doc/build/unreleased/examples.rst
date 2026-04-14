.. change::
    :tags: usecase, examples

    The ``examples/bench`` folder has been removed as it used mostly
    long-obsolete template engines.  The ``examples/wsgi/run_wsgi.py`` example
    has been updated to remove the use of the removed-in-Python-3.13 ``cgi``
    module, and to be runnable as a module from the project root.
