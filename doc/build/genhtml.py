#!/usr/bin/env python
import sys,re,os,shutil
import cPickle as pickle

sys.path = ['../../', './lib/'] + sys.path

from mako.lookup import TemplateLookup
from mako import exceptions, __version__ as version

import read_markdown, toc

files = [
    'index',
    'documentation',
    'usage',
    'syntax',
    'defs',
    'runtime',
    'namespaces',
    'inheritance',
    'filtering',
    'unicode',
    'caching',
    ]

title='Mako Documentation'

root = toc.TOCElement('', 'root', '', version=version, doctitle=title)

shutil.copy('./content/index.html', './output/index.html')
shutil.copy('./content/documentation.html', './output/documentation.html')

read_markdown.parse_markdown_files(root, files)

pickle.dump(root, file('./output/table_of_contents.pickle', 'w'))

template_dirs = ['./templates', './output']
output = os.path.dirname(os.getcwd())

lookup = TemplateLookup(template_dirs, output_encoding='utf-8')

def genfile(name, toc):
    infile = name + ".html"
    outname = os.path.join(os.getcwd(), '../', name + ".html")
    outfile = file(outname, 'w')
    print infile, '->', outname
    outfile.write(lookup.get_template(infile).render())
    
for filename in files:
    try:
        genfile(filename, root)
    except:
        print exceptions.text_error_template().render()


        


