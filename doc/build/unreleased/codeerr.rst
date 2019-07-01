.. change::
    :tags: bug, exceptions

    Improved the line-number tracking for source lines inside of Python  ``<%
    ... %>`` blocks, such that text- and HTML-formatted exception traces such
    as that of  :func:`.html_error_template` now report the correct source line
    inside the block, rather than the first line of the block itself.
    Exceptions in ``<%! ... %>`` blocks which get raised while loading the
    module are still not reported correctly, as these are handled before the
    Mako code is generated.  Pull request courtesy Martin von Gagern.
