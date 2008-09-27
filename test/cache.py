from mako.template import Template
from mako.lookup import TemplateLookup
from mako import lookup
import shutil, unittest, os
from util import result_lines

if not os.access('./test_htdocs', os.F_OK):
    os.mkdir('./test_htdocs')
for cache_dir in ('container_dbm', 'container_dbm_lock', 'container_file',
            'container_file_lock'):
    fullpath = os.path.join('./test_htdocs', cache_dir)
    if os.path.exists(fullpath):
        shutil.rmtree(fullpath)

class MockCache(object):
    def __init__(self, realcache):
        self.realcache = realcache
    def get(self, key, **kwargs):
        self.key = key
        self.kwargs = kwargs.copy()
        self.kwargs.pop('createfunc', None)
        return self.realcache.get(key, **kwargs)
    
class CacheTest(unittest.TestCase):
    def test_def(self):
        t = Template("""
        <%!
            callcount = [0]
        %>
        <%def name="foo()" cached="True">
            this is foo
            <%
            callcount[0] += 1
            %>
        </%def>
    
        ${foo()}
        ${foo()}
        ${foo()}
        callcount: ${callcount}
""")
        m = self._install_mock_cache(t)
        assert result_lines(t.render()) == [
            'this is foo',
            'this is foo',
            'this is foo',
            'callcount: [1]',
        ]
        assert m.kwargs == {}

    def test_nested_def(self):
        t = Template("""
        <%!
            callcount = [0]
        %>
        <%def name="foo()">
            <%def name="bar()" cached="True">
                this is foo
                <%
                callcount[0] += 1
                %>
            </%def>
            ${bar()}
        </%def>

        ${foo()}
        ${foo()}
        ${foo()}
        callcount: ${callcount}
""")
        m = self._install_mock_cache(t)
        assert result_lines(t.render()) == [
            'this is foo',
            'this is foo',
            'this is foo',
            'callcount: [1]',
        ]
        assert m.kwargs == {}
        
    def test_page(self):
        t = Template("""
        <%!
            callcount = [0]
        %>
        <%page cached="True"/>
        this is foo
        <%
        callcount[0] += 1
        %>
        callcount: ${callcount}
""")
        m = self._install_mock_cache(t)
        t.render()
        t.render()
        assert result_lines(t.render()) == [
            "this is foo",
            "callcount: [1]"
        ]
        assert m.kwargs == {}

    def test_dynamic_key_with_funcargs(self):
        t = Template("""
            <%def name="foo(num=5)" cached="True" cache_key="foo_${str(num)}">
             hi
            </%def>

            ${foo()}
        """)
        m = self._install_mock_cache(t)
        t.render()
        t.render()
        assert result_lines(t.render()) == ['hi']
        assert m.key == "foo_5"

        t = Template("""
            <%def name="foo(*args, **kwargs)" cached="True" cache_key="foo_${kwargs['bar']}">
             hi
            </%def>

            ${foo(1, 2, bar='lala')}
        """)
        m = self._install_mock_cache(t)
        t.render()
        assert result_lines(t.render()) == ['hi']
        assert m.key == "foo_lala"

        t = Template('''
        <%page args="bar='hi'" cache_key="foo_${bar}" cached="True"/>
         hi
        ''')
        m = self._install_mock_cache(t)
        t.render()
        assert result_lines(t.render()) == ['hi']
        assert m.key == "foo_hi"

        
    def test_dynamic_key_with_imports(self):
        lookup = TemplateLookup()
        lookup.put_string("foo.html", """
        <%!
            callcount = [0]
        %>
        <%namespace file="ns.html" import="*"/>
        <%page cached="True" cache_key="${foo}"/>
        this is foo
        <%
        callcount[0] += 1
        %>
        callcount: ${callcount}
""")
        lookup.put_string("ns.html", """""")
        t = lookup.get_template("foo.html")
        m = self._install_mock_cache(t)
        t.render(foo='somekey')
        t.render(foo='somekey')
        assert result_lines(t.render(foo='somekey')) == [
            "this is foo",
            "callcount: [1]"
        ]
        assert m.kwargs == {}
        
    def test_fileargs_implicit(self):
        l = lookup.TemplateLookup(module_directory='./test_htdocs')
        l.put_string("test","""
                <%!
                    callcount = [0]
                %>
                <%def name="foo()" cached="True" cache_type='dbm'>
                    this is foo
                    <%
                    callcount[0] += 1
                    %>
                </%def>

                ${foo()}
                ${foo()}
                ${foo()}
                callcount: ${callcount}
        """)
        
        m = self._install_mock_cache(l.get_template('test'))
        assert result_lines(l.get_template('test').render()) == [
            'this is foo',
            'this is foo',
            'this is foo',
            'callcount: [1]',
        ]
        assert m.kwargs == {'type':'dbm', 'data_dir':'./test_htdocs'}
        
    def test_fileargs_deftag(self):
        t = Template("""
        <%!
            callcount = [0]
        %>
        <%def name="foo()" cached="True" cache_type='file' cache_dir='./test_htdocs'>
            this is foo
            <%
            callcount[0] += 1
            %>
        </%def>

        ${foo()}
        ${foo()}
        ${foo()}
        callcount: ${callcount}
""")
        m = self._install_mock_cache(t)
        assert result_lines(t.render()) == [
            'this is foo',
            'this is foo',
            'this is foo',
            'callcount: [1]',
        ]
        assert m.kwargs == {'type':'file','data_dir':'./test_htdocs'}

    def test_fileargs_pagetag(self):
        t = Template("""
        <%page cache_dir='./test_htdocs' cache_type='dbm'/>
        <%!
            callcount = [0]
        %>
        <%def name="foo()" cached="True">
            this is foo
            <%
            callcount[0] += 1
            %>
        </%def>

        ${foo()}
        ${foo()}
        ${foo()}
        callcount: ${callcount}
""")
        m = self._install_mock_cache(t)
        assert result_lines(t.render()) == [
            'this is foo',
            'this is foo',
            'this is foo',
            'callcount: [1]',
        ]
        assert m.kwargs == {'data_dir':'./test_htdocs', 'type':'dbm'}

    def test_args_complete(self):
        t = Template("""
        <%def name="foo()" cached="True" cache_timeout="30" cache_dir="./test_htdocs" cache_type="file" cache_key='somekey'>
            this is foo
        </%def>

        ${foo()}
""")
        m = self._install_mock_cache(t)
        t.render()
        assert m.kwargs == {'data_dir':'./test_htdocs', 'type':'file', 'expiretime':30}
        
        t2 = Template("""
        <%page cached="True" cache_timeout="30" cache_dir="./test_htdocs" cache_type="file" cache_key='somekey'/>
        hi
        """)
        m = self._install_mock_cache(t2)
        t2.render()
        assert m.kwargs == {'data_dir':'./test_htdocs', 'type':'file', 'expiretime':30}

    def test_fileargs_lookup(self):
        l = lookup.TemplateLookup(cache_dir='./test_htdocs', cache_type='file')
        l.put_string("test","""
                <%!
                    callcount = [0]
                %>
                <%def name="foo()" cached="True">
                    this is foo
                    <%
                    callcount[0] += 1
                    %>
                </%def>

                ${foo()}
                ${foo()}
                ${foo()}
                callcount: ${callcount}
        """)
    
        t = l.get_template('test')
        m = self._install_mock_cache(t)
        assert result_lines(l.get_template('test').render()) == [
            'this is foo',
            'this is foo',
            'this is foo',
            'callcount: [1]',
        ]
        assert m.kwargs == {'data_dir':'./test_htdocs', 'type':'file'}
    
    def test_buffered(self):
        t = Template("""
        <%!
            def a(text):
                return "this is a " + text.strip()
        %>
        ${foo()}
        ${foo()}
        <%def name="foo()" cached="True" buffered="True">
            this is a test
        </%def>
        """, buffer_filters=["a"])
        assert result_lines(t.render()) == ["this is a this is a test", "this is a this is a test"]
    
    def test_load_from_expired(self):
        """test that the cache callable can be called safely after the
        originating template has completed rendering.
        
        """
        t = Template("""
        ${foo()}
        <%def name="foo()" cached="True" cache_timeout="2">
            foo
        </%def>
        """)
        
        import time
        x1 = t.render()
        time.sleep(3)
        x2 = t.render()
        assert x1.strip() == x2.strip() == "foo"
    
    def test_cache_uses_current_context(self):
        t = Template("""
        ${foo()}
        <%def name="foo()" cached="True" cache_timeout="2">
            foo: ${x}
        </%def>
        """)
        
        import time
        x1 = t.render(x=1)
        time.sleep(3)
        x2 = t.render(x=2)
        assert x1.strip() == "foo: 1"
        assert x2.strip() == "foo: 2"

    def test_namespace_access(self):
        t = Template("""
            <%def name="foo(x)" cached="True">
                foo: ${x}
            </%def>

            <%
                foo(1)
                foo(2)
                local.cache.invalidate_def('foo')
                foo(3)
                foo(4)
            %>
        """)
        assert result_lines(t.render()) == ['foo: 1', 'foo: 1', 'foo: 3', 'foo: 3']
        
    def test_invalidate(self):
        t = Template("""
            <%def name="foo()" cached="True">
                foo: ${x}
            </%def>

            <%def name="bar()" cached="True" cache_type='dbm' cache_dir='./test_htdocs'>
                bar: ${x}
            </%def>
            ${foo()} ${bar()}
        """)

        assert result_lines(t.render(x=1)) == ["foo: 1", "bar: 1"]
        assert result_lines(t.render(x=2)) == ["foo: 1", "bar: 1"]
        t.cache.invalidate_def('foo')
        assert result_lines(t.render(x=3)) == ["foo: 3", "bar: 1"]
        t.cache.invalidate_def('bar')
        assert result_lines(t.render(x=4)) == ["foo: 3", "bar: 4"]
        
        t = Template("""
            <%page cached="True" cache_type="dbm" cache_dir="./test_htdocs"/>
            
            page: ${x}
        """)
        assert result_lines(t.render(x=1)) == ["page: 1"]
        assert result_lines(t.render(x=2)) == ["page: 1"]
        t.cache.invalidate_body()
        assert result_lines(t.render(x=3)) == ["page: 3"]
        assert result_lines(t.render(x=4)) == ["page: 3"]
        
        
    def _install_mock_cache(self, template):
        m = MockCache(template.module._template_cache)
        template.module._template_cache = m
        return m
            
if __name__ == '__main__':
    unittest.main()
