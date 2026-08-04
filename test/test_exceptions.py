import os
import sys
import tempfile
import traceback
import warnings

import pytest

from mako import exceptions
from mako.lookup import TemplateLookup
from mako.template import Template
from mako.testing.assertions import assert_raises_message
from mako.testing.assertions import eq_
from mako.testing.exclusions import requires_no_pygments_exceptions
from mako.testing.exclusions import requires_pygments_14
from mako.testing.fixtures import TemplateTest
from mako.testing.helpers import result_lines

all_sources = pytest.mark.parametrize(
    "source", ["string", "file", "module_file"]
)


class ExceptionsTest(TemplateTest):
    def test_html_error_template(self):
        """test the html_error_template"""
        code = """
% i = 0
"""
        try:
            template = Template(code)
            template.render_unicode()
            assert False
        except exceptions.CompileException:
            html_error = exceptions.html_error_template().render_unicode()
            assert (
                "CompileException: Fragment &#39;i = 0&#39; is not "
                "a partial control statement at line: 2 char: 1"
            ) in html_error
            assert "<style>" in html_error
            html_error_stripped = html_error.strip()
            assert html_error_stripped.startswith("<html>")
            assert html_error_stripped.endswith("</html>")

            not_full = exceptions.html_error_template().render_unicode(
                full=False
            )
            assert "<html>" not in not_full
            assert "<style>" in not_full

            no_css = exceptions.html_error_template().render_unicode(css=False)
            assert "<style>" not in no_css
        else:
            assert False, (
                "This function should trigger a CompileException, "
                "but didn't"
            )

    def test_text_error_template(self):
        code = """
% i = 0
"""
        try:
            template = Template(code)
            template.render_unicode()
            assert False
        except exceptions.CompileException:
            text_error = exceptions.text_error_template().render_unicode()
            assert "Traceback (most recent call last):" in text_error
            assert (
                "CompileException: Fragment 'i = 0' is not a partial "
                "control statement"
            ) in text_error

    @requires_pygments_14
    def test_utf8_html_error_template_pygments(self):
        """test the html_error_template with a Template containing UTF-8
        chars"""

        code = """# -*- coding: utf-8 -*-
% if 2 == 2: /an error
${'привет'}
% endif
"""
        try:
            template = Template(code)
            template.render_unicode()
        except exceptions.CompileException:
            html_error = exceptions.html_error_template().render()
            assert (
                "CompileException: Fragment &#39;if 2 == 2: /an "
                "error&#39; is not a partial control statement "
                "at line: 2 char: 1"
            ).encode(
                sys.getdefaultencoding(), "htmlentityreplace"
            ) in html_error

            assert (
                "".encode(sys.getdefaultencoding(), "htmlentityreplace")
                in html_error
            )
        else:
            assert False, (
                "This function should trigger a CompileException, "
                "but didn't"
            )

    @requires_no_pygments_exceptions
    def test_utf8_html_error_template_no_pygments(self):
        """test the html_error_template with a Template containing UTF-8
        chars"""

        code = """# -*- coding: utf-8 -*-
% if 2 == 2: /an error
${'привет'}
% endif
"""
        try:
            template = Template(code)
            template.render_unicode()
        except exceptions.CompileException:
            html_error = exceptions.html_error_template().render()
            assert (
                "CompileException: Fragment &#39;if 2 == 2: /an "
                "error&#39; is not a partial control statement "
                "at line: 2 char: 1"
            ).encode(
                sys.getdefaultencoding(), "htmlentityreplace"
            ) in html_error
            assert (
                "${&#39;привет&#39;}".encode(
                    sys.getdefaultencoding(), "htmlentityreplace"
                )
                in html_error
            )
        else:
            assert False, (
                "This function should trigger a CompileException, "
                "but didn't"
            )

    def test_format_closures(self):
        try:
            exec("def foo():" "    raise RuntimeError('test')", locals())
            foo()  # noqa
        except:
            html_error = exceptions.html_error_template().render()
            assert "RuntimeError: test" in str(html_error)

    def test_py_utf8_html_error_template(self):
        try:
            foo = "日本"  # noqa
            raise RuntimeError("test")
        except:
            html_error = exceptions.html_error_template().render()
            assert "RuntimeError: test" in html_error.decode("utf-8")
            assert "foo = &quot;日本&quot;" in html_error.decode(
                "utf-8"
            ) or "foo = &#34;日本&#34;" in html_error.decode("utf-8")

    def test_py_unicode_error_html_error_template(self):
        try:
            raise RuntimeError("日本")
        except:
            html_error = exceptions.html_error_template().render()
            assert "RuntimeError: 日本".encode("ascii", "ignore") in html_error

    @requires_pygments_14
    def test_format_exceptions_pygments(self):
        l = TemplateLookup(format_exceptions=True)

        l.put_string(
            "foo.html",
            """
<%inherit file="base.html"/>
${foobar}
        """,
        )

        l.put_string(
            "base.html",
            """
        ${self.body()}
        """,
        )

        assert (
            '<table class="syntax-highlightedtable">'
            in l.get_template("foo.html").render_unicode()
        )

    @requires_no_pygments_exceptions
    def test_format_exceptions_no_pygments(self):
        l = TemplateLookup(format_exceptions=True)

        l.put_string(
            "foo.html",
            """
<%inherit file="base.html"/>
${foobar}
        """,
        )

        l.put_string(
            "base.html",
            """
        ${self.body()}
        """,
        )

        assert '<div class="sourceline">${foobar}</div>' in result_lines(
            l.get_template("foo.html").render_unicode()
        )

    @requires_pygments_14
    def test_utf8_format_exceptions_pygments(self):
        """test that htmlentityreplace formatting is applied to
        exceptions reported with format_exceptions=True"""

        l = TemplateLookup(format_exceptions=True)
        l.put_string(
            "foo.html", """# -*- coding: utf-8 -*-\n${'привет' + foobar}"""
        )

        assert "&#39;привет&#39;</span>" in l.get_template(
            "foo.html"
        ).render().decode("utf-8")

    @requires_no_pygments_exceptions
    def test_utf8_format_exceptions_no_pygments(self):
        """test that htmlentityreplace formatting is applied to
        exceptions reported with format_exceptions=True"""

        l = TemplateLookup(format_exceptions=True)
        l.put_string(
            "foo.html", """# -*- coding: utf-8 -*-\n${'привет' + foobar}"""
        )

        assert (
            '<div class="sourceline">${&#39;привет&#39; + foobar}</div>'
            in result_lines(
                l.get_template("foo.html").render().decode("utf-8")
            )
        )

    def test_mod_no_encoding(self):
        mod = __import__("test.foo.mod_no_encoding").foo.mod_no_encoding
        try:
            mod.run()
        except:
            t, v, tback = sys.exc_info()
            exceptions.html_error_template().render_unicode(
                error=v, traceback=tback
            )

    def test_custom_tback(self):
        try:
            raise RuntimeError("error 1")
            foo("bar")  # noqa
        except:
            t, v, tback = sys.exc_info()

        try:
            raise RuntimeError("error 2")
        except:
            html_error = exceptions.html_error_template().render_unicode(
                error=v, traceback=tback
            )

        # obfuscate the text so that this text
        # isn't in the 'wrong' exception
        assert (
            "".join(reversed(");touq&rab;touq&(oof")) in html_error
            or "".join(reversed(");43#&rab;43#&(oof")) in html_error
        )

    def test_tback_no_trace_from_py_file(self):
        try:
            t = self._file_template("runtimeerr.html")
            t.render()
        except:
            t, v, tback = sys.exc_info()

        # and don't even send what we have.
        html_error = exceptions.html_error_template().render_unicode(
            error=v, traceback=None
        )

        assert self.indicates_unbound_local_error(html_error, "y")

    def test_tback_trace_from_py_file(self):
        t = self._file_template("runtimeerr.html")
        try:
            t.render()
            assert False
        except:
            html_error = exceptions.html_error_template().render_unicode()

        assert self.indicates_unbound_local_error(html_error, "y")

    def test_code_block_line_number(self):
        l = TemplateLookup()
        l.put_string(
            "foo.html",
            """
<%
msg = "Something went wrong."
raise RuntimeError(msg)  # This is the line.
%>
            """,
        )
        t = l.get_template("foo.html")
        try:
            t.render()
        except:
            text_error = exceptions.text_error_template().render_unicode()
            assert 'File "foo.html", line 4, in render_body' in text_error
            assert "raise RuntimeError(msg)  # This is the line." in text_error
        else:
            assert False

    def test_module_block_line_number(self):
        l = TemplateLookup()
        l.put_string(
            "foo.html",
            """
<%!
def foo():
    msg = "Something went wrong."
    raise RuntimeError(msg)  # This is the line.
%>
${foo()}
            """,
        )
        t = l.get_template("foo.html")
        try:
            t.render()
        except:
            text_error = exceptions.text_error_template().render_unicode()
            assert 'File "foo.html", line 7, in render_body' in text_error
            assert 'File "foo.html", line 5, in foo' in text_error
            assert "raise RuntimeError(msg)  # This is the line." in text_error
        else:
            assert False

    def test_alternating_file_names(self):
        l = TemplateLookup()
        l.put_string(
            "base.html",
            """
<%!
def broken():
    raise RuntimeError("Something went wrong.")
%> body starts here
<%block name="foo">
    ${broken()}
</%block>
            """,
        )
        l.put_string(
            "foo.html",
            """
<%inherit file="base.html"/>
<%block name="foo">
    ${parent.foo()}
</%block>
            """,
        )
        t = l.get_template("foo.html")
        try:
            t.render()
        except:
            text_error = exceptions.text_error_template().render_unicode()
            assert """
  File "base.html", line 5, in render_body
    %> body starts here
  File "foo.html", line 4, in render_foo
    ${parent.foo()}
  File "base.html", line 7, in render_foo
    ${broken()}
  File "base.html", line 4, in broken
    raise RuntimeError("Something went wrong.")
""" in text_error
        else:
            assert False


