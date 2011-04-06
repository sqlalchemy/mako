<%text>#coding:utf-8
<%inherit file="/root.html"/>
<%page cache_type="file" cached="True"/>
<%!
    in_docs=True
%>
</%text>

<%doc>
## TODO: pdf
<div style="text-align:right">
<b>PDF Download:</b> <a href="${pathto('sqlalchemy_' + release.replace('.', '_') + '.pdf', 1)}">download</a>
</div>
</%doc>

${'<%text>'}
${next.body()}
${'</%text>'}

<%text><%def name="style()"></%text>
    <%block name="headers"/>

    <%text>${parent.style()}</%text>
    <link href="/css/site_docs.css" rel="stylesheet" type="text/css"></link>
<%text></%def></%text>

<%text><%def name="title()"></%text>${self.show_title()} &mdash; ${docstitle|h}<%text></%def></%text>


<%!
    local_script_files = []
%>
