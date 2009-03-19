import unittest

def suite():
    modules_to_test = (
        'lru',
        'ast',
        'pygen',
        'lexer',
        'template',
        'lookup',
        'def',
        'decorators',
        'namespace',
        'filters',
        'inheritance',
        'call',
        'cache',
        'exceptions_',
        'babelplugin',
        'tgplugin'
        )
    alltests = unittest.TestSuite()
    for name in modules_to_test:
        mod = __import__(name)
        for token in name.split('.')[1:]:
            mod = getattr(mod, token)
        alltests.addTest(unittest.findTestCases(mod, suiteClass=None))
    return alltests

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
