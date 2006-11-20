from cgi import escape
import os
from StringIO import StringIO
import sys
import timeit

__all__ = ['myghty', 'django', 'kid', 'genshi', 'cheetah', 'mako']

def genshi(dirname, verbose=False):
    from genshi.template import TemplateLoader
    loader = TemplateLoader([dirname], auto_reload=False)
    template = loader.load('template.html')
    def render():
        data = dict(title='Just a test', user='joe',
                    items=['Number %d' % num for num in range(1, 15)])
        return template.generate(**data).render('xhtml')

    if verbose:
        print render()
    return render

def myghty(dirname, verbose=False):
    from myghty import interp
    interpreter = interp.Interpreter(component_root=dirname)
    def render():
        data = dict(title='Just a test', user='joe',
                    items=['Number %d' % num for num in range(1, 15)])
        buffer = StringIO()
        interpreter.execute("template.myt", request_args=data, out_buffer=buffer)
        return buffer.getvalue()
    if verbose:
        print render()
    return render

def mako(dirname, verbose=False):
    from mako.template import Template
    from mako.lookup import TemplateLookup
    lookup = TemplateLookup(directories=[dirname])
    template = lookup.get_template('template.html')
    def render():
        return template.render(title="Just a test", user="joe", list_items=[u'Number %d' % num for num in range(1,15)])
    if verbose:
        print render()
    return render
    
def cheetah(dirname, verbose=False):
    from Cheetah.Template import Template
    filename = os.path.join(dirname, 'template.tmpl')
    template = Template(file=filename)
    def render():
        template.__dict__.update({'title': 'Just a test', 'user': 'joe',
                                  'list_items': [u'Number %d' % num for num in range(1, 15)]})
        return template.respond()

    if verbose:
        print render()
    return render

def django(dirname, verbose=False):
    from django.conf import settings
    settings.configure(TEMPLATE_DIRS=[os.path.join(dirname, 'templates')])
    from django import template, templatetags
    from django.template import loader
    templatetags.__path__.append(os.path.join(dirname, 'templatetags'))
    tmpl = loader.get_template('template.html')

    def render():
        data = {'title': 'Just a test', 'user': 'joe',
                'items': ['Number %d' % num for num in range(1, 15)]}
        return tmpl.render(template.Context(data))

    if verbose:
        print render()
    return render

def kid(dirname, verbose=False):
    import kid
    kid.path = kid.TemplatePath([dirname])
    template = kid.Template(file='template.kid')
    def render():
        template = kid.Template(file='template.kid',
                                title='Just a test', user='joe',
                                items=['Number %d' % num for num in range(1, 15)])
        return template.serialize(output='xhtml')

    if verbose:
        print render()
    return render


def run(engines, number=2000, verbose=False):
    basepath = os.path.abspath(os.path.dirname(__file__))
    for engine in engines:
        dirname = os.path.join(basepath, engine)
        if verbose:
            print '%s:' % engine.capitalize()
            print '--------------------------------------------------------'
        else:
            print '%s:' % engine.capitalize(),
        t = timeit.Timer(setup='from __main__ import %s; render = %s(r"%s", %s)'
                                       % (engine, engine, dirname, verbose),
                                 stmt='render()')
            
        time = t.timeit(number=number) / number
        if verbose:
            print '--------------------------------------------------------'
        print '%.2f ms' % (1000 * time)
        if verbose:
            print '--------------------------------------------------------'


if __name__ == '__main__':
    engines = [arg for arg in sys.argv[1:] if arg[0] != '-']
    if not engines:
        engines = __all__

    verbose = '-v' in sys.argv

    if '-p' in sys.argv:
        import hotshot, hotshot.stats
        prof = hotshot.Profile("template.prof")
        benchtime = prof.runcall(run, engines, number=100, verbose=verbose)
        stats = hotshot.stats.load("template.prof")
        stats.strip_dirs()
        stats.sort_stats('time', 'calls')
        stats.print_stats()
    else:
        run(engines, verbose=verbose)
