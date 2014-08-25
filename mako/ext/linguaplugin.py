from lingua.extractors import Extractor
from lingua.extractors.python import _extract_python
from mako.ext.extract import MessageExtractor


class LinguaMakoExtractor(Extractor, MessageExtractor):
    '''Mako templates'''
    extensions = ['.mako']
    default_config = {
            'encoding': 'utf-8',
            }

    def __call__(self, filename, options):
        self.options = options
        self.filename = filename
        with open(filename) as input:
            return self.process_file(fileobj)

    def process_python(self, code, code_lineno, translator_strings):
        for msg in _extract_python(self.filename, code.getvalue(), self.options,
                code_lineno):
            if translator_strings:
                msg = Message(msg.msgctxt, msg.msgid, msg.msgid_plural,
                              msg.flags,
                              u' '.join(translator_strings + [msg.comment]),
                              msg.tcomment, msg.location)
            yield msg
