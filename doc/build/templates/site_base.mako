<%text>#coding:utf-8
<%inherit file="/root.mako"/>
<%page cache_type="file" cached="True"/>
<%!
    in_docs=True
%>
</%text>


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
