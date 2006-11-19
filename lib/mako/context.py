"""provides the Context class, the runtime namespace for templates."""


class Context(object):
    """provides runtime namespace and output buffer for templates."""
    def __init__(self, buffer, **data):
        self.buffer = buffer
        self.data = data
        # the Template instance currently rendering with this context.
        self.with_template = None
    def __getitem__(self, key):
        return self.data[key]
    def get(self, key, default=None):
        return self.data.get(key, default)
    def write(self, string):
        self.buffer.write(string)