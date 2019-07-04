.. change::
    :tags: feature, template

    The ``n`` filter is now supported in the ``<%page>`` tag.  This allows a
    template to omit the default expression filters throughout a whole
    template, for those cases where a template-wide filter needs to have
    default filtering disabled.  Pull request courtesy Martin von Gagern.

    .. seealso::

        :ref:`expression_filtering_nfilter`


