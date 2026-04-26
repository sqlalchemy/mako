"""Assorted runtime unit tests"""

from mako import runtime
from mako.testing.assertions import eq_
from mako.template import Template


class ContextTest:
    def test_locals_kwargs(self):
        c = runtime.Context(None, foo="bar")
        eq_(c.kwargs, {"foo": "bar"})

        d = c._locals({"zig": "zag"})

        # kwargs is the original args sent to the Context,
        # it's intentionally kept separate from _data
        eq_(c.kwargs, {"foo": "bar"})
        eq_(d.kwargs, {"foo": "bar"})

        eq_(d._data["zig"], "zag")

    def test_align_on_code_block_entry_1(self):
        """
        No "\n" in the text before "<%"
        No identation is added before the first character of the written text because the text before "<%" already contains the indentation
        Any "\n" in the written text make the text just after "\n" also indented
        Last character in the written text is "\n" and no indentation is added after the "\n"
        """
        template = Template("""   <% context.write("text 1\\ntext 2\\n", True) %>""")

        assert (
            template.render()
            ==
"""\
   text 1
   text 2
"""
        )

    def test_align_on_code_block_entry_2(self):
        """
        "\n" just before "<%"
        No identation is added before the first character of the written text because the text before "<%" already contains the indentation
        Any "\n" in the written text make the text just after "\n" also indented
        Last character in the written text is not "\n"
        """
        template = Template("""---\n<% context.write("text 1\\ntext 2", True) %>""")

        assert (
            template.render()
            ==
"""\
---
text 1
text 2\
"""
        )

    def test_align_on_code_block_entry_3(self):
        """
        Any characters except "\n" before "<%" are part of the indentation to be taken into account while indenting the written text
        The indentation of "<%" that is taken into account is the indentation in the generated text, not in the template
        Any text written before the next writing with indentation is taken into account for the indentation of this next writing with indentation.
        If this text is longer than the block indentation, then no indentation occurs for the first character of the next writing with indentation.
        """
        template = Template(
"""
Hel\\
lo <%
    context.write("text 1\\ntext 2\\n", True)
    context.write("012")
    context.write("text 3\\n", True)
%>\\
Good ${what} to you <%
    context.write("\\ntext 4\\ntext 5", True)
    context.write("6789")
    context.write("text 6\\ntext 7\\n", True)
%>\\
Bye
"""
        )

        assert (
            template.render(what="day")
            ==
"""
Hello text 1
      text 2
012   text 3
Good day to you 
                text 4
                text 56789text 6
                text 7
Bye
"""
        )
