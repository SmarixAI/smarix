"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import rehypeRaw from "rehype-raw";
import mermaid from "mermaid";
import {
  Send,
  Loader2,
  Bot,
  User,
  Sparkles,
  FileCode,
  BarChart3,
  Trash2,
  Copy,
  Check,
  ChevronDown,
  ExternalLink,
  GitPullRequest,
  AlertCircle,
  GitCommit,
  Code2,
  Workflow,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  PlusCircle,
  MessageSquarePlus,
  ChevronLeft,
  ChevronRight,
  Clock,
  Database,
} from "lucide-react";
import Link from "next/link";

if (typeof window !== "undefined") {
  mermaid.initialize({
    startOnLoad: false,
    theme: "dark",
    logLevel: "error",
    securityLevel: "loose",
    themeVariables: {
      primaryColor: "#22d3ee",
      primaryTextColor: "#fff",
      primaryBorderColor: "#06b6d4",
      lineColor: "#a855f7",
      secondaryColor: "#a855f7",
      tertiaryColor: "#1f2937",
      background: "#000",
      mainBkg: "#0a0a0a",
      nodeBorder: "#22d3ee",
      clusterBkg: "#1f2937",
      clusterBorder: "#a855f7",
      titleColor: "#fff",
      edgeLabelBackground: "#1f2937",
      fontFamily:
        "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
    },
    flowchart: {
      htmlLabels: true,
      curve: "basis",
      useMaxWidth: true,
      defaultRenderer: "elk",
      padding: 20,
    },
  });
}

const sanitizeMermaidCode = (code: string): string => {
  const lines = code.split("\n");

  const sanitizedLines = lines.map((line) => {
    if (
      line.trim().startsWith("%%") ||
      line.trim().startsWith("graph") ||
      line.trim().startsWith("flowchart") ||
      line.trim() === ""
    ) {
      return line;
    }

    return line.replace(
      /([A-Za-z0-9_]+)\[([^\]]+)\]/g,
      (match, nodeId, label) => {
        if (
          label.includes("(") ||
          label.includes(")") ||
          label.includes("[") ||
          label.includes("]") ||
          label.includes("{") ||
          label.includes("}")
        ) {
          if (!label.startsWith('"') || !label.endsWith('"')) {
            const escapedLabel = label.replace(/"/g, '\\"');
            return `${nodeId}["${escapedLabel}"]`;
          }
        }
        return match;
      }
    );
  });

  return sanitizedLines.join("\n");
};

const MermaidDiagram = ({ code }: { code: string }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);
  const [zoom, setZoom] = useState(1);

  useEffect(() => {
    if (!code || !containerRef.current) return;

    const renderDiagram = async () => {
      setIsLoading(true);
      setError("");

      try {
        const sanitizedCode = sanitizeMermaidCode(code);
        const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;
        const { svg } = await mermaid.render(id, sanitizedCode);

        if (containerRef.current) {
          containerRef.current.innerHTML = svg;

          const svgElement = containerRef.current.querySelector("svg");
          if (svgElement) {
            svgElement.style.maxWidth = "100%";
            svgElement.style.height = "auto";
            svgElement.style.transformOrigin = "center";
            svgElement.style.transition = "transform 0.2s ease-out";
          }
        }
      } catch (err) {
        console.error("Mermaid rendering error:", err);
        setError(
          err instanceof Error ? err.message : "Failed to render diagram"
        );
      } finally {
        setIsLoading(false);
      }
    };

    renderDiagram();
  }, [code]);

  useEffect(() => {
    if (containerRef.current) {
      const svgElement = containerRef.current.querySelector("svg");
      if (svgElement) {
        svgElement.style.transform = `scale(${zoom})`;
      }
    }
  }, [zoom]);

  const handleZoomIn = () => {
    setZoom((prev) => Math.min(prev + 0.2, 3));
  };

  const handleZoomOut = () => {
    setZoom((prev) => Math.max(prev - 0.2, 0.5));
  };

  const handleReset = () => {
    setZoom(1);
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    setZoom((prev) => Math.max(0.5, Math.min(3, prev + delta)));
  };

  if (error) {
    return (
      <div className="text-red-400 text-sm p-4 bg-red-500/10 border border-red-500/30 rounded my-4">
        <p className="font-semibold mb-1">Failed to render diagram</p>
        <p className="text-xs text-gray-400">{error}</p>
        <details className="mt-2">
          <summary className="cursor-pointer text-xs text-gray-500 hover:text-gray-300">
            Show code
          </summary>
          <pre className="mt-2 text-xs bg-black/50 p-2 rounded overflow-x-auto">
            {code}
          </pre>
        </details>
      </div>
    );
  }

  return (
    <div className="my-4 bg-black/50 rounded-lg border border-cyan-400/30 relative">
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/50 z-10">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
        </div>
      )}

      {!isLoading && (
        <div className="absolute top-2 right-2 z-20 flex items-center gap-1 bg-black/80 rounded-lg p-1 border border-cyan-400/30">
          <button
            onClick={handleZoomOut}
            className="p-1.5 hover:bg-white/10 rounded transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4 text-cyan-400" />
          </button>

          <div className="px-2 py-0.5 min-w-[50px] text-center">
            <span className="text-xs text-white font-mono">
              {(zoom * 100).toFixed(0)}%
            </span>
          </div>

          <button
            onClick={handleZoomIn}
            className="p-1.5 hover:bg-white/10 rounded transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4 text-cyan-400" />
          </button>

          <button
            onClick={handleReset}
            className="p-1.5 hover:bg-white/10 rounded transition-colors"
            title="Reset Zoom"
          >
            <RotateCcw className="w-4 h-4 text-cyan-400" />
          </button>
        </div>
      )}

      <div
        className="p-4 overflow-auto"
        onWheel={handleWheel}
        style={{ minHeight: "200px", maxHeight: "600px" }}
      >
        <div ref={containerRef} className="mermaid-container" />
      </div>
    </div>
  );
};