class TemplateModuleSpecTest(TemplateTest):
    """test that in-memory template modules present a usable ``__spec__``.

    A module made from :class:`types.ModuleType` alone carries a ``__spec__``
    of ``None``, which Python 3.15's :mod:`linecache` reports as a
    :class:`DeprecationWarning` while a traceback is being formatted.

    """

    def test_module_spec_has_loader(self):
        template = Template("hello world")

        spec = template.module.__spec__
        assert spec is not None
        assert spec.loader is not None
        eq_(spec.loader, template.module.__loader__)

    def test_loader_returns_module_source(self):
        template = Template("hello world")

        loader = template.module.__spec__.loader
        eq_(loader.get_source(template.module.__name__), template.code)

    def test_no_warning_formatting_traceback(self):
        """test #437"""

        template = Template("${1 / 0}")

        try:
            template.render()
        except ZeroDivisionError:
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                formatted = traceback.format_exc()
        else:
            assert False

        assert "ZeroDivisionError" in formatted

    def test_traceback_includes_module_source(self):
        """test that generated source lines are available to linecache"""

        template = Template("${1 / 0}")

        try:
            template.render()
        except ZeroDivisionError:
            formatted = traceback.format_exc()
        else:
            assert False

        assert template.module.__name__ in formatted
        assert "__M_writer" in formatted


