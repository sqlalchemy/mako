from setuptools import setup, find_packages

version = '0.1'

setup(name='Mako',
      version=version,
      description="A super-fast templating language that borrows the \
 best ideas from the existing templating languages.",
      long_description="""\
Mako is a template library written in Python. It provides a familiar, non-XML 
syntax which compiles into Python modules for maximum performance. Mako's 
syntax and API borrows from the best ideas of many others, including Django
templates, Cheetah, Myghty, and Genshi. Conceptually, Mako is an embedded 
Python (i.e. Python Server Page) language, which refines the familiar ideas
of componentized layout and inheritance to produce one of the most 
straightforward and flexible models available, while also maintaining close 
ties to Python calling and scoping semantics.

The latest version is available in a `Subversion repository
<http://svn.makotemplates.org/mako/trunk#egg=Mako-dev>`_.
""",
      classifiers=[
      'Development Status :: 4 - Beta',
      'Environment :: Web Environment',
      'Intended Audience :: Developers',
      'Programming Language :: Python',
      'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
      ],
      keywords='wsgi myghty mako',
      author='Mike Bayer',
      author_email='mike@zzzcomputing.com',
      url='http://www.makotemplates.org/',
      license='MIT',
      package_dir={'':'lib'},
      packages=find_packages('lib', exclude=['ez_setup', 'examples', 'tests']),
      zip_safe=False,
      install_requires=[
          'MyghtyUtils',
      ],
      entry_points="""
      [python.templating.engines]
      mako = mako.ext.turbogears:TGPlugin
      """,
)
