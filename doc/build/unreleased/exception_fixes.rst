.. change::
    :tags: bug, exceptions
    :tickets: 430, 245, 428

    A series of fixes involving syntax warnings and exceptions found
    during template lexing / compilation:

    * Warnings raised while a template is compiled, which in practice means
      ``SyntaxWarning``, now report the filename and line number of the
      template rather than a line within the generated module, and are no
      longer reported twice.  This applies equally to templates compiled from a
      string, from a file, and to a module file in a
      :paramref:`.Template.module_directory`, as does a warning raised while
      the module level code of a ``<%! %>`` block runs.  Warnings raised while
      a template renders continue to report the location within the generated
      module.

      To do this, Mako replaces ``warnings.showwarning`` while a template is
      compiled.  As that name is global to the process, an unrelated warning
      displayed by another thread during that window may also be passed through
      Mako's hook, which shows any warning it does not recognize unchanged.
      (:ticket:`430`)

    * The ``SyntaxException`` raised for a syntax error in Python code spanning
      several lines of a template, such as that within a ``<% %>`` or ``<%! %>``
      block, is now reported against the line the error is on, rather than
      against the line on which the block begins.  The line reported for code
      that occupies a single line, such as an expression or a control line, is
      unchanged. (:ticket:`245`)

    * The ``SyntaxException`` raised for a tag or expression that is never
      closed is now reported against the line the construct begins on, rather
      than the point at which the search for the closing token gave up, which
      for an unclosed construct is the end of the template.  The message of the
      exception is amended to indicate that the position given is where the
      unterminated construct begins. (:ticket:`428`)