class CompileWarningsTest(TemplateTest):
    """test that warnings raised while compiling a template report the
    location within the template.

    """

    def _warning_message(self, model):
        """resolve the expected message for a warning.

        ``model`` is a fragment of Python source that raises the same
        warning being tested; the message is taken from the interpreter in
        use, as the wording and category of compiler warnings vary by Python
        version.  A fragment that raises no warning of its own is taken to
        be the message itself.

        """

        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter("always")
            try:
                compile(model, "<test>", "exec")
            except SyntaxError:
                return model

        if recorded:
            return str(recorded[0].message)
        else:
            return model

    def _assert_compile_warnings(
        self,
        text,
        source,
        expected,
        extra_files=None,
        filter_action="always",
        raises=None,
        **kw,
    ):
        """compile ``text`` and assert the warnings that were raised.

        ``source`` is one of "string", "file" or "module_file", so that the
        same assertions can be made however the template was loaded.

        ``expected`` is a list of (filename, lineno, model) tuples, where
        ``model`` is resolved to a message by :meth:`._warning_message`.  The
        template's own filename is given as "<template>", as it is otherwise
        a temporary path, or an id in the case of a template compiled from a
        string; any other filename is given as its base name.

        ``extra_files`` is an optional map of filename to content, written
        alongside the template and importable while it is compiled.

        ``filter_action`` is the warnings filter in effect for the
        compilation.

        ``raises`` is an optional message expected of a
        ``SyntaxException``, for a filter action under which the warning is
        raised rather than shown.

        """

        with tempfile.TemporaryDirectory() as tempdir:
            for name, content in (extra_files or {}).items():
                with open(os.path.join(tempdir, name), "w") as f:
                    f.write(content)

            if extra_files:
                sys.path.insert(0, tempdir)

            try:
                if source == "string":
                    filename = None

                    def _compile():
                        nonlocal filename
                        template = Template(text, **kw)
                        filename = template.uri

                else:
                    filename = os.path.join(tempdir, "warning.mako")
                    with open(filename, "w") as f:
                        f.write(text)

                    if source == "module_file":
                        kw["module_directory"] = os.path.join(
                            tempdir, "modules"
                        )

                    def _compile():
                        Template(filename=filename, **kw)

                with warnings.catch_warnings(record=True) as recorded:
                    warnings.simplefilter(filter_action)
                    if raises is not None:
                        assert_raises_message(
                            exceptions.SyntaxException, raises, _compile
                        )
                    else:
                        _compile()
            finally:
                if extra_files:
                    sys.path.remove(tempdir)
                    for name in extra_files:
                        sys.modules.pop(os.path.splitext(name)[0], None)

        def _filename(warning):
            if warning.filename == filename:
                return "<template>"
            else:
                return os.path.basename(warning.filename)

        eq_(
            [(_filename(w), w.lineno, str(w.message)) for w in recorded],
            [
                (filename, lineno, self._warning_message(model))
                for filename, lineno, model in expected
            ],
        )

    @all_sources
    def test_warning_in_code_block(self, source):
        """test #430"""

        self._assert_compile_warnings(
            'line one\nline two\n<%\n    x = "\\d"\n%>\n',
            source,
            [("<template>", 4, 'x = "\\d"')],
        )

    @all_sources
    def test_warning_line_not_affected_by_preceding_lines(self, source):
        self._assert_compile_warnings(
            "\n" * 10 + '<%\n    x = "\\d"\n%>\n',
            source,
            [("<template>", 12, 'x = "\\d"')],
        )

    @all_sources
    def test_warning_in_module_block_and_expression(self, source):
        self._assert_compile_warnings(
            '<%!\n    x = "\\d"\n%>\n${"\\q"}\n',
            source,
            [
                ("<template>", 2, 'x = "\\d"'),
                ("<template>", 4, '"\\q"'),
            ],
        )

    @all_sources
    @pytest.mark.parametrize(
        "filter_action", ["always", "default", "module", "once"]
    )
    def test_warning_shown_for_each_filter_action(self, source, filter_action):
        """test that the warning survives a filter with a stateful action.

        the occurrence that is dropped is passed over by the filters first,
        so a "once" filter would otherwise record the warning and suppress
        the occurrence that can be translated.

        """

        self._assert_compile_warnings(
            'line one\nline two\n<%\n    x = "\\d"\n%>\n',
            source,
            [("<template>", 4, 'x = "\\d"')],
            filter_action=filter_action,
        )

    @all_sources
    def test_error_filter_raises_from_the_parse(self, source):
        """test that a filter which turns warnings into errors is unchanged.

        The warning is raised as an exception where it is first passed over
        by the filters, which is the parse of the individual expression, and
        so is never shown; the display hook the translation is performed in
        is not reached at all.

        """

        self._assert_compile_warnings(
            'line one\nline two\n<%\n    x = "\\d"\n%>\n',
            source,
            [],
            filter_action="error",
            raises="invalid escape sequence",
        )

    @all_sources
    def test_warning_from_module_level_block(self, source):
        """test that a warning raised as the module level code of a
        <%! %> block runs is reported against the template, the same way
        however the template was loaded.

        """

        self._assert_compile_warnings(
            "<%!\n"
            "    import warnings\n"
            '    warnings.warn("module body", UserWarning)\n'
            "%>\nok\n",
            source,
            [("<template>", 3, "module body")],
        )

    def test_module_source_without_metadata(self):
        """test that a warning is shown untranslated if the metadata of the
        module it is raised for cannot be read, rather than the failure to
        read it displacing the warning

        """

        from mako.template import _translate_module_warnings

        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter("always")
            with _translate_module_warnings(
                lambda: "not a mako module", "the_module", "the_template.mako"
            ):
                warnings.warn_explicit(
                    "unmapped", UserWarning, "the_module", 5
                )

        eq_(
            [(w.filename, w.lineno, str(w.message)) for w in recorded],
            [("the_module", 5, "unmapped")],
        )

    @all_sources
    def test_no_warnings_for_clean_template(self, source):
        self._assert_compile_warnings("hello ${world}\n", source, [])

    @all_sources
    def test_warning_from_imported_module_passes_through(self, source):
        """test that a warning raised by a module imported from the
        template is not translated, or swallowed, along with those raised
        by the compiler itself.

        """

        self._assert_compile_warnings(
            "<%!\n    import mako_test_warns_on_import\n%>\nok\n",
            source,
            [("mako_test_warns_on_import.py", 2, "imported module warning")],
            extra_files={
                "mako_test_warns_on_import.py": (
                    "import warnings\n"
                    "warnings.warn('imported module warning', UserWarning)\n"
                )
            },
        )

    @all_sources
    def test_unknown_filename_warning_from_import_passes_through(self, source):
        """test that a warning raised as the template module executes is
        shown even if it carries the filename used when parsing individual
        expressions.

        """

        self._assert_compile_warnings(
            "<%!\n    import mako_test_warns_unknown\n%>\nok\n",
            source,
            [("<unknown>", 1, "warning from an unknown file")],
            extra_files={
                "mako_test_warns_unknown.py": (
                    "import warnings\n"
                    "warnings.warn_explicit(\n"
                    "    'warning from an unknown file', UserWarning,\n"
                    "    '<unknown>', 1\n"
                    ")\n"
                )
            },
        )


