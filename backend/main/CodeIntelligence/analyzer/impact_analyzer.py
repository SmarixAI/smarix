##/Users/vishalkeshari/Desktop/smarix/backend/main/CodeIntelligence/analyzer/impact_analyzer.py

class ImpactAnalyzer:

    def __init__(
        self,
        file_graph,
        reverse_file_graph,
        call_graph,
        reverse_call_graph,
        class_graph,
        reverse_class_graph,
    ):
        self.file_graph = file_graph
        self.reverse_file_graph = reverse_file_graph
        self.call_graph = call_graph
        self.reverse_call_graph = reverse_call_graph
        self.class_graph = class_graph
        self.reverse_class_graph = reverse_class_graph

    # ----------------------------
    # File-level impact
    # ----------------------------
    def get_impacted_files(self, file_path, transitive=True):
        return self._bfs(self.reverse_file_graph, file_path, transitive)

    # ----------------------------
    # Method-level impact
    # ----------------------------
    def get_impacted_methods(self, method_symbol, transitive=True):
        return self._bfs(self.reverse_call_graph, method_symbol, transitive)

    # ----------------------------
    # Class-level impact
    # ----------------------------
    def get_impacted_classes(self, class_name, transitive=True):
        return self._bfs(self.reverse_class_graph, class_name, transitive)

    # ----------------------------
    # BFS traversal
    # ----------------------------
    def _bfs(self, graph, start_node, transitive):
        visited = set()
        queue = [start_node]

        while queue:
            node = queue.pop(0)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    if transitive:
                        queue.append(neighbor)

        return list(visited)

    # ----------------------------
    # Risk Score
    # ----------------------------
    def compute_file_risk(self, file_path):
        impacted_files = self.get_impacted_files(file_path)
        impacted_methods = [
            m for m in self.reverse_call_graph
            if m.startswith(file_path)
        ]

        fan_in = len(self.reverse_file_graph.get(file_path, []))

        return (
            len(impacted_files) * 2
            + len(impacted_methods)
            + fan_in * 3
        )