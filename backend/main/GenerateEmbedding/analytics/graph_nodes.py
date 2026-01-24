from typing import List, Any, Tuple, Dict

def prepare_graph_nodes(graph_data: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Convert Graph Nodes into embeddable chunks so we can search the Graph semantically.
    """
    nodes = graph_data.get("nodes", [])
    prepared_chunks = []
    stats = {'processed': 0, 'skipped': 0}
    
    print(f"   Graph contains {len(nodes)} nodes. Preparing for embedding...")

    for node in nodes:
        # ID Format: REPO::FILE::TYPE::NAME
        node_id = node.get("id")
        label = node.get("label") # Function, Class, File
        props = node.get("properties", {})

        name = props.get("name", "")
        description = ""

        if label == "PullRequest":
            name = f"PR #{props.get('number', '?')}"
            description = f"Pull Request #{props.get('number')}: {props.get('title', '')}"
            if props.get('state'): description += f" ({props.get('state')})"
        
        elif label == "Issue":
            name = f"Issue #{props.get('number', '?')}"
            description = f"Issue #{props.get('number')}: {props.get('title', '')}"
        
        elif label == "User":
            name = props.get("name", "Unknown User")
            description = f"User/Developer: {name}"
        
        else:
            # Skip generic nodes if any
            if not name: 
                stats['skipped'] += 1
                continue

            # Create a semantic description for the node
            # e.g. "Function process_payment defined in payment_service.py"
            description = f"{label} {name}"
            if props.get("path"):
                description += f" defined in {props['path']}"
            if props.get("args"):
                description += f" with arguments: {', '.join(props['args'])}"
            
            # Create standard chunk structure
            chunk = {
                "chunk_id": node_id,
                "type": "graph_node",
                "source": "graph",
                "content": description, # This is what gets embedded
                "metadata": {
                    "node_label": label,
                    "node_name": name,
                    "file_path": props.get("path"),
                    "lineno": props.get("lineno")
                },
                "skip_embedding": False
            }
            
            prepared_chunks.append(chunk)
            stats['processed'] += 1

    return prepared_chunks, stats