class UnterminatedTagLocationTest(TemplateTest):
    """test that a tag or expression which is never closed is reported
    against the line it begins on.

    tests for #428

    """

    def _assert_syntax_error(self, text, message):
        assert_raises_message(
            exceptions.SyntaxException,
            message,
            Template,
            text,
            filename="foo.mako",
        )

    def test_unterminated_expression(self):
        """test #428"""

        self._assert_syntax_error(
            "one\ntwo\n${ d['x'\n"
            + "".join('line%d "quoted" text\n' % i for i in range(4, 40)),
            r"Expected: \\\|,\}; unterminated tag or expression beginning "
            r"in file 'foo.mako' at line: 3 char: 1",
        )

    def test_unterminated_code_block(self):
        self._assert_syntax_error(
            "one\n<%\n    x = 1\n"
            + "".join('line%d "quoted" text\n' % i for i in range(4, 40)),
            r"Expected: %>; unterminated tag or expression beginning "
            r"in file 'foo.mako' at line: 2 char: 1",
        )

    def test_unterminated_expression_filter(self):
        """the filter of an expression is scanned separately, so the
        position reported is where the filter begins

        """

        self._assert_syntax_error(
            "one\ntwo\nthree\n${ x | trim\n"
            + "".join('line%d "quoted" text\n' % i for i in range(5, 40)),
            r"Expected: \}; unterminated tag or expression beginning "
            r"in file 'foo.mako' at line: 4 char: 6",
        )


