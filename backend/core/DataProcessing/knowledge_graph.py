"""
Knowledge Graph Builder
Builds a graph representation of code relationships and dependencies
"""

from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict


class KnowledgeGraphBuilder:
    """
    Builds knowledge graph with:
    - Nodes: Files, Functions, Classes, Issues, PRs, People
    - Edges: Dependencies, References, Authorship, Fixes
    """
    
    def __init__(self, repo_data: Dict[str, Any]):
        self.repo_data = repo_data
        self.nodes = {}
        self.edges = []
        self.node_id_counter = 0
    
    def build(self, enriched_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build knowledge graph from enriched chunks"""
        
        print("   Building nodes...")
        self._build_nodes(enriched_chunks)
        
        print("   Building edges...")
        self._build_edges(enriched_chunks)
        
        print("   Computing metrics...")
        metrics = self._compute_graph_metrics()
        
        graph = {
            'nodes': list(self.nodes.values()),
            'edges': self.edges,
            'node_count': len(self.nodes),
            'edge_count': len(self.edges),
            'metrics': metrics
        }
        
        return graph
    
    def _build_nodes(self, enriched_chunks: List[Dict[str, Any]]) -> None:
        """Create nodes from chunks and entities"""
        
        # Create chunk nodes
        for chunk in enriched_chunks:
            node_id = chunk['chunk_id']
            self.nodes[node_id] = {
                'id': node_id,
                'type': 'chunk',
                'chunk_type': chunk.get('chunk_type'),
                'category': chunk.get('category'),
                'importance': chunk.get('importance_score', 1.0),
                'tags': chunk.get('semantic_tags', []),
                'file_path': chunk.get('file_path'),
                'title': chunk.get('title', chunk.get('section_header', ''))
            }
        
        # Create entity nodes (files, functions, classes)
        file_nodes = set()
        function_nodes = set()
        class_nodes = set()
        people_nodes = set()
        
        for chunk in enriched_chunks:
            entities = chunk.get('entities', {})
            
            # File nodes
            if chunk.get('file_path'):
                file_nodes.add(chunk['file_path'])
            
            for file in chunk.get('mentioned_files', []):
                file_nodes.add(file)
            
            for func in entities.get('functions', []):
                function_nodes.add(func)
            
            for cls in entities.get('classes', []):
                class_nodes.add(cls)
            
            for person in chunk.get('mentioned_people', []):
                people_nodes.add(person)
        
        for file_path in file_nodes:
            node_id = f"file_{file_path}"
            if node_id not in self.nodes:
                self.nodes[node_id] = {
                    'id': node_id,
                    'type': 'file',
                    'path': file_path,
                    'name': file_path.split('/')[-1]
                }
        
        for func in function_nodes:
            node_id = f"function_{func}"
            if node_id not in self.nodes:
                self.nodes[node_id] = {
                    'id': node_id,
                    'type': 'function',
                    'name': func
                }
        
        for cls in class_nodes:
            node_id = f"class_{cls}"
            if node_id not in self.nodes:
                self.nodes[node_id] = {
                    'id': node_id,
                    'type': 'class',
                    'name': cls
                }
        
        for person in people_nodes:
            node_id = f"person_{person}"
            if node_id not in self.nodes:
                self.nodes[node_id] = {
                    'id': node_id,
                    'type': 'person',
                    'name': person
                }
    
    def _build_edges(self, enriched_chunks: List[Dict[str, Any]]) -> None:
        """Create edges between nodes"""
        
        for chunk in enriched_chunks:
            chunk_id = chunk['chunk_id']
            
            # Chunk -> File
            if chunk.get('file_path'):
                file_id = f"file_{chunk['file_path']}"
                if file_id in self.nodes:
                    self.edges.append({
                        'source': chunk_id,
                        'target': file_id,
                        'type': 'belongs_to'
                    })
            
            entities = chunk.get('entities', {})
            for func in entities.get('functions', []):
                func_id = f"function_{func}"
                if func_id in self.nodes:
                    self.edges.append({
                        'source': chunk_id,
                        'target': func_id,
                        'type': 'defines'
                    })
            
            for cls in entities.get('classes', []):
                cls_id = f"class_{cls}"
                if cls_id in self.nodes:
                    self.edges.append({
                        'source': chunk_id,
                        'target': cls_id,
                        'type': 'defines'
                    })
            
            for person in chunk.get('mentioned_people', []):
                person_id = f"person_{person}"
                if person_id in self.nodes:
                    self.edges.append({
                        'source': chunk_id,
                        'target': person_id,
                        'type': 'authored_by'
                    })
            
            for related_id in chunk.get('related_chunks', []):
                if related_id in self.nodes:
                    self.edges.append({
                        'source': chunk_id,
                        'target': related_id,
                        'type': 'related_to'
                    })
            
            if chunk.get('file_path'):
                source_file = f"file_{chunk['file_path']}"
                for mentioned in chunk.get('mentioned_files', []):
                    target_file = f"file_{mentioned}"
                    if source_file in self.nodes and target_file in self.nodes:
                        self.edges.append({
                            'source': source_file,
                            'target': target_file,
                            'type': 'references'
                        })
    
    def _compute_graph_metrics(self) -> Dict[str, Any]:
        """Compute graph metrics"""
        
        # Node degree (connections)
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        
        for edge in self.edges:
            out_degree[edge['source']] += 1
            in_degree[edge['target']] += 1
        
        # Find hub nodes (high connectivity)
        hub_nodes = sorted(
            [(node_id, out_degree[node_id] + in_degree[node_id]) 
             for node_id in self.nodes.keys()],
            key=lambda x: x[1],
            reverse=True
        )[:20]
        
        # Count by node type
        node_types = defaultdict(int)
        for node in self.nodes.values():
            node_types[node['type']] += 1
        
        edge_types = defaultdict(int)
        for edge in self.edges:
            edge_types[edge['type']] += 1
        
        return {
            'hub_nodes': [{'id': nid, 'connections': count} for nid, count in hub_nodes],
            'node_types': dict(node_types),
            'edge_types': dict(edge_types),
            'avg_connections': len(self.edges) / len(self.nodes) if self.nodes else 0
        }
    
    def get_node_neighbors(self, node_id: str) -> List[str]:
        """Get neighbors of a node"""
        neighbors = set()
        for edge in self.edges:
            if edge['source'] == node_id:
                neighbors.add(edge['target'])
            if edge['target'] == node_id:
                neighbors.add(edge['source'])
        return list(neighbors)
    
    def get_path(self, source_id: str, target_id: str, max_depth: int = 3) -> List[str]:
        """Find shortest path between two nodes (BFS)"""
        if source_id not in self.nodes or target_id not in self.nodes:
            return []
        
        if source_id == target_id:
            return [source_id]
        
        visited = {source_id}
        queue = [(source_id, [source_id])]
        
        while queue:
            current, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            for neighbor in self.get_node_neighbors(current):
                if neighbor == target_id:
                    return path + [neighbor]
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return []