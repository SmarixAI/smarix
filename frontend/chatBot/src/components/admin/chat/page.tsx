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
  History,
  MessageSquare,
  ArrowLeft,
  LogOut,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Fira_Code, Space_Grotesk } from "next/font/google";
import Image from "next/image";
import { useAuth } from "@/components/auth/AuthContext";
import { formatResponseForUI } from "@/utils/responseFormatter";

const firaCode = Fira_Code({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  display: "swap",
});

if (typeof window !== "undefined") {
  mermaid.initialize({
    startOnLoad: false,
    theme: "default",
    logLevel: "error",
    securityLevel: "loose",
    themeVariables: {
      primaryColor: "#0E1B2E",
      primaryTextColor: "#FAFAFA",
      primaryBorderColor: "#0E1B2E",
      lineColor: "#0E1B2E",
      secondaryColor: "#1a2f4d",
      tertiaryColor: "#FAFAFA",
      background: "#FAFAFA",
      mainBkg: "#FFFFFF",
      nodeBorder: "#0E1B2E",
      clusterBkg: "#F5F5F5",
      clusterBorder: "#0E1B2E",
      titleColor: "#0E1B2E",
      edgeLabelBackground: "#FFFFFF",
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
      <div className="text-red-600 text-sm p-4 bg-red-50 border border-red-200 rounded-lg my-4">
        <p className="font-semibold mb-1 text-[#0E1B2E]">Failed to render diagram</p>
        <p className="text-xs text-red-700/70">{error}</p>
        <details className="mt-2">
          <summary className="cursor-pointer text-xs text-[#0E1B2E]/70 hover:text-[#0E1B2E]">
            Show code
          </summary>
          <pre className="mt-2 text-xs bg-[#0E1B2E]/5 p-2 rounded overflow-x-auto border border-[#0E1B2E]/10">
            {code}
          </pre>
        </details>
      </div>
    );
  }

  return (
    <div className="my-4 bg-white/60 backdrop-blur-sm rounded-xl border border-[#0E1B2E]/10 shadow-sm relative">
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/80 backdrop-blur-sm z-10 rounded-xl">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0E1B2E]"></div>
        </div>
      )}

      {!isLoading && (
        <div className="absolute top-2 right-2 z-20 flex items-center gap-1 bg-white/80 backdrop-blur-md rounded-lg p-1 border border-[#0E1B2E]/10 shadow-sm">
          <button
            onClick={handleZoomOut}
            className="p-1.5 hover:bg-[#0E1B2E]/5 rounded transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4 text-[#0E1B2E]" />
          </button>

          <div className="px-2 py-0.5 min-w-[50px] text-center">
            <span className={`text-xs text-[#0E1B2E] ${firaCode.className}`}>
              {(zoom * 100).toFixed(0)}%
            </span>
          </div>

          <button
            onClick={handleZoomIn}
            className="p-1.5 hover:bg-[#0E1B2E]/5 rounded transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4 text-[#0E1B2E]" />
          </button>

          <button
            onClick={handleReset}
            className="p-1.5 hover:bg-[#0E1B2E]/5 rounded transition-colors"
            title="Reset Zoom"
          >
            <RotateCcw className="w-4 h-4 text-[#0E1B2E]" />
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
  const router = useRouter();
  const { user, logout, isAuthenticated } = useAuth();
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
  const [sidebarView, setSidebarView] = useState<"sessions" | "messages">("sessions");
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);
  const [selectedRole, setSelectedRole] = useState<"onboarding" | "offboarding" | "general">("general");
  const messageRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});
  
  // Check if user has status "general"
  const showUserInfo = isAuthenticated && user && user.status === "general";

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
    let mermaidCode = `%%{init: {'theme':'default', 'themeVariables': {'primaryColor':'#0E1B2E','primaryTextColor':'#FAFAFA','primaryBorderColor':'#0E1B2E','lineColor':'#0E1B2E','secondaryColor':'#1a2f4d','tertiaryColor':'#FAFAFA'},'flowchart':{'defaultRenderer':'elk','htmlLabels':true,'curve':'basis'}}}%%\n`;
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

  const scrollToMessage = (messageId: string) => {
    const messageElement = messageRefs.current[messageId];
    if (messageElement) {
      messageElement.scrollIntoView({ behavior: "smooth", block: "center" });
      setSelectedMessageId(messageId);
      // Remove highlight after 2 seconds
      setTimeout(() => setSelectedMessageId(null), 2000);
    }
  };

  const getMessagePreview = (content: string, maxLength: number = 60) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + "...";
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

      const requestBody: { query: string; session_id?: string; username?: string; role?: string } = {
        query: input,
        role: selectedRole,
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
    <div className="flex h-screen bg-[#FAFAFA] text-[#0E1B2E] antialiased relative selection:bg-[#0E1B2E] selection:text-white">
      {/* Background Grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
      {/* Sidebar */}
      <motion.div
        initial={false}
        className="w-80 border-r border-[#0E1B2E]/10 bg-white/60 backdrop-blur-xl flex flex-col overflow-hidden shadow-sm relative z-10"
        style={{
          WebkitFontSmoothing: "antialiased",
          MozOsxFontSmoothing: "grayscale",
        }}
      >
        <div className="flex flex-col h-full w-80">
          {/* Header */}
          <div className="p-4 border-b border-[#0E1B2E]/10 flex-shrink-0 bg-white/40 backdrop-blur-sm">
            <Link href="/" className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-[#0E1B2E] rounded-lg flex items-center justify-center overflow-hidden">
                <Image
                  src="/logo.png"
                  alt="Smarix Logo"
                  width={24}
                  height={24}
                  className="w-6 h-6 object-contain"
                />
              </div>
              <span className={`${spaceGrotesk.className} font-bold text-lg text-[#0E1B2E]`}>Smarix</span>
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
              className="w-full p-3 bg-[#0E1B2E] hover:bg-[#1a2f4d] text-white rounded-lg transition-all flex items-center justify-center gap-2 group hover:scale-[1.02] active:scale-[0.98] shadow-md hover:shadow-lg hover:shadow-[#0E1B2E]/20"
            >
              <MessageSquarePlus className="w-5 h-5 group-hover:rotate-12 transition-transform" />
              <span className={`text-sm font-medium ${spaceGrotesk.className}`}>New Chat</span>
            </button>

            {/* Stats */}
            {stats && (
              <div className="mt-4 p-3 bg-white/60 backdrop-blur-sm rounded-lg border border-[#0E1B2E]/10 shadow-sm">
                <div className="flex items-center gap-2 mb-2">
                  <Database className="w-4 h-4 text-[#0E1B2E]" />
                  <span className={`text-xs font-semibold text-[#0E1B2E] ${spaceGrotesk.className}`}>
                    Database Stats
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-[#0E1B2E]/70">Total Chunks</span>
                  <span className={`text-sm ${firaCode.className} text-[#0E1B2E]`}>
                    {stats.total_chunks?.toLocaleString()}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar View Toggle */}
          <div className="px-3 pt-3 pb-2 border-b border-[#0E1B2E]/10 bg-white/30 flex-shrink-0">
            <div className="relative">
              <button
                onClick={() => setSidebarView(sidebarView === "sessions" ? "messages" : "sessions")}
                className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-white/60 backdrop-blur-sm transition-colors group"
              >
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-[#0E1B2E]" />
                  <span className={`text-xs font-semibold text-[#0E1B2E] ${spaceGrotesk.className}`}>
                    {sidebarView === "sessions" ? "Recent Chats" : "Chat History"}
                  </span>
                  {sidebarView === "sessions" && messages.length > 0 && (
                    <span className={`${firaCode.className} text-[10px] bg-[#0E1B2E]/10 text-[#0E1B2E] px-1.5 py-0.5 rounded`}>
                      {messages.length}
                    </span>
                  )}
                </div>
                <ChevronDown className={`w-4 h-4 text-[#0E1B2E]/60 transition-transform ${sidebarView === "messages" ? "rotate-180" : ""}`} />
              </button>
            </div>
          </div>

          {/* Sessions List */}
          <div className="flex-1 overflow-y-auto p-3 bg-white/20" id="sessions-container">
            {sidebarView === "sessions" && (
              <>
                <div className="mb-2 flex items-center justify-between px-2">
                  <span className={`text-xs font-semibold text-[#0E1B2E]/70 uppercase tracking-wider ${spaceGrotesk.className}`}>
                    Recent Chats
                  </span>
                  <Clock className="w-3.5 h-3.5 text-[#0E1B2E]/50" />
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
                      ? "bg-[#0E1B2E] text-white border border-[#0E1B2E] shadow-lg"
                      : "hover:bg-white/60 backdrop-blur-sm border border-transparent hover:border-[#0E1B2E]/20 bg-white/40"
                  }`}
                  onClick={() => loadSession(session.session_id)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className={`text-sm font-medium truncate mb-1 ${selectedSessionId === session.session_id ? 'text-white' : 'text-[#0E1B2E]'} ${spaceGrotesk.className}`}>
                        {session.title}
                      </div>
                      <div className={`flex items-center gap-2 text-xs ${selectedSessionId === session.session_id ? 'text-white/70' : 'text-[#0E1B2E]/60'}`}>
                        <span className="flex items-center gap-1">
                          <MessageSquarePlus className="w-3 h-3" />
                          {session.message_count}
                        </span>
                        <span>•</span>
                        <span className={`${firaCode.className} text-[10px]`}>
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
                      className={`p-1.5 opacity-0 group-hover:opacity-100 hover:bg-red-100 rounded transition-all flex-shrink-0 ${selectedSessionId === session.session_id ? 'text-red-300 hover:text-red-200' : 'text-red-500 hover:text-red-600'}`}
                      title="Delete chat"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

                {sessions.length === 0 && (
                  <div className={`text-center text-xs text-[#0E1B2E]/60 py-8 ${spaceGrotesk.className}`}>
                    No conversations yet
                    <div className="text-[10px] mt-1 text-[#0E1B2E]/40">
                      Start chatting to see history
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Chat History View */}
            {sidebarView === "messages" && (
              <>
                <div className="mb-2 flex items-center justify-between px-2">
                  <span className={`text-xs font-semibold text-[#0E1B2E]/70 uppercase tracking-wider ${spaceGrotesk.className}`}>
                    Current Chat
                  </span>
                  <MessageSquare className="w-3.5 h-3.5 text-[#0E1B2E]/50" />
                </div>
                <div className="px-2 mb-2">
                  <p className={`${firaCode.className} text-xs text-[#0E1B2E]/60`}>
                    {messages.length} {messages.length === 1 ? "message" : "messages"}
                  </p>
                </div>
                <div className="space-y-1">
                  {messages.map((message) => (
                    <motion.button
                      key={message.id}
                      onClick={() => scrollToMessage(message.id)}
                      whileHover={{ x: 2 }}
                      className={`w-full text-left px-3 py-2 rounded-lg transition-colors mb-1 ${
                        selectedMessageId === message.id
                          ? "bg-[#0E1B2E] text-white border border-[#0E1B2E] shadow-lg"
                          : "hover:bg-white/60 backdrop-blur-sm border border-transparent hover:border-[#0E1B2E]/20 bg-white/40"
                      }`}
                    >
                      <div className="flex items-start space-x-2">
                        <div
                          className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                            message.role === "user"
                              ? selectedMessageId === message.id
                                ? "bg-white/20"
                                : "bg-[#0E1B2E]"
                              : selectedMessageId === message.id
                              ? "bg-white/20"
                              : "bg-[#0E1B2E]/80"
                          }`}
                        >
                          {message.role === "user" ? (
                            <User className="w-3 h-3 text-white" />
                          ) : (
                            <Bot className="w-3 h-3 text-white" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-0.5">
                            <span
                              className={`${spaceGrotesk.className} text-xs font-medium ${
                                selectedMessageId === message.id
                                  ? "text-white"
                                  : message.role === "user"
                                  ? "text-[#0E1B2E]"
                                  : "text-[#0E1B2E]/80"
                              }`}
                            >
                              {message.role === "user" ? "You" : "Assistant"}
                            </span>
                            <span
                              className={`${firaCode.className} text-[10px] ${
                                selectedMessageId === message.id
                                  ? "text-white/70"
                                  : "text-[#0E1B2E]/50"
                              }`}
                            >
                              {message.timestamp.toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </span>
                          </div>
                          <p
                            className={`${spaceGrotesk.className} text-xs line-clamp-2 ${
                              selectedMessageId === message.id
                                ? "text-white/90"
                                : "text-[#0E1B2E]/70"
                            }`}
                          >
                            {getMessagePreview(message.content)}
                          </p>
                        </div>
                      </div>
                    </motion.button>
                  ))}
                </div>
                {messages.length === 0 && (
                  <div className={`text-center text-xs text-[#0E1B2E]/60 py-8 ${spaceGrotesk.className}`}>
                    No messages yet
                    <div className="text-[10px] mt-1 text-[#0E1B2E]/40">
                      Start chatting to see message history
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Current Session Footer */}
          {sessionId && (
            <div className="p-3 border-t border-[#0E1B2E]/10 bg-white/60 backdrop-blur-sm flex-shrink-0">
              <div className="flex items-center justify-between text-xs mb-2">
                <span className={`text-[#0E1B2E]/70 font-semibold ${spaceGrotesk.className}`}>
                  Active Session
                </span>
                <button
                  onClick={clearHistory}
                  className="p-1.5 hover:bg-red-100 rounded text-red-500 hover:text-red-600 transition-all"
                  title="Clear this session"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <div className={`${firaCode.className} text-xs text-[#0E1B2E] bg-[#0E1B2E]/5 px-2 py-1 rounded border border-[#0E1B2E]/10`}>
                {sessionId.slice(0, 16)}...
              </div>
            </div>
          )}
        </div>
      </motion.div>

      <div className="flex-1 flex flex-col relative z-10">
        <div className="border-b border-[#0E1B2E]/10 bg-white/60 backdrop-blur-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 flex-1">
              <button
                onClick={() => router.back()}
                className="p-2 hover:bg-[#0E1B2E]/10 rounded-lg transition-colors"
                title="Go back"
              >
                <ArrowLeft className="w-5 h-5 text-[#0E1B2E]" />
              </button>
              <div>
                <h1 className={`text-xl font-bold text-[#0E1B2E] ${spaceGrotesk.className}`}>
                  Chat with Your Codebase
                </h1>
                <p className={`text-sm text-[#0E1B2E]/70 mt-1 ${spaceGrotesk.className}`}>
                  Ask anything about your code, flows, issues, and PRs
                </p>
              </div>
            </div>
            {showUserInfo && (
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 px-3 py-2 bg-white/80 rounded-lg border border-[#0E1B2E]/10">
                  <User className="w-4 h-4 text-[#0E1B2E]" />
                  <span className={`text-sm font-medium text-[#0E1B2E] ${spaceGrotesk.className}`}>
                    {user.name || user.username}
                  </span>
                </div>
                <button
                  onClick={() => logout()}
                  className="flex items-center gap-2 px-3 py-2 bg-[#0E1B2E] text-white rounded-lg hover:bg-[#0E1B2E]/90 transition-colors"
                  title="Logout"
                >
                  <LogOut className="w-4 h-4" />
                  <span className={`text-sm font-medium ${spaceGrotesk.className}`}>
                    Logout
                  </span>
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full space-y-6">
              <div className="w-20 h-20 bg-[#0E1B2E] rounded-2xl flex items-center justify-center overflow-hidden shadow-lg">
                <Image
                  src="/logo.png"
                  alt="Smarix Logo"
                  width={48}
                  height={48}
                  className="w-12 h-12 object-contain"
                />
              </div>
              <div className="text-center space-y-2">
                <h2 className={`text-2xl font-bold text-[#0E1B2E] ${spaceGrotesk.className}`}>
                  How can I help you today?
                </h2>
                <p className={`text-[#0E1B2E]/70 ${spaceGrotesk.className}`}>
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
                    className="p-4 text-left bg-white/60 backdrop-blur-sm hover:bg-white/80 border border-[#0E1B2E]/10 hover:border-[#0E1B2E]/30 rounded-lg transition-all duration-300 group shadow-sm hover:shadow-md"
                  >
                    <span className={`text-sm text-[#0E1B2E] group-hover:text-[#1a2f4d] ${spaceGrotesk.className}`}>
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
                ref={(el) => {
                  messageRefs.current[message.id] = el;
                }}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className={`flex gap-4 transition-all duration-300 ${
                  message.role === "user" ? "justify-end" : "justify-start"
                } ${
                  selectedMessageId === message.id
                    ? "bg-[#0E1B2E]/5 rounded-lg px-2 py-1 -mx-2 -my-1"
                    : ""
                }`}
              >
                {message.role === "assistant" && (
                  <div className="w-8 h-8 bg-[#0E1B2E] rounded-lg flex items-center justify-center flex-shrink-0 mt-1 shadow-md">
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
                        ? "bg-[#0E1B2E] text-white border border-[#0E1B2E] shadow-md"
                        : "bg-white/60 backdrop-blur-sm border border-[#0E1B2E]/10 shadow-sm"
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
                            <div className="mb-6 p-5 bg-white/60 backdrop-blur-sm border border-[#0E1B2E]/10 rounded-xl shadow-md">
                              <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-2">
                                  <div className="p-2 bg-[#0E1B2E]/10 rounded-lg">
                                    <Workflow className="w-5 h-5 text-[#0E1B2E]" />
                                  </div>
                                  <div>
                                    <h3 className={`text-lg font-semibold text-[#0E1B2E] ${spaceGrotesk.className}`}>
                                      Code Flow Diagram
                                    </h3>
                                    <p className={`text-xs text-[#0E1B2E]/60 mt-0.5 ${spaceGrotesk.className}`}>
                                      Interactive visualization of code
                                      structure
                                    </p>
                                  </div>
                                </div>
                                <div className="flex items-center gap-3 text-xs">
                                  <span className={`px-2 py-1 bg-[#0E1B2E]/10 text-[#0E1B2E] rounded-full ${spaceGrotesk.className}`}>
                                    {message.flow_data.nodes.length} nodes
                                  </span>
                                  <span className={`px-2 py-1 bg-[#0E1B2E]/10 text-[#0E1B2E] rounded-full ${spaceGrotesk.className}`}>
                                    {message.flow_data.edges.length} connections
                                  </span>
                                </div>
                              </div>

                              <MermaidDiagram
                                code={convertFlowDataToMermaid(
                                  message.flow_data
                                )}
                              />

                              <div className={`mt-3 flex items-center gap-2 text-xs text-[#0E1B2E]/70 ${spaceGrotesk.className}`}>
                                <div className="flex items-center gap-1.5">
                                  <div className="w-3 h-3 bg-[#0E1B2E] rounded"></div>
                                  <span>Functions</span>
                                </div>
                                <div className="flex items-center gap-1.5">
                                  <div className="w-3 h-3 bg-[#0E1B2E]/70 rounded"></div>
                                  <span>Classes</span>
                                </div>
                                <div className="flex items-center gap-1.5">
                                  <div className="w-3 h-3 bg-[#0E1B2E]/50 rounded"></div>
                                  <span>Methods</span>
                                </div>
                              </div>
                            </div>
                          )}

                        <div className="markdown-content prose max-w-none antialiased">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            rehypePlugins={[rehypeHighlight, rehypeRaw]}
                            components={{
                              h1: ({ node, ...props }) => (
                                <h1
                                  className={`text-2xl font-bold text-[#0E1B2E] mb-4 mt-6 first:mt-0 border-b border-[#0E1B2E]/20 pb-2 antialiased ${spaceGrotesk.className}`}
                                  {...props}
                                />
                              ),
                              h2: ({ node, ...props }) => (
                                <h2
                                  className={`text-xl font-bold text-[#0E1B2E] mb-3 mt-5 first:mt-0 antialiased ${spaceGrotesk.className}`}
                                  {...props}
                                />
                              ),
                              h3: ({ node, ...props }) => (
                                <h3
                                  className={`text-lg font-semibold text-[#0E1B2E] mb-2 mt-4 first:mt-0 antialiased ${spaceGrotesk.className}`}
                                  {...props}
                                />
                              ),
                              p: ({ node, ...props }) => (
                                <p
                                  className={`text-[#0E1B2E]/80 leading-relaxed mb-4 last:mb-0 antialiased ${spaceGrotesk.className}`}
                                  {...props}
                                />
                              ),
                              ul: ({ node, ...props }) => (
                                <ul
                                  className={`list-disc list-outside ml-5 space-y-2 mb-4 text-[#0E1B2E]/80 antialiased ${spaceGrotesk.className}`}
                                  {...props}
                                />
                              ),
                              ol: ({ node, ...props }) => (
                                <ol
                                  className={`list-decimal list-outside ml-5 space-y-2 mb-4 text-[#0E1B2E]/80 antialiased ${spaceGrotesk.className}`}
                                  {...props}
                                />
                              ),
                              li: ({ node, ...props }) => (
                                <li
                                  className={`text-[#0E1B2E]/80 leading-relaxed pl-2 antialiased ${spaceGrotesk.className}`}
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
                                        className="px-2 py-1 bg-[#0E1B2E]/10 hover:bg-[#0E1B2E]/20 rounded text-xs text-[#0E1B2E] opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1"
                                      >
                                        <Copy className="w-3 h-3" />
                                        Copy
                                      </button>
                                    </div>
                                    <pre className="!bg-[#0E1B2E]/5 !p-4 rounded-lg overflow-x-auto border border-[#0E1B2E]/10">
                                      <code
                                        className={`${className} !bg-transparent text-sm leading-relaxed ${firaCode.className}`}
                                        {...props}
                                      >
                                        {children}
                                      </code>
                                    </pre>
                                  </div>
                                ) : (
                                  <code
                                    className={`px-1.5 py-0.5 bg-[#0E1B2E]/10 text-[#0E1B2E] rounded text-sm ${firaCode.className}`}
                                    {...props}
                                  >
                                    {children}
                                  </code>
                                );
                              },
                              blockquote: ({ node, ...props }) => (
                                <blockquote
                                  className={`border-l-4 border-[#0E1B2E]/30 pl-4 py-2 my-4 italic text-[#0E1B2E]/70 bg-[#0E1B2E]/5 rounded-r ${spaceGrotesk.className}`}
                                  {...props}
                                />
                              ),
                              a: ({ node, ...props }) => (
                                <a
                                  className="text-[#0E1B2E] hover:text-[#1a2f4d] underline decoration-[#0E1B2E]/30 hover:decoration-[#1a2f4d] inline-flex items-center gap-1 transition-colors"
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  {...props}
                                >
                                  {props.children}
                                  <ExternalLink className="w-3 h-3 inline" />
                                </a>
                              ),
                              table: ({ node, ...props }) => (
                                <div className="overflow-x-auto my-4 rounded-lg border border-[#0E1B2E]/10">
                                  <table className="min-w-full" {...props} />
                                </div>
                              ),
                              thead: ({ node, ...props }) => (
                                <thead className="bg-[#0E1B2E]/5" {...props} />
                              ),
                              th: ({ node, ...props }) => (
                                <th
                                  className={`px-4 py-3 text-left text-[#0E1B2E] font-semibold border-b border-[#0E1B2E]/10 ${spaceGrotesk.className}`}
                                  {...props}
                                />
                              ),
                              td: ({ node, ...props }) => (
                                <td
                                  className={`px-4 py-3 text-[#0E1B2E]/80 border-b border-[#0E1B2E]/10 ${spaceGrotesk.className}`}
                                  {...props}
                                />
                              ),
                              strong: ({ node, ...props }) => (
                                <strong
                                  className={`font-bold text-[#0E1B2E] ${spaceGrotesk.className}`}
                                  {...props}
                                />
                              ),
                              em: ({ node, ...props }) => (
                                <em
                                  className={`italic text-[#0E1B2E]/80 ${spaceGrotesk.className}`}
                                  {...props}
                                />
                              ),
                              hr: ({ node, ...props }) => (
                                <hr
                                  className="my-6 border-t border-[#0E1B2E]/20"
                                  {...props}
                                />
                              ),
                            }}
                          >
                            {formatResponseForUI(message.content)}
                          </ReactMarkdown>
                        </div>
                      </div>
                    ) : (
                      <div className="text-white whitespace-pre-wrap">
                        {message.content}
                      </div>
                    )}

                    {message.role === "assistant" && (
                      <div className="mt-4 flex items-center gap-3 pt-4 border-t border-[#0E1B2E]/10">
                        <button
                          onClick={() =>
                            copyToClipboard(message.content, message.id)
                          }
                          className={`text-xs text-[#0E1B2E]/70 hover:text-[#0E1B2E] transition-colors flex items-center gap-1.5 px-2 py-1 hover:bg-[#0E1B2E]/5 rounded ${spaceGrotesk.className}`}
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
                            className={`text-xs text-[#0E1B2E]/70 hover:text-[#0E1B2E] transition-colors flex items-center gap-1.5 px-2 py-1 hover:bg-[#0E1B2E]/5 rounded ${spaceGrotesk.className}`}
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
                            className={`text-xs text-[#0E1B2E]/70 hover:text-[#0E1B2E] transition-colors flex items-center gap-1.5 px-2 py-1 hover:bg-[#0E1B2E]/5 rounded ${spaceGrotesk.className}`}
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

                    {/* Sources Display */}
                    {message.role === "assistant" &&
                      showSources[message.id] &&
                      message.sources &&
                      message.sources.length > 0 && (
                        <AnimatePresence>
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: "auto" }}
                            exit={{ opacity: 0, height: 0 }}
                            className="mt-4 space-y-2 p-4 bg-white/40 backdrop-blur-sm rounded-lg border border-[#0E1B2E]/10"
                          >
                            <h4 className={`text-sm font-semibold text-[#0E1B2E] mb-3 ${spaceGrotesk.className}`}>
                              Sources ({message.sources.length})
                            </h4>
                            <div className="space-y-2">
                              {message.sources.map((source, idx) => (
                                <div
                                  key={idx}
                                  className="p-3 bg-white/60 backdrop-blur-sm rounded-lg border border-[#0E1B2E]/10 hover:border-[#0E1B2E]/20 transition-colors"
                                >
                                  <div className="flex items-start justify-between gap-2">
                                    <div className="flex items-start gap-2 flex-1">
                                      {getContentIcon(source.content_type)}
                                      <div className="flex-1 min-w-0">
                                        <div className={`text-sm font-medium text-[#0E1B2E] truncate ${spaceGrotesk.className}`}>
                                          {formatFileName(source)}
                                        </div>
                                        {source.type && (
                                          <div className={`text-xs text-[#0E1B2E]/60 mt-1 ${spaceGrotesk.className}`}>
                                            {source.type}
                                          </div>
                                        )}
                                        {source.score && (
                                          <div className={`text-xs text-[#0E1B2E]/50 mt-1 ${firaCode.className}`}>
                                            Score: {(source.score * 100).toFixed(1)}%
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                    {(source.url || source.html_url) && (
                                      <a
                                        href={source.url || source.html_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-[#0E1B2E] hover:text-[#1a2f4d] transition-colors"
                                      >
                                        <ExternalLink className="w-4 h-4" />
                                      </a>
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </motion.div>
                        </AnimatePresence>
                      )}
                  </div>
                </div>

                {message.role === "user" && (
                  <div className="w-8 h-8 bg-[#0E1B2E]/20 border border-[#0E1B2E]/20 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
                    <User className="w-5 h-5 text-[#0E1B2E]" />
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
              <div className="w-8 h-8 bg-[#0E1B2E] rounded-lg flex items-center justify-center shadow-md">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="p-4 bg-white/60 backdrop-blur-sm border border-[#0E1B2E]/10 rounded-2xl shadow-sm">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-[#0E1B2E]" />
                  <span className={`text-sm text-[#0E1B2E]/70 ${spaceGrotesk.className}`}>
                    Searching through your codebase and related knowledge
                  </span>
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="border-t border-[#0E1B2E]/10 bg-white/60 backdrop-blur-xl p-4 shadow-sm">
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
                className={`w-full px-4 py-3 pr-12 bg-white/80 backdrop-blur-sm border border-[#0E1B2E]/20 focus:border-[#0E1B2E] rounded-xl text-[#0E1B2E] placeholder-[#0E1B2E]/40 resize-none focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed transition-colors antialiased shadow-sm ${spaceGrotesk.className}`}
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
                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-[#0E1B2E] hover:bg-[#1a2f4d] disabled:bg-[#0E1B2E]/30 disabled:cursor-not-allowed rounded-lg transition-all duration-300 group shadow-md hover:shadow-lg hover:shadow-[#0E1B2E]/20 flex items-center justify-center"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 text-white animate-spin" />
                ) : (
                  <Send className="w-5 h-5 text-white group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                )}
              </button>
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
            className="fixed right-4 bottom-20 w-96 max-h-[60vh] overflow-auto bg-white/90 backdrop-blur-xl border border-[#0E1B2E]/20 rounded-xl p-4 z-50 shadow-2xl"
          >
            <div className="flex items-center justify-between mb-2">
              <h4 className={`text-sm font-semibold text-[#0E1B2E] ${spaceGrotesk.className}`}>Related Knowledge</h4>
              <button
                onClick={() =>
                  setShowRelatedKnowledge((prev) => ({
                    ...prev,
                    [m.id]: false,
                  }))
                }
                className={`text-xs text-[#0E1B2E]/70 hover:text-[#0E1B2E] ${spaceGrotesk.className}`}
              >
                Close
              </button>
            </div>

            {metrics ? (
              <div className="mb-3 p-2 bg-[#0E1B2E]/5 rounded-lg border border-[#0E1B2E]/10">
                <h5 className={`text-xs text-[#0E1B2E] font-medium mb-1 ${spaceGrotesk.className}`}>
                  Metrics / Tech Summary
                </h5>
                <pre className={`text-xs text-[#0E1B2E]/80 max-h-40 overflow-auto p-2 bg-[#0E1B2E]/5 rounded ${firaCode.className}`}>
                  {JSON.stringify(metrics, null, 2)}
                </pre>
              </div>
            ) : null}

            <div>
              {rk.issues && rk.issues.length > 0 && (
                <div className="mb-3">
                  <h6 className={`text-xs text-[#0E1B2E] font-medium mb-1 ${spaceGrotesk.className}`}>
                    Issues
                  </h6>
                  {rk.issues.map((it: any) => (
                    <div
                      key={it.number}
                      className="p-2 bg-[#0E1B2E]/5 rounded-lg mb-2 border border-[#0E1B2E]/10"
                    >
                      <div className="flex items-center justify-between text-sm">
                        <div>
                          <div className={`font-semibold text-[#0E1B2E] ${spaceGrotesk.className}`}>{it.title}</div>
                          <div className={`text-xs text-[#0E1B2E]/60 ${spaceGrotesk.className}`}>
                            #{it.number} • {it.status}
                          </div>
                        </div>
                        <a
                          className={`text-xs text-[#0E1B2E] hover:text-[#1a2f4d] ${spaceGrotesk.className}`}
                          href={it.url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Open
                        </a>
                      </div>
                      {it.description && (
                        <div className={`text-xs text-[#0E1B2E]/70 mt-1 ${spaceGrotesk.className}`}>
                          {it.description.slice(0, 300)}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {rk.prs && rk.prs.length > 0 && (
                <div className="mb-3">
                  <h6 className={`text-xs text-[#0E1B2E] font-medium mb-1 ${spaceGrotesk.className}`}>
                    PRs
                  </h6>
                  {rk.prs.map((pr: any) => (
                    <div
                      key={pr.number}
                      className="p-2 bg-[#0E1B2E]/5 rounded-lg mb-2 border border-[#0E1B2E]/10"
                    >
                      <div className="flex items-center justify-between text-sm">
                        <div>
                          <div className={`font-semibold text-[#0E1B2E] ${spaceGrotesk.className}`}>{pr.title}</div>
                          <div className={`text-xs text-[#0E1B2E]/60 ${spaceGrotesk.className}`}>
                            #{pr.number} • {pr.status}
                          </div>
                        </div>
                        <a
                          className={`text-xs text-[#0E1B2E] hover:text-[#1a2f4d] ${spaceGrotesk.className}`}
                          href={pr.url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Open
                        </a>
                      </div>
                      {pr.description && (
                        <div className={`text-xs text-[#0E1B2E]/70 mt-1 ${spaceGrotesk.className}`}>
                          {pr.description.slice(0, 300)}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {rk.commits && rk.commits.length > 0 && (
                <div className="mb-3">
                  <h6 className={`text-xs text-[#0E1B2E] font-medium mb-1 ${spaceGrotesk.className}`}>
                    Commits
                  </h6>
                  {rk.commits.map((c: any) => (
                    <div key={c.sha} className="p-2 bg-[#0E1B2E]/5 rounded-lg mb-2 border border-[#0E1B2E]/10">
                      <div className="flex items-center justify-between text-sm">
                        <div>
                          <div className={`font-semibold text-[#0E1B2E] ${spaceGrotesk.className}`}>
                            {c.message?.slice(0, 120) || c.sha}
                          </div>
                          <div className={`text-xs text-[#0E1B2E]/60 ${spaceGrotesk.className}`}>
                            {c.author}
                          </div>
                        </div>
                        <a
                          className={`text-xs text-[#0E1B2E] hover:text-[#1a2f4d] ${spaceGrotesk.className}`}
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
                  <div className={`text-xs text-[#0E1B2E]/60 ${spaceGrotesk.className}`}>
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
