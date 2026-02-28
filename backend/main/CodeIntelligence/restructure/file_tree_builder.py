import os
from typing import List, Dict, Any


class FileTreeBuilder:
    """
    Builds hierarchical file tree from flat code_files list
    """

    def __init__(self, code_files: List[Dict[str, Any]]):
        self.code_files = code_files

    def build(self) -> List[Dict[str, Any]]:
        tree = {}

        for file in self.code_files:
            path = file.get("path")
            if not path:
                continue

            parts = path.split("/")
            current = tree

            for part in parts[:-1]:
                current = current.setdefault(part, {})

            current[parts[-1]] = file

        return self._convert_to_tree_format(tree)

    def _convert_to_tree_format(self, node):
        result = []

        for name in sorted(node.keys()):
            value = node[name]

            # Folder
            if isinstance(value, dict) and "content" not in value:
                result.append({
                    "name": name,
                    "type": "folder",
                    "children": self._convert_to_tree_format(value)
                })
            else:
                result.append({
                    "name": name,
                    "type": "file",
                    "path": value.get("path"),
                    "extension": value.get("extension"),
                    "lines": value.get("lines"),
                    "size": value.get("size"),
                    "sha": value.get("sha")
                })

        return result