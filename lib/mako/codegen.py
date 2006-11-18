

class TemplateGenerator(object):
    def __init__(self, nodes):
        self.nodes = nodes
        self.module_code = []
        class FindPyDecls(object):
            def visitCode(s, node):
                if node.ismodule:
                    self.module_code.append(node)
        f = FindPyDecls()
        for n in nodes:
            n.accept_visitor(f)