class SyntaxExceptionLocationTest(TemplateTest):
    """test that a syntax error in Python code within a template is
    reported against the line it is on.

    tests for #245
    """

    def _assert_syntax_error(self, text, message):
        assert_raises_message(
            exceptions.SyntaxException,
            message,
            Template,
            text,
            filename="foo.mako",
        )

    def test_code_block(self):
        """test #245"""

        self._assert_syntax_error(
            "one\ntwo\nthree\nfour\n<%\n    a = 1\n    b = 2\n    c = (\n%>\n",
            r"\(SyntaxError\) '\(' was never closed .* "
            r"in file 'foo.mako' at line: 8 char: 1",
        )

    def test_code_block_beginning_on_tag_line(self):
        self._assert_syntax_error(
            "one\ntwo\n<% a = 1\nc = ( %>\n",
            r"\(SyntaxError\) '\(' was never closed .* "
            r"in file 'foo.mako' at line: 4 char: 1",
        )

    def test_module_level_block(self):
        self._assert_syntax_error(
            "one\n<%!\n    a = 1\n    c = (\n%>\n",
            r"\(SyntaxError\) '\(' was never closed .* "
            r"in file 'foo.mako' at line: 4 char: 1",
        )

    def test_expression(self):
        self._assert_syntax_error(
            "one\ntwo\n${x +* 1}\nfour\n",
            r"\(SyntaxError\) invalid syntax .* "
            r"in file 'foo.mako' at line: 3 char: 1",
        )

    def test_def_signature(self):
        self._assert_syntax_error(
            'one\n<%def name="d(a b)">\nx\n</%def>\n',
            r"\(SyntaxError\) .* in file 'foo.mako' at line: 2 char: 1",
        )

    def test_control_line_if(self):
        self._assert_syntax_error(
            "one\ntwo\n% if x +* 1:\nb\n% endif\n",
            r"\(SyntaxError\) invalid syntax .* "
            r"in file 'foo.mako' at line: 3 char: 1",
        )

    def test_control_line_elif(self):
        self._assert_syntax_error(
            "one\n% if x:\na\n% elif y +* 1:\nb\n% endif\n",
            r"\(SyntaxError\) invalid syntax .* "
            r"in file 'foo.mako' at line: 4 char: 1",
        )

    def test_control_line_except(self):
        self._assert_syntax_error(
            "one\n% try:\na\n% except (E e):\nb\n% endtry\n",
            r"\(SyntaxError\) .* in file 'foo.mako' at line: 4 char: 1",
        )

    def test_control_line_for(self):
        self._assert_syntax_error(
            "one\ntwo\nthree\n% for x in (:\na\n% endfor\n",
            r"\(SyntaxError\) .* in file 'foo.mako' at line: 4 char: 1",
        )
