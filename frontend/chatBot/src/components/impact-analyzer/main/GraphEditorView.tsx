"use client";

import React, { useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
} from "reactflow";
import dagre from "dagre";
import "reactflow/dist/style.css";

interface Props {
  graphData: any;
}

const nodeWidth = 180;
const nodeHeight = 50;

function getLayoutedElements(nodes: Node[], edges: Edge[]) {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  dagreGraph.setGraph({
    rankdir: "TB", // Top → Bottom
    nodesep: 80,
    ranksep: 100,
  });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, {
      width: nodeWidth,
      height: nodeHeight,
    });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  return nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);

    return {
      ...node,
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    };
  });
}

export default function GraphEditorView({ graphData }: Props) {
  if (!graphData || !graphData.nodes) {
    return (
      <div className="text-gray-500 text-sm p-6">
        No graph data available
      </div>
    );
  }

  // Convert backend → ReactFlow nodes
  const rawNodes: Node[] = useMemo(() => {
    return graphData.nodes.map((n: any) => ({
      id: n.id,
      data: { label: n.label },
      position: { x: 0, y: 0 }, // temporary
      style: {
        background:
          n.severity === "CRITICAL"
            ? "#7f1d1d"
            : n.severity === "HIGH"
            ? "#991b1b"
            : n.severity === "MEDIUM"
            ? "#92400e"
            : "#1e293b",
        color: "white",
        borderRadius: "8px",
        padding: "6px",
        fontSize: "10px",
        border:
          n.category === "center"
            ? "2px solid #6366f1"
            : "1px solid #334155",
      },
    }));
  }, [graphData]);

  const rawEdges: Edge[] = useMemo(() => {
    return graphData.edges.map((e: any, index: number) => ({
      id: `${e.source}-${e.target}-${index}`,
      source: e.source,
      target: e.target,
      animated: true,
      style: {
        stroke: e.type === "incoming" ? "#22c55e" : "#f97316",
      },
    }));
  }, [graphData]);

  const layoutedNodes = useMemo(() => {
    return getLayoutedElements(rawNodes, rawEdges);
  }, [rawNodes, rawEdges]);

  return (
    <div className="w-full h-full bg-[#1E1E1E]">
      <ReactFlow
        nodes={layoutedNodes}
        edges={rawEdges}
        fitView
      >
        <MiniMap />
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  );
}