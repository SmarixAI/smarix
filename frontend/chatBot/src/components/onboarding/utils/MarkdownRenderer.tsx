'use client';

import React, { ReactNode, useRef, useState, useEffect } from 'react';
import mermaid from 'mermaid';
import { ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

interface MarkdownRendererProps {
  content: string;
  className?: string;
  isFullscreen?: boolean;
}

// Initialize mermaid once
if (typeof window !== "undefined" && !(window as any).mermaidInitialized) {
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
      fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
    },
    flowchart: {
      htmlLabels: true,
      curve: "basis",
      useMaxWidth: true,
      defaultRenderer: "elk",
      padding: 20,
    },
  });
  (window as any).mermaidInitialized = true;
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
            <span className="text-xs text-[#0E1B2E] font-mono">
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

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  className = '',
  isFullscreen = false,
}) => {
  const parseMarkdown = (text: string): ReactNode[] => {
    const parts: ReactNode[] = [];
    let lastIndex = 0;
    
    // First, extract mermaid code blocks
    const mermaidRegex = /```mermaid\n([\s\S]*?)```/g;
    const mermaidBlocks: Array<{ start: number; end: number; code: string }> = [];
    let mermaidMatch;
    
    while ((mermaidMatch = mermaidRegex.exec(text)) !== null) {
      mermaidBlocks.push({
        start: mermaidMatch.index,
        end: mermaidMatch.index + mermaidMatch[0].length,
        code: mermaidMatch[1].trim(),
      });
    }
    
    // If we have mermaid blocks, split the text and insert mermaid components
    if (mermaidBlocks.length > 0) {
      let currentIndex = 0;
      
      mermaidBlocks.forEach((block, idx) => {
        // Add text before mermaid block
        if (block.start > currentIndex) {
          const textBefore = text.substring(currentIndex, block.start);
          if (textBefore.trim()) {
            parts.push(...parseTextContent(textBefore, idx * 10000));
          }
        }
        
        // Add mermaid diagram
        parts.push(
          <MermaidDiagram key={`mermaid-${idx}`} code={block.code} />
        );
        
        currentIndex = block.end;
      });
      
      // Add remaining text after last mermaid block
      if (currentIndex < text.length) {
        const textAfter = text.substring(currentIndex);
        if (textAfter.trim()) {
          parts.push(...parseTextContent(textAfter, mermaidBlocks.length * 10000));
        }
      }
      
      return parts;
    }
    
    // No mermaid blocks, parse normally
    return parseTextContent(text, 0);
  };
  
  const parseTextContent = (text: string, baseKey: number): ReactNode[] => {
    // Split by lines first to handle headings and lists properly
    const lines = text.split('\n');
    
    return lines.map((line, lineIndex) => {
      const key = baseKey + lineIndex;
      if (line.match(/^### /)) {
        const title = line.replace(/^### /, '').trim();
        return (
          <h3
            key={`h3-${lineIndex}`}
            className="text-lg font-bold text-[#0E1B2E] mt-3 mb-2"
          >
            {title}
          </h3>
        );
      }

      if (line.match(/^## /)) {
        const title = line.replace(/^## /, '').trim();
        return (
          <h2
            key={`h2-${lineIndex}`}
            className="text-xl font-bold text-[#0E1B2E] mt-4 mb-3"
          >
            {title}
          </h2>
        );
      }

      if (line.match(/^# /)) {
        const title = line.replace(/^# /, '').trim();
        return (
          <h1
            key={`h1-${lineIndex}`}
            className="text-2xl font-bold text-[#0E1B2E] mt-5 mb-3"
          >
            {title}
          </h1>
        );
      }

      if (line.match(/^- /) || line.match(/^• /)) {
        const item = line.replace(/^[-•]\s*/, '').trim();
        return (
          <li key={`li-${lineIndex}`} className="text-[#0E1B2E] ml-4 my-1 flex gap-2">
            <span className="flex-shrink-0 text-[#3B82F6] font-bold">▪</span>
            <span className="flex-1">{renderInlinElements(item)}</span>
          </li>
        );
      }

      if (line.trim() === '') {
        return (
          <div key={`spacer-${lineIndex}`} className="h-2" />
        );
      }

      return (
        <p key={`p-${lineIndex}`} className={`text-[#0E1B2E] leading-relaxed ${isFullscreen ? 'text-base' : 'text-sm'}`}>
          {renderInlinElements(line)}
        </p>
      );
    });
  };

  const renderInlinElements = (text: string): ReactNode => {
    const parts: ReactNode[] = [];
    let lastIndex = 0;

    // Handle bold
    const boldRegex = /\*\*(.+?)\*\*/g;
    let boldMatch;
    const boldMatches: Array<{ start: number; end: number; text: string }> = [];

    while ((boldMatch = boldRegex.exec(text)) !== null) {
      boldMatches.push({
        start: boldMatch.index,
        end: boldMatch.index + boldMatch[0].length,
        text: boldMatch[1],
      });
    }

    // Handle inline code
    const codeRegex = /`([^`]+)`/g;
    let codeMatch;
    const codeMatches: Array<{ start: number; end: number; text: string }> = [];

    while ((codeMatch = codeRegex.exec(text)) !== null) {
      codeMatches.push({
        start: codeMatch.index,
        end: codeMatch.index + codeMatch[0].length,
        text: codeMatch[1],
      });
    }

    // Combine and sort all matches
    const allMatches = [...boldMatches, ...codeMatches].sort(
      (a, b) => a.start - b.start
    );

    let currentIndex = 0;

    allMatches.forEach((match, idx) => {
      if (match.start > currentIndex) {
        parts.push(text.substring(currentIndex, match.start));
      }

      if (boldMatches.some((bm) => bm === match)) {
        parts.push(
          <strong
            key={`bold-${idx}`}
            className="font-bold text-[#0E1B2E] bg-gradient-to-r from-[#3B82F6] to-[#1E40AF] bg-clip-text text-transparent"
          >
            {match.text}
          </strong>
        );
      } else if (codeMatches.some((cm) => cm === match)) {
        parts.push(
          <code
            key={`code-${idx}`}
            className="bg-[#0E1B2E]/10 text-[#0E1B2E] px-2 py-0.5 rounded font-mono text-xs border border-[#0E1B2E]/20"
          >
            {match.text}
          </code>
        );
      }

      currentIndex = match.end;
    });

    if (currentIndex < text.length) {
      parts.push(text.substring(currentIndex));
    }

    return parts.length > 0 ? parts : text;
  };

  return (
    <div className={`space-y-1 ${className}`}>
      {parseMarkdown(content)}
    </div>
  );
};

export default MarkdownRenderer;
