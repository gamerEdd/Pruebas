"""
Stub minimal para `pygraphviz`. No crea gráficos; evita ModuleNotFoundError
during packaging. For real graph support, install Graphviz system package
and `pygraphviz` Python package.
"""
class AGraph:
    def __init__(self, *args, **kwargs):
        pass
    def add_node(self, *args, **kwargs):
        pass
    def add_edge(self, *args, **kwargs):
        pass
    def draw(self, *args, **kwargs):
        raise NotImplementedError('pygraphviz stub: no drawing support')
