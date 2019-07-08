.. change::
    :tags: bug, exceptions

    Fixed issue where the correct file URI would not be shown in the
    template-formatted exception traceback if the template filename were not
    known.  Additionally fixes an issue where stale filenames would be
    displayed if a stack trace alternated between different templates.  Pull
    request courtesy Martin von Gagern.

