#!/usr/bin/env python
import sys,re,os,shutil
import cPickle as pickle

sys.path = ['../../lib', './lib/'] + sys.path

from mako.lookup import TemplateLookup
from mako import exceptions

import read_markdown, toc

files = [
    'index',
    'documentation',
    'defs',
    'namespaces',
    'caching',
    ]

title='Mako Documentation'
version = '0.1.0'

root = toc.TOCElement('', 'root', '', version=version, doctitle=title)

shutil.copy('./content/index.html', './output/index.html')
shutil.copy('./content/documentation.html', './output/documentation.html')

read_markdown.parse_markdown_files(root, files)

pickle.dump(root, file('./output/table_of_contents.pickle', 'w'))

template_dirs = ['./templates', './output']
output = os.path.dirname(os.getcwd())

lookup = TemplateLookup(template_dirs, module_directory='./modules')

def genfile(name, toc):
    infile = name + ".html"
    outname = os.path.join(os.getcwd(), '../', name + ".html")
    outfile = file(outname, 'w')
    print infile, '->', outname
    outfile.write(lookup.get_template(infile).render(toc=toc, extension='html'))
    
for filename in files:
    try:
        genfile(filename, root)
    except:
        print exceptions.text_error_template().render()


        


