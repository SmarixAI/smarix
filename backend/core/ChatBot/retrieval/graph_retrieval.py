"""
Graph-based retrieval using NetworkX dependency graphs.
"""
from typing import List, Dict, Any
from pathlib import Path
import pickle


class GraphRetrievalMixin:
    """Mixin for graph-based retrieval from dependency graphs."""
    
    def load_graph_structure(self):
        """Lazy load the NetworkX graph structure"""
        if hasattr(self, 'G') and self.G:
            return self.G
            
        graph_path = Path("../../data/VectorDB") / self.repo_owner / self.repo_name / "graph_structure.pkl"
        if graph_path.exists():
            try:
                with open(graph_path, 'rb') as f:
                    self.G = pickle.load(f)
                print(f"🕸️  Graph loaded: {self.G.number_of_nodes()} nodes")
                return self.G
            except Exception as e:
                print(f"⚠️ Failed to load graph structure: {e}")
        return None
    
    def retrieve_graph_context(self, query_embedding, top_k=5):
        """
        1. Search 'graph_nodes' index to find Entry Points.
        2. Traverse edges in NetworkX to find connected components.
        """
        G = self.load_graph_structure()
        if not G or not self.multi_index_store:
            return []

        # Step 1: Find Entry Nodes using Vector Search on 'graph_nodes' index
        entry_nodes = self.multi_index_store.search_by_type(
            query_embedding, 
            index_type='graph_nodes', 
            top_k=top_k
        )
        
        graph_results = []
        visited = set()

        for node_hit in entry_nodes:
            node_id = node_hit.get('chunk_id') or node_hit.get('metadata', {}).get('chunk_id')
            if not node_id or node_id not in G.nodes:
                continue
                
            if node_id in visited: 
                continue
            visited.add(node_id)

            # Get Node Data
            node_data = G.nodes[node_id]
            
            # Step 2: Get Neighbors (Traverse 1-hop)
            relationships = []
            
            # Incoming edges (e.g., Who calls me? Who modifies me?)
            for u, v, attr in G.in_edges(node_id, data=True):
                edge_type = attr.get('type', 'RELATED')
                source_name = u.split('::')[-1] # Simplify ID to Name
                relationships.append(f"<- [{edge_type}] -- {source_name}")

            # Outgoing edges (e.g., Who do I call? Who did I create?)
            for u, v, attr in G.out_edges(node_id, data=True):
                edge_type = attr.get('type', 'RELATED')
                target_name = v.split('::')[-1]
                relationships.append(f"-- [{edge_type}] -> {target_name}")

            # Format as a Text Chunk for the Context Window
            context_text = f"Entity: {node_data.get('label')} {node_data.get('name')}\n"
            
            if relationships:
                # Limit to 15 relationships to prevent context overflow
                context_text += "Relationships:\n" + "\n".join(relationships[:15]) + "\n"
            
            graph_results.append({
                "content": context_text,
                "metadata": {
                    "type": "graph_context",
                    "source": "dependency_graph",
                    "node_id": node_id
                },
                "score": node_hit.get('score', 1.0)
            })

        return graph_results