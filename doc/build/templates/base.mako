<html>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<link rel="shortcut icon" href="/favicon.ico" type="image/x-icon">
<head>
<title><%block name="head_title">Mako Templates for Python</%block></title>
<%block name="headers">
</%block>
<link rel="stylesheet" href="${pathto('_static/site.css', 1)}"></link>


</head>
<body>
    <div id="wrap">
    <div class="rightbar">
    <div class="slogan">
    Hyperfast and lightweight templating for the Python platform.
    </div>

    % if toolbar:
    <div class="toolbar">
    <a href="${site_base}/">Home</a>
    &nbsp; | &nbsp;
    <a href="${site_base}/trac">Trac</a> 
    &nbsp; | &nbsp;
    <a href="${site_base}/community.html">Community</a>
    &nbsp; | &nbsp;
    <a href="${pathto('index')}">Documentation</a>
    &nbsp; | &nbsp;
    <a href="${site_base}/download.html">Download</a>
    </div>
    % endif

    </div>

    <a href="${site_base}/"><img src="${pathto('_static/makoLogo.png', 1)}" /></a>

    <hr/>

    ${next.body()}
<div class="clearfix">
<%block name="footer">
<hr/>

<div class="copyright">Website content copyright &copy; by Michael Bayer. 
    All rights reserved.  Mako and its documentation are licensed 
    under the MIT license.  mike(&)zzzcomputing.com</div>
</%block>
</div>
</div>
</body>
</html>
