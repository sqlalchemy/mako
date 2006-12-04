import myghtyutils.container as container
try:
    import myghtyutils.ext.memcached as memcached
    clsmap = {
        'memory':container.MemoryContainer,
        'dbm':container.DBMContainer,
        'file':container.FileContainer,
        'memcached':memcached.MemcachedContainer
    }
except ImportError:
    clsmap = {
        'memory':container.MemoryContainer,
        'dbm':container.DBMContainer,
        'file':container.FileContainer,
    }

class Cache(object):
    def __init__(self, id):
        self.id = id
        self.context = container.ContainerContext()
        self._containers = {}
    def put(self, key, value, type='memory', **kwargs):
        self._get_container(key, type, **kwargs).set_value(value)
    def get(self, key, type='memory', **kwargs):
        return self._get_container(key, type, **kwargs).get_value()
    def _get_container(self, key, type, **kwargs):
        try:
            return self._containers[key]
        except KeyError:
            return self._containers.setdefault(key, clsmap[type](key, self.context, self.id, **kwargs))
    