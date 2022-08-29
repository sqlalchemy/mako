.. change::
    :tags: bug, lexer
    :tickets: 366

    Fixed issue in lexer where the regexp used to match tags would not
    correctly interpret quoted sections individually. While this parsing issue
    still produced the same expected tag structure later on, the mis-handling
    of quoted sections was also subject to a regexp crash if a tag had a large
    number of quotes within its quoted sections.