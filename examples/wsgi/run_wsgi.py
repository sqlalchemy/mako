#!/usr/bin/python
import mimetypes
import os
import posixpath
import re

import urllib.parse

from mako import exceptions
from mako.lookup import TemplateLookup

root = "./"
port = 8000

lookup = TemplateLookup(
    directories=[root + "templates", root + "htdocs"],
    filesystem_checks=True,
    module_directory="./modules",
    # even better would be to use 'charset' in start_response
    output_encoding="ascii",
    encoding_errors="replace",
)


def parse_form_data(environ):
    """eplacement for parsing 'GET' data in cgi.FieldStorage"""
    query_string = environ.get('QUERY_STRING', '')
    form_data = urllib.parse.parse_qs(query_string, keep_blank_values=True)
    return {k: v[0] if len(v) == 1 else v for k, v in form_data.items()}


def serve(environ, start_response):
    """serves requests using the WSGI callable interface."""
    d = parse_form_data(environ)

    uri = environ.get("PATH_INFO", "/")
    if not uri:
        uri = "/index.html"
    else:
        uri = re.sub(r"^/$", "/index.html", uri)

    if re.match(r".*\.html$", uri):
        try:
            template = lookup.get_template(uri)
        except exceptions.TopLevelLookupException:
            start_response("404 Not Found", [])
            return [str.encode("Cant find template '%s'" % uri)]

        start_response("200 OK", [("Content-type", "text/html")])

        try:
            return [template.render(**d)]
        except:
            return [exceptions.html_error_template().render()]
    else:
        u = re.sub(r"^\/+", "", uri)
        filename = os.path.join(root, u)
        if os.path.isfile(filename):
            start_response("200 OK", [("Content-type", guess_type(uri))])
            with open(filename, "rb") as f:
                return [f.read()]
        else:
            start_response("404 Not Found", [])
            return [str.encode("File not found: '%s'" % filename)]


extensions_map = mimetypes.types_map.copy()


def guess_type(path):
    """return a mimetype for the given path based on file extension."""
    base, ext = posixpath.splitext(path)
    if ext in extensions_map:
        return extensions_map[ext]
    ext = ext.lower()
    if ext in extensions_map:
        return extensions_map[ext]
    else:
        return "text/html"


if __name__ == "__main__":
    import wsgiref.simple_server

    server = wsgiref.simple_server.make_server("", port, serve)
    print("Server listening on port %d" % port)
    server.serve_forever()
