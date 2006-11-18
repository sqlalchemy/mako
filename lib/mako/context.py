class Context(object):
    def __init__(self, buffer, **data):
        self.buffer = buffer
        self.data = data
    def __getitem__(self, key):
        return self.data[key]
    def get(self, key, default=None):
        return self.data.get(key, default)
    def write(self, string):
        self.buffer.write(string)