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
  const MIN_ZOOM = 0.3;
  const MAX_ZOOM = 1.6;
  const ZOOM_STEP = 0.05;
  const [collapsed, setCollapsed] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const isDragging = useRef(false);
  const startX = useRef(0);
  const startY = useRef(0);
  const scrollLeft = useRef(0);
  const scrollTop = useRef(0);




  useEffect(() => {
    if (!code || !containerRef.current) return;

    // Reset zoom on re-render
    setZoom(1);

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
    setZoom((prev) =>
    Math.min(MAX_ZOOM, prev + ZOOM_STEP)
  );

  };

  const handleZoomOut = () => {
    setZoom((prev) =>
    Math.max(MIN_ZOOM, prev - ZOOM_STEP)
  );

  };

  const handleReset = () => {
    setZoom(1);
  };

  const handleWheel = (e: React.WheelEvent) => {
    // Only zoom when Ctrl (Windows/Linux) or Cmd (Mac) is pressed
    if (!(e.ctrlKey || e.metaKey)) return;

    e.preventDefault();

    const delta = e.deltaY > 0 ? -ZOOM_STEP : ZOOM_STEP;

    setZoom((prev) =>
      Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, prev + delta))
    );
  };

  const onMouseDown = (e: React.MouseEvent) => {
    const el = scrollRef.current;
    if (!el) return;

    isDragging.current = true;
    el.classList.add('cursor-grabbing');

    startX.current = e.pageX - el.offsetLeft;
    startY.current = e.pageY - el.offsetTop;
    scrollLeft.current = el.scrollLeft;
    scrollTop.current = el.scrollTop;
  };

  const onMouseLeaveOrUp = () => {
    const el = scrollRef.current;
    if (!el) return;

    isDragging.current = false;
    el.classList.remove('cursor-grabbing');
  };

  const onMouseMove = (e: React.MouseEvent) => {
    if (!isDragging.current) return;

    const el = scrollRef.current;
    if (!el) return;

    e.preventDefault();

    const x = e.pageX - el.offsetLeft;
    const y = e.pageY - el.offsetTop;

    el.scrollLeft = scrollLeft.current - (x - startX.current);
    el.scrollTop = scrollTop.current - (y - startY.current);
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
    <div className="my-4 rounded-xl border border-[#0E1B2E]/10 bg-white/60 backdrop-blur-sm shadow-sm overflow-hidden">

      {/* Loading overlay */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/80 backdrop-blur-sm z-10">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0E1B2E]" />
        </div>
      )}

      {/* Header */}
      {!isLoading && (
        <div className="flex items-center justify-between px-4 py-2 text-xs bg-[#0E1B2E]/5 border-b border-[#0E1B2E]/10">
          
          {/* Left: Title */}
          <span className="font-mono text-[#0E1B2E]/80 uppercase">
            Diagram
          </span>

          {/* Right: Controls */}
          <div className="flex items-center gap-3">
            
            {/* Collapse / Expand */}
            <button
              onClick={() => setCollapsed((prev) => !prev)}
              className="text-[#0E1B2E]/60 hover:text-[#0E1B2E] transition"
            >
              {collapsed ? 'Expand' : 'Collapse'}
            </button>

            <span className="w-px h-4 bg-[#0E1B2E]/20" />

            {/* Zoom out */}
            <button
              onClick={handleZoomOut}
              className="hover:text-[#0E1B2E]"
              title="Zoom Out"
            >
              <ZoomOut className="w-4 h-4" />
            </button>

            {/* Zoom percentage */}
            <span className="text-xs font-mono text-[#0E1B2E] min-w-[40px] text-center">
              {(zoom * 100).toFixed(0)}%
            </span>

            {/* Zoom in */}
            <button
              onClick={handleZoomIn}
              className="hover:text-[#0E1B2E]"
              title="Zoom In"
            >
              <ZoomIn className="w-4 h-4" />
            </button>

            {/* Reset */}
            <button
              onClick={handleReset}
              className="hover:text-[#0E1B2E]"
              title="Reset Zoom"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Diagram Body */}
      <div
        className={`
          transition-[max-height] duration-300 ease-in-out
          ${collapsed ? 'max-h-0 overflow-hidden' : 'max-h-[520px] overflow-auto'}
        `}
        style={{ minHeight: collapsed ? '0px' : '240px' }}
      >
        <div
          ref={scrollRef}
          className="p-4 overflow-auto cursor-grab"
          onMouseDown={onMouseDown}
          onMouseUp={onMouseLeaveOrUp}
          onMouseLeave={onMouseLeaveOrUp}
          onMouseMove={onMouseMove}
          onWheel={handleWheel}
        >

          <div ref={containerRef} className="mermaid-container" />
        </div>
      </div>
    </div>
);

};