interface FlowNode {
  id: string;
  label: string;
  file: string;
  type: string;
  line_start?: number;
  line_end?: number;
}

interface FlowEdge {
  from: string;
  to: string;
  label?: string;
}

interface FlowData {
  nodes: FlowNode[];
  edges: FlowEdge[];
  metadata: {
    diagram_type: string;
    direction: string;
    query: string;
  };
}

interface RelatedIssue {
  number: number;
  title: string;
  status: string;
  labels: string[];
  url: string;
  matched_keywords: string[];
  match_score: number;
  description: string;
}

interface RelatedPR {
  number: number;
  title: string;
  status: string;
  author: string;
  url: string;
  matched_keywords: string[];
  match_score: number;
  description: string;
}

interface RelatedCommit {
  sha: string;
  full_sha: string;
  author: string;
  url: string;
  matched_keywords: string[];
  match_score: number;
  message: string;
}

interface RelatedKnowledge {
  issues: RelatedIssue[];
  prs: RelatedPR[];
  commits: RelatedCommit[];
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  chunks_retrieved?: number;
  flow_data?: FlowData;
  related_knowledge?: RelatedKnowledge;
  metrics_summary?: any;
  timestamp: Date;
}

interface Source {
  file: string;
  type: string;
  score: number;
  context_role?: string;
  url?: string;
  html_url?: string;
  content_type?: string;
  issue_number?: number;
  pr_number?: number;
  issue_id?: string;
  pr_id?: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [showSources, setShowSources] = useState<{ [key: string]: boolean }>(
    {}
  );
  const [showRelatedKnowledge, setShowRelatedKnowledge] = useState<{
    [key: string]: boolean;
  }>({});
  const [stats, setStats] = useState<any>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(
    null
  );
  const [isSidebarExpanded, setIsSidebarExpanded] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    fetchStats();
    loadSessions();
  }, []);

  const convertFlowDataToMermaid = (flowData: FlowData): string => {
    if (!flowData || !flowData.nodes || !flowData.edges) return "";

    const direction = flowData.metadata?.direction || "TD";
    let mermaidCode = `%%{init: {'theme':'dark', 'themeVariables': {'primaryColor':'#22d3ee','primaryTextColor':'#fff','primaryBorderColor':'#06b6d4','lineColor':'#a855f7','secondaryColor':'#a855f7','tertiaryColor':'#1f2937'},'flowchart':{'defaultRenderer':'elk','htmlLabels':true,'curve':'basis'}}}%%\n`;
    mermaidCode += `flowchart ${direction}\n`;

    const nodesByComponent: { [key: string]: FlowNode[] } = {};
    flowData.nodes.forEach((node) => {
      const filePath = node.file || "";
      let component = "Main";

      if (filePath) {
        const parts = filePath.split("/");
        component = parts.length > 1 ? parts[parts.length - 2] : "Main";
      }

      if (!nodesByComponent[component]) {
        nodesByComponent[component] = [];
      }
      nodesByComponent[component].push(node);
    });

    const components = Object.keys(nodesByComponent);
    let subgraphCounter = 0;

    components.forEach((component) => {
      const nodes = nodesByComponent[component];
      const indent = components.length > 1 ? "        " : "    ";

      if (components.length > 1) {
        subgraphCounter++;
        const safeComponent = component.replace(/[^a-zA-Z0-9]/g, "_");
        mermaidCode += `    subgraph SG${subgraphCounter}["${component}"]\n`;
      }

      nodes.forEach((node) => {
        const safeLabel = node.label.replace(/"/g, "'");
        const nodeId = node.id;
        const nodeType = node.type || "function";

        let nodeShape = "";
        if (nodeType === "class") {
          nodeShape = `${nodeId}[("${safeLabel}")]`;
        } else if (nodeType === "method") {
          nodeShape = `${nodeId}["${safeLabel}"]`;
        } else if (nodeType === "function") {
          nodeShape = `${nodeId}[["${safeLabel}"]]`;
        } else {
          nodeShape = `${nodeId}["${safeLabel}"]`;
        }

        mermaidCode += `${indent}${nodeShape}\n`;
      });

      if (components.length > 1) {
        mermaidCode += `    end\n`;
      }
    });

    mermaidCode += "\n";
    flowData.edges.forEach((edge) => {
      if (edge.label) {
        mermaidCode += `    ${edge.from} -.->|${edge.label}| ${edge.to}\n`;
      } else {
        mermaidCode += `    ${edge.from} --> ${edge.to}\n`;
      }
    });

    mermaidCode += "\n";
    mermaidCode +=
      "    classDef functionClass fill:#0891b2,stroke:#22d3ee,stroke-width:2px,color:#fff\n";
    mermaidCode +=
      "    classDef classClass fill:#7c3aed,stroke:#a855f7,stroke-width:2px,color:#fff\n";
    mermaidCode +=
      "    classDef methodClass fill:#059669,stroke:#10b981,stroke-width:2px,color:#fff\n";

    flowData.nodes.forEach((node) => {
      const nodeType = node.type || "function";
      if (nodeType === "function") {
        mermaidCode += `    class ${node.id} functionClass\n`;
      } else if (nodeType === "class") {
        mermaidCode += `    class ${node.id} classClass\n`;
      } else if (nodeType === "method") {
        mermaidCode += `    class ${node.id} methodClass\n`;
      }
    });

    return mermaidCode;
  };

  const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchStats = async () => {
    try {
      const response = await fetch(`${baseURL}/stats`);
      const data = await response.json();
      setStats(data.stats);
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  };

  const normalizeRelatedKnowledge = (raw: any) => {
    if (!raw) {
      return { issues: [], prs: [], commits: [], metricsSummary: null };
    }

    if (
      Array.isArray(raw.issues) ||
      Array.isArray(raw.prs) ||
      Array.isArray(raw.commits)
    ) {
      return {
        issues: Array.isArray(raw.issues) ? raw.issues : [],
        prs: Array.isArray(raw.prs) ? raw.prs : [],
        commits: Array.isArray(raw.commits) ? raw.commits : [],
        metricsSummary: null,
      };
    }

    const metrics: any = {};
    if (raw.repo_metrics) {
      metrics.repo_metrics = raw.repo_metrics;
    } else if (raw.repo_metrics_present !== undefined) {
      metrics.repo_metrics = raw.repo_metrics_present;
    }
    if (raw.tech_summary) {
      metrics.tech_summary = raw.tech_summary;
    } else if (raw.tech_summary_present !== undefined) {
      metrics.tech_summary = raw.tech_summary_present;
    }

    const simplifiedMetrics: any = {};
    if (metrics.repo_metrics) {
      if (
        Array.isArray(metrics.repo_metrics) &&
        metrics.repo_metrics.length > 0
      ) {
        simplifiedMetrics.repo_metrics = metrics.repo_metrics[0];
      } else {
        simplifiedMetrics.repo_metrics = metrics.repo_metrics;
      }
    }
    if (metrics.tech_summary) {
      if (
        Array.isArray(metrics.tech_summary) &&
        metrics.tech_summary.length > 0
      ) {
        simplifiedMetrics.tech_summary = metrics.tech_summary[0];
      } else {
        simplifiedMetrics.tech_summary = metrics.tech_summary;
      }
    }

    return {
      issues: [],
      prs: [],
      commits: [],
      metricsSummary: Object.keys(simplifiedMetrics).length
        ? simplifiedMetrics
        : null,
    };
  };

  const loadSessions = async () => {
    try {
      const response = await fetch(`${baseURL}/sessions`);
      const data = await response.json();
      console.log(
        "📋 Titles:",
        (data.sessions || []).map((s: any) => `${s.title} (${s.message_count})`)
      );
      setSessions(data.sessions || []);
    } catch (error) {
      console.error("Failed to load sessions:", error);
    }
  };

  const loadSession = async (sessionId: string) => {
    try {
      console.log(`Loading session: ${sessionId}`);
      const response = await fetch(
        `${baseURL}/load-session/${sessionId}`
      );
      const data = await response.json();
      console.log("Loaded messages:", data.messages);

      const formattedMessages = (data.messages || []).map(
        (msg: any, index: number) => ({
          id:
            msg.id?.toString() ||
            `msg-${index}-${sessionId.slice(-4)}-${Date.now()}`,
          role: (msg.role as "user" | "assistant") || "assistant",
          content: msg.content || "No content available",
          timestamp: new Date(msg.created_at || Date.now()),
        })
      );

      setMessages(formattedMessages);
      setSessionId(data.session_id);
      setSelectedSessionId(data.session_id);

      await loadSessions();
      scrollToActiveSession();
    } catch (error) {
      console.error("Failed to load session:", error);
      setMessages([]);
      setSessionId(sessionId);
      setSelectedSessionId(sessionId);
    }
  };

  const scrollToActiveSession = () => {
    setTimeout(() => {
      const container = document.getElementById("sessions-container");
      const activeSession = container?.querySelector(".ring-2");
      if (activeSession) {
        activeSession.scrollIntoView({
          behavior: "smooth",
          block: "nearest",
          inline: "start",
        });
      }
    }, 100);
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // Try to get username from localStorage
      let username: string | undefined;
      try {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
          const user = JSON.parse(storedUser);
          username = user.username;
        }
      } catch (e) {
        // Ignore errors getting username
      }

      const requestBody: { query: string; session_id?: string; username?: string } = {
        query: input,
      };

      if (sessionId) {
        requestBody.session_id = sessionId;
      }

      if (username) {
        requestBody.username = username;
      }

      const response = await fetch(`${baseURL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error("Failed to get response");
      }

      const data = await response.json();

      if (
        data.conversation_id &&
        (!sessionId || sessionId !== data.conversation_id)
      ) {
        setSessionId(data.conversation_id);
        setSelectedSessionId(data.conversation_id);
        await loadSessions();
        console.log(`New session created: ${data.conversation_id}`);
      }

      const normalizedRelated = normalizeRelatedKnowledge(
        data.related_knowledge
      );

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.answer,
        sources: data.sources,
        chunks_retrieved: data.chunks_retrieved,
        flow_data: data.flow_data,
        related_knowledge: {
          issues: normalizedRelated.issues,
          prs: normalizedRelated.prs,
          commits: normalizedRelated.commits,
        },
        metrics_summary: normalizedRelated.metricsSummary,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          "Sorry, I encountered an error. Please make sure the backend is running and try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearHistory = async () => {
    if (!sessionId) return;

    try {
      const requestBody = { session_id: sessionId };

      await fetch(`${baseURL}/clear-history`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      setMessages([]);
      setSessionId(null);
      setSelectedSessionId(null);
      await loadSessions();
    } catch (error) {
      console.error("Failed to clear history:", error);
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const toggleSources = (messageId: string) => {
    setShowSources((prev) => ({
      ...prev,
      [messageId]: !prev[messageId],
    }));
  };

  const toggleRelatedKnowledge = (messageId: string) => {
    setShowRelatedKnowledge((prev) => ({
      ...prev,
      [messageId]: !prev[messageId],
    }));
  };

  const getContentIcon = (contentType?: string) => {
    switch (contentType) {
      case "issue":
        return <AlertCircle className="w-3 h-3" />;
      case "pull_request":
        return <GitPullRequest className="w-3 h-3" />;
      case "commit":
        return <GitCommit className="w-3 h-3" />;
      default:
        return <FileCode className="w-3 h-3" />;
    }
  };

  const formatFileName = (source: Source) => {
    if (source.content_type === "issue" && source.issue_id) {
      return `Issue ${source.issue_id}`;
    }
    if (source.content_type === "pull_request" && source.pr_id) {
      return `PR ${source.pr_id}`;
    }
    if (source.content_type === "commit") {
      return `Commit ${source.file}`;
    }
    return source.file;
  };

  return (
    <div className="flex h-screen bg-gradient-to-b from-black via-zinc-900 to-black text-white antialiased">
      {/* Sidebar */}
      <motion.div
        initial={false}
        animate={{ width: isSidebarExpanded ? 320 : 0 }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className="border-r border-white/10 bg-black/40 backdrop-blur-md flex flex-col overflow-hidden"
        style={{
          WebkitFontSmoothing: "antialiased",
          MozOsxFontSmoothing: "grayscale",
        }}
      >
        <div className="flex flex-col h-full w-80">
          {/* Header */}
          <div className="p-4 border-b border-white/10 flex-shrink-0">
            <Link href="/" className="flex items-center gap-3 mb-4">
              <img
                src="/logo.png"
                alt="Smarix Logo"
                className="w-10 h-10 object-contain"
              />
              <span className="font-bold text-lg">Smarix</span>
            </Link>

            {/* New Chat Button */}
            <button
              onClick={async () => {
                try {
                  const response = await fetch(
                    `${baseURL}/new-session`,
                    {
                      method: "POST",
                    }
                  );
                  const data = await response.json();

                  setSessionId(data.session_id);
                  setSelectedSessionId(data.session_id);
                  setMessages([]);

                  await loadSessions();
                } catch (err) {}
              }}
              className="w-full p-3 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 hover:from-cyan-500/30 hover:to-purple-500/30 border border-cyan-400/30 rounded-lg transition-all flex items-center justify-center gap-2 group hover:scale-[1.02] active:scale-[0.98]"
            >
              <MessageSquarePlus className="w-5 h-5 text-cyan-400 group-hover:rotate-12 transition-transform" />
              <span className="text-sm font-medium">New Chat</span>
            </button>

            {/* Stats */}
            {stats && (
              <div className="mt-4 p-3 bg-white/5 rounded-lg border border-white/10">
                <div className="flex items-center gap-2 mb-2">
                  <Database className="w-4 h-4 text-cyan-400" />
                  <span className="text-xs font-semibold text-gray-300">
                    Database Stats
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-400">Total Chunks</span>
                  <span className="text-sm font-mono text-cyan-400">
                    {stats.total_chunks?.toLocaleString()}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Sessions List */}
          <div className="flex-1 overflow-y-auto p-3" id="sessions-container">
            <div className="mb-2 flex items-center justify-between px-2">
              <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Recent Chats
              </span>
              <Clock className="w-3.5 h-3.5 text-gray-500" />
            </div>
            <AnimatePresence>
              {sessions.map((session: any) => (
                <motion.div
                  key={session.session_id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  className={`p-3 cursor-pointer rounded-lg transition-all mb-2 group relative ${
                    selectedSessionId === session.session_id
                      ? "bg-gradient-to-r from-cyan-500/20 to-purple-500/20 border border-cyan-400/50 shadow-lg"
                      : "hover:bg-white/5 border border-transparent hover:border-cyan-400/30"
                  }`}
                  onClick={() => loadSession(session.session_id)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate text-white mb-1">
                        {session.title}
                      </div>
                      <div className="flex items-center gap-2 text-xs text-gray-400">
                        <span className="flex items-center gap-1">
                          <MessageSquarePlus className="w-3 h-3" />
                          {session.message_count}
                        </span>
                        <span>•</span>
                        <span className="font-mono text-[10px]">
                          {new Date(session.last_message).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={async (e) => {
                        e.stopPropagation();
                        if (confirm(`Delete "${session.title}"?`)) {
                          try {
                            await fetch(
                              `${baseURL}/delete-session/${session.session_id}`,
                              {
                                method: "DELETE",
                              }
                            );
                            await loadSessions();
                          } catch (error) {
                            console.error("Failed to delete session:", error);
                            alert("Failed to delete session");
                          }
                        }
                      }}
                      className="p-1.5 opacity-0 group-hover:opacity-100 hover:bg-red-500/20 rounded text-red-400 hover:text-red-300 transition-all flex-shrink-0"
                      title="Delete chat"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {sessions.length === 0 && (
              <div className="text-center text-xs text-gray-500 py-8">
                No conversations yet
                <div className="text-[10px] mt-1 text-gray-600">
                  Start chatting to see history
                </div>
              </div>
            )}
          </div>

          {/* Current Session Footer */}
          {sessionId && (
            <div className="p-3 border-t border-white/10 bg-black/50 flex-shrink-0">
              <div className="flex items-center justify-between text-xs mb-2">
                <span className="text-gray-400 font-semibold">
                  Active Session
                </span>
                <button
                  onClick={clearHistory}
                  className="p-1.5 hover:bg-red-500/20 rounded text-red-400 hover:text-red-300 transition-all"
                  title="Clear this session"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <div className="font-mono text-xs text-cyan-400 bg-cyan-400/10 px-2 py-1 rounded border border-cyan-400/30">
                {sessionId.slice(0, 16)}...
              </div>
            </div>
          )}
        </div>
      </motion.div>

      {/* Toggle Sidebar Button */}
      <motion.button
        onClick={() => setIsSidebarExpanded(!isSidebarExpanded)}
        animate={{ left: isSidebarExpanded ? "260px" : "0px" }}
        transition={{ duration: 0.1, ease: "easeInOut" }}
        title={isSidebarExpanded ? "Hide sidebar" : "Show sidebar"}
      >
        {isSidebarExpanded ? (
          <div className="fixed top-4 z-50 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 hover:from-cyan-500/30 hover:to-purple-500/30 border border-cyan-400/50 hover:border-cyan-400 rounded-lg p-2.5 transition-all shadow-xl backdrop-blur-md group ml-2">
            <ChevronLeft className="w-5 h-5 text-cyan-400 group-hover:text-cyan-300 transition-colors" />
          </div>
        ) : (
          <img
            src="/logo.png"
            alt="Smarix Logo"
            className="w-15 h-15 fixed top-4 z-50 p-2.5 object-contain"
          />
        )}
      </motion.button>

      <div className="flex-1 flex flex-col">
        <div className="border-b border-white/10 bg-black/40 backdrop-blur-md p-4">
          <div className="flex items-center justify-between ml-12 mr-4">
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                Chat with Your Codebase
              </h1>
              <p className="text-sm text-gray-400 mt-1">
                Ask anything about your code, flows, issues, and PRs
              </p>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full space-y-6">
              <img
                src="/logo.png"
                alt="Smarix Logo"
                className="w-20 h-20 object-contain"
              />
              <div className="text-center space-y-2">
                <h2 className="text-2xl font-bold">
                  How can I help you today?
                </h2>
                <p className="text-gray-400">
                  Ask me about your codebase, functions, architecture, or
                  anything else
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl w-full">
                {[
                  "Explain the authentication flow",
                  "Show me notification related issues and PRs",
                  "What is the architecture of the notification service?",
                  "Show me the commit history for the login feature",
                ].map((example, i) => (
                  <button
                    key={i}
                    onClick={() => setInput(example)}
                    className="p-4 text-left bg-white/5 hover:bg-white/10 border border-white/10 hover:border-cyan-400/30 rounded-lg transition-all duration-300 group"
                  >
                    <span className="text-sm text-gray-300 group-hover:text-white">
                      {example}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          <AnimatePresence>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className={`flex gap-4 ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {message.role === "assistant" && (
                  <div className="w-8 h-8 bg-gradient-to-br from-cyan-400 to-purple-500 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                )}

                <div
                  className={`max-w-4xl flex-1 ${
                    message.role === "user" ? "order-first" : ""
                  }`}
                >
                  <div
                    className={`p-5 rounded-2xl ${
                      message.role === "user"
                        ? "bg-white/5 border border-white/10 backdrop-blur-sm text-white"
                        : "bg-white/5 border border-white/10"
                    }`}
                    style={{
                      WebkitFontSmoothing: "antialiased",
                      MozOsxFontSmoothing: "grayscale",
                    }}
                  >
                    {message.role === "assistant" ? (
                      <div className="space-y-4">
                        {message.flow_data &&
                          message.flow_data.nodes &&
                          message.flow_data.nodes.length > 0 && (
                            <div className="mb-6 p-5 bg-gradient-to-br from-black/60 to-cyan-950/20 border border-cyan-400/30 rounded-xl shadow-lg">
                              <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-2">
                                  <div className="p-2 bg-cyan-500/20 rounded-lg">
                                    <Workflow className="w-5 h-5 text-cyan-400" />
                                  </div>
                                  <div>
                                    <h3 className="text-lg font-semibold text-cyan-400">
                                      Code Flow Diagram
                                    </h3>
                                    <p className="text-xs text-gray-400 mt-0.5">
                                      Interactive visualization of code
                                      structure
                                    </p>
                                  </div>
                                </div>
                                <div className="flex items-center gap-3 text-xs">
                                  <span className="px-2 py-1 bg-cyan-500/20 text-cyan-300 rounded-full">
                                    {message.flow_data.nodes.length} nodes
                                  </span>
                                  <span className="px-2 py-1 bg-purple-500/20 text-purple-300 rounded-full">
                                    {message.flow_data.edges.length} connections
                                  </span>
                                </div>
                              </div>

                              <MermaidDiagram
                                code={convertFlowDataToMermaid(
                                  message.flow_data
                                )}
                              />

                              <div className="mt-3 flex items-center gap-2 text-xs text-gray-500">
                                <div className="flex items-center gap-1.5">
                                  <div className="w-3 h-3 bg-cyan-600 rounded"></div>
                                  <span>Functions</span>
                                </div>
                                <div className="flex items-center gap-1.5">
                                  <div className="w-3 h-3 bg-purple-600 rounded"></div>
                                  <span>Classes</span>
                                </div>
                                <div className="flex items-center gap-1.5">
                                  <div className="w-3 h-3 bg-green-600 rounded"></div>
                                  <span>Methods</span>
                                </div>
                              </div>
                            </div>
                          )}

                        <div className="markdown-content prose prose-invert max-w-none antialiased">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            rehypePlugins={[rehypeHighlight, rehypeRaw]}
                            components={{
                              h1: ({ node, ...props }) => (
                                <h1
                                  className="text-2xl font-bold text-cyan-400 mb-4 mt-6 first:mt-0 border-b border-cyan-400/30 pb-2 antialiased"
                                  {...props}
                                />
                              ),
                              h2: ({ node, ...props }) => (
                                <h2
                                  className="text-xl font-bold text-purple-400 mb-3 mt-5 first:mt-0 antialiased"
                                  {...props}
                                />
                              ),
                              h3: ({ node, ...props }) => (
                                <h3
                                  className="text-lg font-semibold text-white mb-2 mt-4 first:mt-0 antialiased"
                                  {...props}
                                />
                              ),
                              p: ({ node, ...props }) => (
                                <p
                                  className="text-gray-300 leading-relaxed mb-4 last:mb-0 antialiased"
                                  {...props}
                                />
                              ),
                              ul: ({ node, ...props }) => (
                                <ul
                                  className="list-disc list-outside ml-5 space-y-2 mb-4 text-gray-300 antialiased"
                                  {...props}
                                />
                              ),
                              ol: ({ node, ...props }) => (
                                <ol
                                  className="list-decimal list-outside ml-5 space-y-2 mb-4 text-gray-300 antialiased"
                                  {...props}
                                />
                              ),
                              li: ({ node, ...props }) => (
                                <li
                                  className="text-gray-300 leading-relaxed pl-2 antialiased"
                                  {...props}
                                />
                              ),
                              code: ({
                                node,
                                inline,
                                className,
                                children,
                                ...props
                              }: any) => {
                                const match = /language-(\w+)/.exec(
                                  className || ""
                                );
                                const language = match ? match[1] : "";

                                if (!inline && language === "mermaid") {
                                  const mermaidCode = String(children).replace(
                                    /\n$/,
                                    ""
                                  );
                                  return <MermaidDiagram code={mermaidCode} />;
                                }

                                return !inline && match ? (
                                  <div className="relative group my-4">
                                    <div className="absolute right-2 top-2 z-10">
                                      <button
                                        onClick={() => {
                                          navigator.clipboard.writeText(
                                            String(children)
                                          );
                                        }}
                                        className="px-2 py-1 bg-white/10 hover:bg-white/20 rounded text-xs text-white opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1"
                                      >
                                        <Copy className="w-3 h-3" />
                                        Copy
                                      </button>
                                    </div>
                                    <pre className="!bg-black/50 !p-4 rounded-lg overflow-x-auto border border-white/10">
                                      <code
                                        className={`${className} !bg-transparent text-sm leading-relaxed`}
                                        {...props}
                                      >
                                        {children}
                                      </code>
                                    </pre>
                                  </div>
                                ) : (
                                  <code
                                    className="px-1.5 py-0.5 bg-cyan-500/20 text-cyan-300 rounded text-sm font-mono"
                                    {...props}
                                  >
                                    {children}
                                  </code>
                                );
                              },
                              blockquote: ({ node, ...props }) => (
                                <blockquote
                                  className="border-l-4 border-purple-500 pl-4 py-2 my-4 italic text-gray-400 bg-white/5 rounded-r"
                                  {...props}
                                />
                              ),
                              a: ({ node, ...props }) => (
                                <a
                                  className="text-cyan-400 hover:text-cyan-300 underline decoration-cyan-400/30 hover:decoration-cyan-300 inline-flex items-center gap-1 transition-colors"
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  {...props}
                                >
                                  {props.children}
                                  <ExternalLink className="w-3 h-3 inline" />
                                </a>
                              ),
                              table: ({ node, ...props }) => (
                                <div className="overflow-x-auto my-4 rounded-lg border border-white/10">
                                  <table className="min-w-full" {...props} />
                                </div>
                              ),
                              thead: ({ node, ...props }) => (
                                <thead className="bg-white/10" {...props} />
                              ),
                              th: ({ node, ...props }) => (
                                <th
                                  className="px-4 py-3 text-left text-cyan-400 font-semibold border-b border-white/10"
                                  {...props}
                                />
                              ),
                              td: ({ node, ...props }) => (
                                <td
                                  className="px-4 py-3 text-gray-300 border-b border-white/10"
                                  {...props}
                                />
                              ),
                              strong: ({ node, ...props }) => (
                                <strong
                                  className="font-bold text-white"
                                  {...props}
                                />
                              ),
                              em: ({ node, ...props }) => (
                                <em
                                  className="italic text-gray-300"
                                  {...props}
                                />
                              ),
                              hr: ({ node, ...props }) => (
                                <hr
                                  className="my-6 border-t border-white/20"
                                  {...props}
                                />
                              ),
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                        </div>
                      </div>
                    ) : (
                      <div className="text-white whitespace-pre-wrap">
                        {message.content}
                      </div>
                    )}

                    {message.role === "assistant" && (
                      <div className="mt-4 flex items-center gap-3 pt-4 border-t border-white/10">
                        <button
                          onClick={() =>
                            copyToClipboard(message.content, message.id)
                          }
                          className="text-xs text-gray-400 hover:text-white transition-colors flex items-center gap-1.5 px-2 py-1 hover:bg-white/5 rounded"
                        >
                          {copiedId === message.id ? (
                            <>
                              <Check className="w-3 h-3" />
                              Copied
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" />
                              Copy
                            </>
                          )}
                        </button>

                        {message.sources && message.sources.length > 0 && (
                          <button
                            onClick={() => toggleSources(message.id)}
                            className="text-xs text-gray-400 hover:text-white transition-colors flex items-center gap-1.5 px-2 py-1 hover:bg-white/5 rounded"
                          >
                            <FileCode className="w-3 h-3" />
                            {message.chunks_retrieved} sources
                            <ChevronDown
                              className={`w-3 h-3 transition-transform ${
                                showSources[message.id] ? "rotate-180" : ""
                              }`}
                            />
                          </button>
                        )}

                        {((message.related_knowledge &&
                          (message.related_knowledge.issues?.length || 0) +
                            (message.related_knowledge.prs?.length || 0) +
                            (message.related_knowledge.commits?.length || 0) >
                            0) ||
                          message.metrics_summary) && (
                          <button
                            onClick={() => toggleRelatedKnowledge(message.id)}
                            className="text-xs text-gray-400 hover:text-white transition-colors flex items-center gap-1.5 px-2 py-1 hover:bg-white/5 rounded"
                          >
                            <GitPullRequest className="w-3 h-3" />
                            Related{" "}
                            {message.related_knowledge
                              ? message.related_knowledge.issues.length +
                                message.related_knowledge.prs.length +
                                message.related_knowledge.commits.length
                              : 0}
                            {message.metrics_summary ? " • metrics" : ""}
                            <ChevronDown
                              className={`w-3 h-3 transition-transform ${
                                showRelatedKnowledge[message.id]
                                  ? "rotate-180"
                                  : ""
                              }`}
                            />
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {message.role === "user" && (
                  <div className="w-8 h-8 bg-gradient-to-br from-gray-600 to-gray-800 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
                    <User className="w-5 h-5 text-white" />
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex gap-4"
            >
              <div className="w-8 h-8 bg-gradient-to-br from-cyan-400 to-purple-500 rounded-lg flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="p-4 bg-white/5 border border-white/10 rounded-2xl">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
                  <span className="text-sm text-gray-400">
                    Searching through your codebase and related knowledge
                  </span>
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="border-t border-white/10 bg-black/40 backdrop-blur-md p-4">
          <div className="max-w-4xl mx-auto">
            <div className="relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask anything about your codebase, flows, issues, or PRs"
                disabled={isLoading}
                rows={1}
                className="w-full px-4 py-3 pr-12 bg-white/5 border border-white/10 focus:border-cyan-400/50 rounded-xl text-white placeholder-gray-500 resize-none focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed transition-colors antialiased"
                style={{
                  minHeight: "50px",
                  maxHeight: "200px",
                  WebkitFontSmoothing: "antialiased",
                  MozOsxFontSmoothing: "grayscale",
                }}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isLoading}
                className="absolute right-2 bottom-2 p-2 bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-600 hover:to-purple-600 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed rounded-lg transition-all duration-300 group"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 text-white animate-spin" />
                ) : (
                  <Send className="w-5 h-5 text-white group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                )}
              </button>
            </div>
            <div className="mt-2 text-xs text-gray-500 flex items-center gap-4">
              <span>Press Enter to send, Shift+Enter for new line</span>
              <span>GPT-4 with keyword-based retrieval</span>
            </div>
          </div>
        </div>
      </div>

      {/* Related Knowledge Drawer */}
      {messages.map((m) => {
        const isOpen = showRelatedKnowledge[m.id];
        if (!isOpen) return null;
        const rk = m.related_knowledge || { issues: [], prs: [], commits: [] };
        const metrics = m.metrics_summary;
        return (
          <div
            key={`related-${m.id}`}
            className="fixed right-4 bottom-20 w-96 max-h-[60vh] overflow-auto bg-black/80 border border-white/10 rounded-lg p-4 z-50"
          >
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-semibold">Related Knowledge</h4>
              <button
                onClick={() =>
                  setShowRelatedKnowledge((prev) => ({
                    ...prev,
                    [m.id]: false,
                  }))
                }
                className="text-xs text-gray-400 hover:text-white"
              >
                Close
              </button>
            </div>

            {metrics ? (
              <div className="mb-3 p-2 bg-white/5 rounded border border-white/10">
                <h5 className="text-xs text-cyan-300 font-medium mb-1">
                  Metrics / Tech Summary
                </h5>
                <pre className="text-xs text-gray-200 max-h-40 overflow-auto p-2 bg-black/60 rounded">
                  {JSON.stringify(metrics, null, 2)}
                </pre>
              </div>
            ) : null}

            <div>
              {rk.issues && rk.issues.length > 0 && (
                <div className="mb-3">
                  <h6 className="text-xs text-purple-300 font-medium mb-1">
                    Issues
                  </h6>
                  {rk.issues.map((it: any) => (
                    <div
                      key={it.number}
                      className="p-2 bg-white/3 rounded mb-2"
                    >
                      <div className="flex items-center justify-between text-sm">
                        <div>
                          <div className="font-semibold">{it.title}</div>
                          <div className="text-xs text-gray-400">
                            #{it.number} • {it.status}
                          </div>
                        </div>
                        <a
                          className="text-xs text-cyan-300"
                          href={it.url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Open
                        </a>
                      </div>
                      {it.description && (
                        <div className="text-xs text-gray-300 mt-1">
                          {it.description.slice(0, 300)}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {rk.prs && rk.prs.length > 0 && (
                <div className="mb-3">
                  <h6 className="text-xs text-cyan-300 font-medium mb-1">
                    PRs
                  </h6>
                  {rk.prs.map((pr: any) => (
                    <div
                      key={pr.number}
                      className="p-2 bg-white/3 rounded mb-2"
                    >
                      <div className="flex items-center justify-between text-sm">
                        <div>
                          <div className="font-semibold">{pr.title}</div>
                          <div className="text-xs text-gray-400">
                            #{pr.number} • {pr.status}
                          </div>
                        </div>
                        <a
                          className="text-xs text-cyan-300"
                          href={pr.url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Open
                        </a>
                      </div>
                      {pr.description && (
                        <div className="text-xs text-gray-300 mt-1">
                          {pr.description.slice(0, 300)}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {rk.commits && rk.commits.length > 0 && (
                <div className="mb-3">
                  <h6 className="text-xs text-green-300 font-medium mb-1">
                    Commits
                  </h6>
                  {rk.commits.map((c: any) => (
                    <div key={c.sha} className="p-2 bg-white/3 rounded mb-2">
                      <div className="flex items-center justify-between text-sm">
                        <div>
                          <div className="font-semibold">
                            {c.message?.slice(0, 120) || c.sha}
                          </div>
                          <div className="text-xs text-gray-400">
                            {c.author}
                          </div>
                        </div>
                        <a
                          className="text-xs text-cyan-300"
                          href={c.url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Open
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {!metrics &&
                rk.issues.length === 0 &&
                rk.prs.length === 0 &&
                rk.commits.length === 0 && (
                  <div className="text-xs text-gray-400">
                    No related items found.
                  </div>
                )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
