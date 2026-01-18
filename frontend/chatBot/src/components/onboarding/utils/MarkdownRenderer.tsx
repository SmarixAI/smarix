'use client';

import React, { ReactNode } from 'react';

interface MarkdownRendererProps {
  content: string;
  className?: string;
  isFullscreen?: boolean;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  className = '',
  isFullscreen = false,
}) => {
  const parseMarkdown = (text: string): ReactNode[] => {
    const parts: ReactNode[] = [];
    let lastIndex = 0;

    // Regular expressions for different markdown elements
    const patterns = [
      { regex: /^### (.+)$/gm, type: 'h3' },
      { regex: /^## (.+)$/gm, type: 'h2' },
      { regex: /^# (.+)$/gm, type: 'h1' },
      { regex: /\*\*(.+?)\*\*/g, type: 'bold' },
      { regex: /^- (.+)$/gm, type: 'li' },
      { regex: /^• (.+)$/gm, type: 'li' },
      { regex: /`([^`]+)`/g, type: 'code' },
    ];

    // Split by lines first to handle headings and lists properly
    const lines = text.split('\n');
    
    return lines.map((line, lineIndex) => {
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
