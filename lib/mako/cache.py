from mako import exceptions

try:
    from beaker import container, exceptions, cache
    clsmap = cache.clsmap

    if 'ext:memcached' in clsmap:
        clsmap['memcached'] = clsmap['ext:memcached']
except ImportError:
    container = None
    clsmap = {}

class Cache(object):
    def __init__(self, id, starttime):
        self.id = id
        self.starttime = starttime
        if container is not None:
            self.context = container.ContainerContext()
        self._values = {}
        
    def put(self, key, value, **kwargs):
        c = self._get_container(key, **kwargs)
        if not c:
            raise exceptions.RuntimeException("No cache container exists for key %r" % key)
        c.set_value(value)
        
    def get(self, key, **kwargs):
        c = self._get_container(key, **kwargs)
        if c:
            return c.get_value()
        else:
            return None
        
    def invalidate(self, key, **kwargs):
        c = self._get_container(key, **kwargs)
        if c:
            c.clear_value()
    
    def invalidate_body(self):
        self.invalidate('render_body')
    
    def invalidate_def(self, name):
        self.invalidate('render_%s' % name)
        
    def invalidate_closure(self, name):
        self.invalidate(name)
        
    def _get_container(self, key, **kwargs):
        if not container:
            raise exceptions.RuntimeException("the Beaker package is required to use cache functionality.")
        
        if kwargs:
            type = kwargs.pop('type', 'memory')
            self._values[key] = k = container.Value(key, self.context, self.id, clsmap[type], starttime=self.starttime, **kwargs)
            return k
        else:
            return self._values.get(key, None)


