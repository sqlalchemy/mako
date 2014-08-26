import io
from lingua.extractors import Extractor
from lingua.extractors import Message
from lingua.extractors import get_extractor
from mako.ext.extract import MessageExtractor


class LinguaMakoExtractor(Extractor, MessageExtractor):
    '''Mako templates'''
    extensions = ['.mako']
    default_config = {
            'encoding': 'utf-8',
            'comment-tags': '',
            }

    def __call__(self, filename, options, fileobj=None):
        self.options = options
        self.filename = filename
        self.python_extractor = get_extractor('x.py')
        if fileobj is None:
            fileobj = open(filename, 'rb')
        return self.process_file(fileobj)

    def process_python(self, code, code_lineno, translator_strings):
        source = code.getvalue().strip()
        if source.endswith(':'):
            source += ' pass'
            code = io.BytesIO(source)
        for msg in self.python_extractor(self.filename, self.options, code, code_lineno):
            if translator_strings:
                msg = Message(msg.msgctxt, msg.msgid, msg.msgid_plural,
                              msg.flags,
                              u' '.join(translator_strings + [msg.comment]),
                              msg.tcomment, msg.location)
            yield msg
