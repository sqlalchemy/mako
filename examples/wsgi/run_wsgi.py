from wsgiutils import wsgiServer
import cgi, sys
from mako.lookup import TemplateLookup
from mako import exceptions

lookup = TemplateLookup(directories=['./'], filesystem_checks=True)

def serve(environ, start_response):
    fieldstorage = cgi.FieldStorage(
            fp = environ['wsgi.input'],
            environ = environ,
            keep_blank_values = True
    )
    d = dict([(k, getfield(fieldstorage[k])) for k in fieldstorage])

    uri = environ.get('PATH_INFO', '/')
    try:
        template = lookup.get_template(uri)
        start_response("200 OK", [('Content-type','text/html')])
        return [template.render(**d)]
    except exceptions.TemplateLookupException:
        start_response("404 Not Found", [])
        return ["Cant find template '%s'" % uri]
    except:
        start_response("200 OK", [('Content-type','text/html')])
        error_template = exceptions.html_error_template(lookup)
        return [error_template.render()]

def getfield(f):
    if isinstance(f, list):
        return [getfield(x) for x in f]
    else:
        return f.value
            
if __name__ == '__main__':
    server = wsgiServer.WSGIServer (('localhost', 8000), {'/': serve})
    print "Server listening on port 8000"
    server.serve_forever()


