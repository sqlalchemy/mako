.. change::
    :tags: bug, py3k

    Mako now performs exception chaining using ``raise from``, correctly
    identifying underlying exception conditions when it raises its own
    exceptions. Pull request courtesy Ram Rachum.
