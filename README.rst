=========================
Mako Templates for Python
=========================

Mako is a template library written in Python. It provides a familiar, non-XML 
syntax which compiles into Python modules for maximum performance. Mako's 
syntax and API borrows from the best ideas of many others, including Django
templates, Cheetah, Myghty, and Genshi. Conceptually, Mako is an embedded 
Python (i.e. Python Server Page) language, which refines the familiar ideas
of componentized layout and inheritance to produce one of the most 
straightforward and flexible models available, while also maintaining close 
ties to Python calling and scoping semantics.

Nutshell
========

::

    <%inherit file="base.html"/>
    <%
        rows = [[v for v in range(0,10)] for row in range(0,10)]
    %>
    <table>
        % for row in rows:
            ${makerow(row)}
        % endfor
    </table>

    <%def name="makerow(row)">
        <tr>
        % for name in row:
            <td>${name}</td>\
        % endfor
        </tr>
    </%def>

Philosophy
===========

Python is a great scripting language. Don't reinvent the wheel...your templates can handle it !

Documentation
==============

See documentation for Mako at https://docs.makotemplates.org/en/latest/


The SQLAlchemy Project
======================

Mako is part of the `SQLAlchemy Project <https://www.sqlalchemy.org>`_ and
adheres to the same standards and conventions as the core project.

Development / Bug reporting / Pull requests
___________________________________________

Please refer to the
`SQLAlchemy Community Guide <https://www.sqlalchemy.org/develop.html>`_ for
guidelines on coding and participating in this project.

Code of Conduct
_______________

Above all, SQLAlchemy places great emphasis on polite, thoughtful, and
constructive communication between users and developers.
Please see our current Code of Conduct at
`Code of Conduct <https://www.sqlalchemy.org/codeofconduct.html>`_.

License
=======

Mako is distributed under the `MIT license
<https://opensource.org/licenses/MIT>`_.

Other incorporated projects may be licensed under different licenses.
All licenses allow for non-commercial and commercial use.
