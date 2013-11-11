<!-- readthedocs add-in template -->

<%inherit file="/layout.mako"/>


<%block name="headers">

<!-- begin iterate through sphinx environment css_files -->
% for cssfile in css_files:
    <link rel="stylesheet" href="${pathto(cssfile, 1)}" type="text/css" />
% endfor
<!-- end iterate through sphinx environment css_files -->

<!-- RTD <head> via mako adapter -->
<script type="text/javascript">
    var doc_version = "${current_version}";
    var doc_slug = "${slug}";
    var static_root = "${pathto('_static', 1)}"

    // copied from:
    // https://github.com/rtfd/readthedocs.org/commit/edbbb4c753454cf20c128d4eb2fef60d740debaa#diff-2f70e8d9361202bfe3f378d2ff2c510bR8
    var READTHEDOCS_DATA = {
        project: "${slug}",
        version: "${current_version}",
        page: "${pagename}",
        theme: "${html_theme or ''}"
      };

</script>
<!-- end RTD <head> via mako adapter -->

    ${parent.headers()}

</%block>


${next.body()}

<%block name="footer">
    ${parent.footer()}
</%block>
