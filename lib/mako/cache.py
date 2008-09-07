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
    def __init__(self, id, starttime, **kwargs):
        self.id = id
        self.starttime = starttime
        if container is not None:
            self.context = container.ContainerContext()
        self._containers = {}
        self.kwargs = kwargs
    def put(self, key, value, type='memory', **kwargs):
        self._get_container(key, type, **kwargs).set_value(value)
    def get(self, key, type='memory', **kwargs):
        return self._get_container(key, type, **kwargs).get_value()
    def _get_container(self, key, type, **kwargs):
        if not container:
            raise exceptions.RuntimeException("the Beaker package is required to use cache functionality.")
        kw = self.kwargs.copy()
        kw.update(kwargs)
        
        return container.Value(key, self.context, self.id, clsmap[type], starttime=self.starttime, **kw)
    
