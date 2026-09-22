import contextlib
import ntpath
import os
import posixpath
import tempfile

import pytest

from mako import exceptions
from mako import lookup
from mako import runtime
from mako.template import Template
from mako.testing.assertions import assert_raises_message
from mako.testing.assertions import assert_raises_with_given_cause
from mako.testing.assertions import eq_
from mako.testing.config import config
from mako.testing.helpers import file_with_template_code
from mako.testing.helpers import replace_file_with_dir
from mako.testing.helpers import result_lines
from mako.testing.helpers import rewind_compile_time
from mako.util import FastEncodingBuffer

tl = lookup.TemplateLookup(directories=[config.template_base])


class LookupTest:
    def test_basic(self):
        t = tl.get_template("index.html")
        assert result_lines(t.render()) == ["this is index"]

    def test_subdir(self):
        t = tl.get_template("/subdir/index.html")
        assert result_lines(t.render()) == [
            "this is sub index",
            "this is include 2",
        ]

        assert (
            tl.get_template("/subdir/index.html").module_id
            == "_subdir_index_html"
        )

    def test_updir(self):
        t = tl.get_template("/subdir/foo/../bar/../index.html")
        assert result_lines(t.render()) == [
            "this is sub index",
            "this is include 2",
        ]

    def test_directory_lookup(self):
        """test that hitting an existent directory still raises
        LookupError."""

        assert_raises_with_given_cause(
            exceptions.TopLevelLookupException,
            KeyError,
            tl.get_template,
            "/subdir",
        )

    def test_no_lookup(self):
        t = Template("hi <%include file='foo.html'/>")

        assert_raises_message(
            exceptions.TemplateLookupException,
            "Template 'memory:%s' has no TemplateLookup associated"
            % hex(id(t)),
            t.render,
        )

    def test_uri_adjust(self):
        tl = lookup.TemplateLookup(directories=["/foo/bar"])
        assert (
            tl.filename_to_uri("/foo/bar/etc/lala/index.html")
            == "/etc/lala/index.html"
        )

        tl = lookup.TemplateLookup(directories=["./foo/bar"])
        assert (
            tl.filename_to_uri("./foo/bar/etc/index.html") == "/etc/index.html"
        )

    def test_uri_cache(self):
        """test that the _uri_cache dictionary is available"""
        tl._uri_cache[("foo", "bar")] = "/some/path"
        assert tl._uri_cache[("foo", "bar")] == "/some/path"

    def test_check_not_found(self):
        tl = lookup.TemplateLookup()
        tl.put_string("foo", "this is a template")
        f = tl.get_template("foo")
        assert f.uri in tl._collection
        f.filename = "nonexistent"
        assert_raises_with_given_cause(
            exceptions.TemplateLookupException,
            FileNotFoundError,
            tl.get_template,
            "foo",
        )
        assert f.uri not in tl._collection

    def test_dont_accept_relative_outside_of_root(self):
        """test the mechanics of an include where
        the include goes outside of the path"""
        tl = lookup.TemplateLookup(
            directories=[os.path.join(config.template_base, "subdir")]
        )
        index = tl.get_template("index.html")

        ctx = runtime.Context(FastEncodingBuffer())
        ctx._with_template = index

        assert_raises_message(
            exceptions.TemplateLookupException,
            'Template uri "../index.html" is invalid - it '
            "cannot be relative outside of the root path",
            runtime._lookup_template,
            ctx,
            "../index.html",
            index.uri,
        )

        assert_raises_message(
            exceptions.TemplateLookupException,
            'Template uri "../othersubdir/foo.html" is invalid - it '
            "cannot be relative outside of the root path",
            runtime._lookup_template,
            ctx,
            "../othersubdir/foo.html",
            index.uri,
        )

        # this is OK since the .. cancels out
        runtime._lookup_template(ctx, "foo/../index.html", index.uri)

    @pytest.mark.parametrize(
        "ospath",
        [
            # get_template() converts the configured directory using
            # os.path.sep; forcing posixpath on a Windows host would
            # leave the directory's real backslashes in place and the
            # template would not be located at all, so this half of the
            # matrix only applies where the filesystem is posix
            pytest.param(
                posixpath,
                marks=pytest.mark.skipif(
                    os.name == "nt",
                    reason="posix path semantics need a posix filesystem",
                ),
                id="posix",
            ),
            pytest.param(ntpath, id="windows"),
        ],
    )
    @pytest.mark.parametrize(
        "uri",
        [
            # plain relative traversal
            "../../secrets/creds.txt",
            "/../../secrets/creds.txt",
            # leading slash prefixes; #434
            "//../../secrets/creds.txt",
            "///../../secrets/creds.txt",
            # backslash separators; #435
            "..\\..\\secrets\\creds.txt",
            "\\..\\..\\secrets\\creds.txt",
            # drive designators; #441.  the drive designator itself
            # consumes one level of the posixpath resolution, hence the
            # extra ".." relative to the forms above
            "C:/../../../secrets/creds.txt",
            "c:/../../../secrets/creds.txt",
            "C:\\..\\..\\..\\secrets\\creds.txt",
            "/C:/../../../secrets/creds.txt",
            "//C:/../../../secrets/creds.txt",
        ],
    )
    def test_dont_accept_traversal_outside_of_root(self, uri, ospath):
        """test that no spelling of a traversal URI can bypass the
        path traversal check, on either platform.

        The URIs above are all spellings of the same traversal, and all
        must be refused whether ``os.path`` is ``posixpath`` or
        ``ntpath``; the backslash and drive designator forms are only
        distinguishable from a plain traversal under ``ntpath``.

        """
        with self._traversal_fixture() as tmpl_dir:
            tl = lookup.TemplateLookup(directories=[tmpl_dir])

            current_path = os.path
            os.path = ospath
            try:
                assert_raises_message(
                    exceptions.TemplateLookupException,
                    "cannot be relative outside of the root path",
                    tl.get_template,
                    uri,
                )

                # a template within the root still resolves
                eq_(tl.get_template("index.html").render(), "Hello")
            finally:
                os.path = current_path

    @contextlib.contextmanager
    def _traversal_fixture(self):
        """set up a template directory with a file to be reached outside
        of it, laid out to match the literal URIs used above."""

        with tempfile.TemporaryDirectory() as base:
            tmpl_dir = os.path.join(base, "app", "templates")
            os.makedirs(tmpl_dir)
            with open(os.path.join(tmpl_dir, "index.html"), "w") as f:
                f.write("Hello")

            secret = os.path.join(base, "secrets", "creds.txt")
            os.makedirs(os.path.dirname(secret))
            with open(secret, "w") as f:
                f.write("SECRET_KEY=supersecret123")

            # keep the literal URIs above honest
            eq_(
                os.path.relpath(secret, tmpl_dir).replace(os.sep, "/"),
                "../../secrets/creds.txt",
            )

            yield tmpl_dir

    def test_checking_against_bad_filetype(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tl = lookup.TemplateLookup(directories=[tempdir])
            index_file = file_with_template_code(
                os.path.join(tempdir, "index.html")
            )

            with rewind_compile_time():
                tmpl = Template(filename=index_file)

            tl.put_template("index.html", tmpl)

            replace_file_with_dir(index_file)

            assert_raises_with_given_cause(
                exceptions.TemplateLookupException,
                OSError,
                tl._check,
                "index.html",
                tl._collection["index.html"],
            )