const CodeBlock = ({
  code,
  language,
}: {
  code: string;
  language: string;
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const [copied, setCopied] = useState(false);
  const blockRef = useRef<HTMLDivElement>(null);

  // Observe visibility
  useEffect(() => {
    const el = blockRef.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        // When block leaves viewport → reset
        if (!entry.isIntersecting) {
          setCopied(false);
        }
      },
      {
        threshold: 0.1, // even slightly visible counts
      }
    );

    observer.observe(el);

    return () => observer.disconnect();
  }, []);

  const handleCopy = () => {
    if (navigator?.clipboard) {
      navigator.clipboard.writeText(code);
      setCopied(true);
    }
  };

  return (
    <div
      ref={blockRef}
      className="my-4 rounded-xl border border-[#0E1B2E]/15 bg-[#0E1B2E] overflow-hidden shadow-sm"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 text-xs bg-black/30">
        <span className="font-mono text-white/80 uppercase">
          {language || 'code'}
        </span>

        <div className="flex items-center gap-3">
          {/* Collapse / Expand */}
          <button
            onClick={() => setCollapsed((prev) => !prev)}
            className="text-white/60 hover:text-white transition"
          >
            {collapsed ? 'Expand' : 'Collapse'}
          </button>

          {/* Copy */}
          <button
            onClick={handleCopy}
            className={`transition font-medium ${
              copied
                ? 'text-green-400'
                : 'text-white/60 hover:text-white'
            }`}
          >
            {copied ? 'Copied ✓' : 'Copy'}
          </button>
        </div>
      </div>

      {/* Code */}
      <div
        className={`
          transition-[max-height] duration-300 ease-in-out
          ${collapsed ? 'max-h-0 overflow-hidden' : 'max-h-[600px]'}
        `}
      >
        {/* Vertical scroll container */}
        <div className="max-h-[600px] overflow-y-auto">
          <pre className="p-4 overflow-x-auto text-sm text-white font-mono leading-relaxed">
            <code>{code}</code>
          </pre>
        </div>
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
    let match;
    let blockIndex = 0;

    const fenceRegex = /```([\w-]+)?\n([\s\S]*?)```/g;

    while ((match = fenceRegex.exec(text)) !== null) {
      const [full, lang = 'text', code] = match;

      // Text before block
      if (match.index > lastIndex) {
        const before = text.slice(lastIndex, match.index);
        if (before.trim()) {
          parts.push(...parseTextContent(before, blockIndex * 1000));
        }
      }

      // Block rendering
      if (lang === 'mermaid') {
        parts.push(
          <MermaidDiagram key={`mermaid-${blockIndex}`} code={code.trim()} />
        );
      } else {
        parts.push(
          <CodeBlock
            key={`code-${blockIndex}`}
            language={lang}
            code={code.trim()}
          />
        );
      }

      lastIndex = match.index + full.length;
      blockIndex++;
    }

    // Remaining text
    if (lastIndex < text.length) {
      const remaining = text.slice(lastIndex);
      if (remaining.trim()) {
        parts.push(...parseTextContent(remaining, blockIndex * 1000));
      }
    }

    return parts;
  };

  
  const parseTextContent = (text: string, baseKey: number): ReactNode[] => {
    const lines = text.split('\n');
    let inDiffBlock = false;

    return lines.map((line, lineIndex) => {

      // --- DIFF BLOCK DETECTION (ADD THIS FIRST) ---
      if (
        line.trim() === 'diff' ||
        line.startsWith('@@ ') ||
        line.startsWith('+++') ||
        line.startsWith('---')
      ) {
        inDiffBlock = true;
      }

      if (inDiffBlock) {
        // Exit diff block on empty line
        if (line.trim() === '') {
          inDiffBlock = false;
          return <div key={`diff-end-${baseKey}-${lineIndex}`} className="h-2" />;
        }

        return (
          <pre
            key={`diff-${baseKey}-${lineIndex}`}
            className="bg-[#0E1B2E] text-white text-xs font-mono p-3 rounded-md overflow-x-auto my-1"
          >
            {line}
          </pre>
        );
      }

      if (line.match(/^#### /)) {
        return (
          <h4
            key={`h4-${baseKey}-${lineIndex}`}
            className="text-base font-semibold text-[#0E1B2E] mt-3 mb-2"
          >
            {line.replace(/^#### /, '').trim()}
          </h4>
        );
      }

      if (line.match(/^### /)) {
        return (
          <h3
            key={`h3-${baseKey}-${lineIndex}`}
            className="text-lg font-semibold text-[#0E1B2E] mt-3 mb-2"
          >
            {line.replace(/^### /, '').trim()}
          </h3>
        );
      }

      if (line.match(/^## /)) {
        return (
          <h2
            key={`h2-${baseKey}-${lineIndex}`}
            className="text-xl font-bold text-[#0E1B2E] mt-4 mb-3"
          >
            {line.replace(/^## /, '').trim()}
          </h2>
        );
      }

      if (line.match(/^# /)) {
        return (
          <h1
            key={`h1-${baseKey}-${lineIndex}`}
            className="text-2xl font-bold text-[#0E1B2E] mt-5 mb-3"
          >
            {line.replace(/^# /, '').trim()}
          </h1>
        );
      }

      if (
        (line.match(/^- /) || line.match(/^• /)) &&
        !line.startsWith('---') &&
        !line.startsWith('@@')
      ) {
        return (
          <li
            key={`li-${baseKey}-${lineIndex}`}
            className="text-[#0E1B2E] ml-4 my-1 flex gap-2"
          >
            <span className="flex-shrink-0 text-[#3B82F6] font-bold">▪</span>
            <span className="flex-1">
              {renderInlinElements(line.replace(/^[-•]\s*/, '').trim())}
            </span>
          </li>
        );
      }

      if (line.trim() === '') {
        return <div key={`spacer-${baseKey}-${lineIndex}`} className="h-2" />;
      }

      return (
        <p
          key={`p-${baseKey}-${lineIndex}`}
          className={`text-[#0E1B2E] leading-relaxed ${
            isFullscreen ? 'text-base' : 'text-sm'
          }`}
        >
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

    // Handle links [text](url)
    const linkRegex = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g;
    let linkMatch;
    const linkMatches: Array<{ start: number; end: number; text: string; url: string }> = [];

    while ((linkMatch = linkRegex.exec(text)) !== null) {
      linkMatches.push({
        start: linkMatch.index,
        end: linkMatch.index + linkMatch[0].length,
        text: linkMatch[1],
        url: linkMatch[2],
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
    const allMatches = [
      ...linkMatches,
      ...codeMatches,
      ...boldMatches,
    ].sort((a, b) => a.start - b.start);


    let currentIndex = 0;

    allMatches.forEach((match, idx) => {
      if (match.start > currentIndex) {
        parts.push(text.substring(currentIndex, match.start));
      }

      // 1️⃣ Links (highest priority)
      if (linkMatches.some((lm) => lm === match)) {
        const isGitHub = match.url.includes('github.com');

        parts.push(
          <a
            key={`link-${idx}`}
            href={match.url}
            target="_blank"
            rel="noopener noreferrer"
            className={`
              inline-flex items-center gap-1 px-2 py-1 rounded-md text-sm font-medium
              ${isGitHub
                ? 'bg-[#24292F]/10 text-[#24292F] hover:bg-[#24292F]/20'
                : 'bg-[#0E1B2E]/10 text-[#0E1B2E] hover:bg-[#0E1B2E]/20'}
              transition-colors
            `}
          >
            🔗 {match.text}
          </a>
        );

      // 2️⃣ Inline code
      } else if (codeMatches.some((cm) => cm === match)) {
        parts.push(
          <code
            key={`code-${idx}`}
            className="bg-[#0E1B2E]/10 text-[#0E1B2E] px-2 py-0.5 rounded font-mono text-xs border border-[#0E1B2E]/20"
          >
            {match.text}
          </code>
        );

      // 3️⃣ Bold (lowest priority)
      } else if (boldMatches.some((bm) => bm === match)) {
        parts.push(
          <strong
            key={`bold-${idx}`}
            className="font-bold text-[#0E1B2E] bg-gradient-to-r from-[#3B82F6] to-[#1E40AF] bg-clip-text text-transparent"
          >
            {match.text}
          </strong>
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
