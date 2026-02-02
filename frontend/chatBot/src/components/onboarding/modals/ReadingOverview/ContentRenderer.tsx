'use client';

import { Code, GitBranch, Terminal, FileText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import type { ContentSection } from '../../../../../types/onboarding';
import { Inter, JetBrains_Mono, Source_Code_Pro } from 'next/font/google';
import React, { useEffect, useState } from 'react';
import { MermaidDiagram } from '../../utils/MarkdownRenderer';

interface ContentRendererProps {
  sections: ContentSection[];
}

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700'] });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], weight: ['400', '500', '600'] });
const sourceCodePro = Source_Code_Pro({ subsets: ['latin'], weight: ['400', '500', '600'] });


export default function ContentRenderer({ sections }: ContentRendererProps) {

  const [collapsedCodes, setCollapsedCodes] = useState<Record<number, boolean>>({});
  const [copiedCodeIdx, setCopiedCodeIdx] = useState<number | null>(null);
  const codeRefs = React.useRef<Record<number, HTMLDivElement | null>>({});

  const toggleCollapse = (idx: number) => {
    setCollapsedCodes(prev => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };



  useEffect(() => {
    if (copiedCodeIdx === null) return;

    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) {
            setCopiedCodeIdx(null);
          }
        });
      },
      { threshold: 0.1 }
    );

    Object.values(codeRefs.current).forEach(el => {
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, [copiedCodeIdx]);



  const copyToClipboard = (text: string, idx: number) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedCodeIdx(idx);
    });
  };



  const getLanguageIcon = (language?: string) => {
    if (!language) return <Code className="w-5 h-5" />;
    
    const lang = language.toLowerCase();
    if (lang === 'bash' || lang === 'sh' || lang === 'shell') {
      return <Terminal className="w-5 h-5" />;
    }
    if (lang === 'plaintext' || lang === 'text') {
      return <FileText className="w-5 h-5" />;
    }
    return <Code className="w-5 h-5" />;
  };

  const getLanguageLabel = (language?: string) => {
    if (!language || language === 'plaintext') return 'Code';
    
    const labels: { [key: string]: string } = {
      'javascript': 'JavaScript',
      'typescript': 'TypeScript',
      'python': 'Python',
      'java': 'Java',
      'cpp': 'C++',
      'c': 'C',
      'csharp': 'C#',
      'go': 'Go',
      'rust': 'Rust',
      'php': 'PHP',
      'ruby': 'Ruby',
      'swift': 'Swift',
      'kotlin': 'Kotlin',
      'dart': 'Dart',
      'bash': 'Bash',
      'shell': 'Shell',
      'sh': 'Shell',
      'sql': 'SQL',
      'json': 'JSON',
      'xml': 'XML',
      'yaml': 'YAML',
      'yml': 'YAML',
      'html': 'HTML',
      'css': 'CSS',
      'scss': 'SCSS',
      'markdown': 'Markdown',
      'md': 'Markdown',
      'cmake': 'CMake',
    };
    
    return labels[language.toLowerCase()] || language.toUpperCase();
  };

  if (!sections || sections.length === 0) {
    return (
      <div className="p-8 rounded-xl text-center bg-gradient-to-br from-amber-50/80 to-orange-50/50 backdrop-blur-sm border border-amber-200/60">
        <p className={`${inter.className} text-base font-semibold text-amber-700`}>
          No content available
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {sections.map((section, idx) => {
        return (
          <div key={idx}>
            {section.type === 'text' && (
              <div className="prose prose-slate max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ children }) => (
                      <h1 className={`${inter.className} text-2xl font-bold mb-4 mt-6 pb-3 border-b-2 border-blue-200/60 text-[#0E1B2E] tracking-tight`}>
                        {children}
                      </h1>
                    ),
                    h2: ({ children }) => (
                      <h2 className={`${inter.className} text-xl font-semibold mb-3 mt-5 pb-2 border-b border-slate-200/60 text-[#0E1B2E] tracking-tight`}>
                        {children}
                      </h2>
                    ),
                    h3: ({ children }) => (
                      <h3 className={`${inter.className} text-lg font-semibold mb-3 mt-4 flex items-center text-[#0E1B2E] tracking-tight`}>
                        <span className="w-1.5 h-5 mr-3 rounded-full bg-gradient-to-b from-blue-500 to-indigo-500" />
                        {children}
                      </h3>
                    ),
                    h4: ({ children }) => (
                      <h4 className={`${inter.className} text-base font-semibold mb-2 mt-3 text-[#0E1B2E]/90`}>
                        {children}
                      </h4>
                    ),
                    p: ({ children }) => (
                      <p className={`${inter.className} mb-4 leading-relaxed text-[15px] text-slate-700 font-normal`}>
                        {children}
                      </p>
                    ),
                    ul: ({ children }) => (
                      <ul className={`${inter.className} list-none mb-4 space-y-2 text-slate-700`}>
                        {children}
                      </ul>
                    ),
                    ol: ({ children }) => (
                      <ol className={`${inter.className} list-decimal list-inside mb-4 space-y-2 ml-1 text-slate-700`}>
                        {children}
                      </ol>
                    ),
                    li: ({ children }) => (
                      <li className={`${inter.className} flex items-start text-[15px]`}>
                        <span className="inline-flex items-center justify-center w-1.5 h-1.5 rounded-full mt-2.5 mr-3 flex-shrink-0 bg-blue-500" />
                        <span className={`${inter.className} flex-1 leading-relaxed`}>{children}</span>
                      </li>
                    ),
                    strong: ({ children }) => (
                      <strong className={`${inter.className} font-semibold text-[#0E1B2E]`}>
                        {children}
                      </strong>
                    ),
                    em: ({ children }) => (
                      <em className={`${inter.className} italic text-slate-600`}>
                        {children}
                      </em>
                    ),
                    code: ({ children }) => (
                      <code className={`${sourceCodePro.className} px-2 py-1 rounded-md text-[13px] font-medium bg-slate-100 text-[#0E1B2E] border border-slate-200`}>
                        {children}
                      </code>
                    ),
                    blockquote: ({ children }) => (
                      <blockquote className={`${inter.className} border-l-4 pl-4 py-2 my-4 rounded-r-lg border-blue-400 bg-blue-50/50 text-slate-700 text-[15px] italic`}>
                        {children}
                      </blockquote>
                    ),
                    a: ({ href, children }) => (
                      <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`${inter.className} font-medium underline decoration-2 underline-offset-2 transition-colors text-blue-600 hover:text-blue-700`}
                      >
                        {children}
                      </a>
                    ),
                    hr: () => (
                      <hr className="my-6 border-t-2 border-slate-200/60" />
                    ),
                    table: ({ children }) => (
                      <div className="overflow-x-auto my-5 rounded-xl border border-slate-200/60 shadow-sm">
                        <table className="min-w-full divide-y divide-slate-200">
                          {children}
                        </table>
                      </div>
                    ),
                    thead: ({ children }) => (
                      <thead className="bg-gradient-to-r from-slate-50 to-blue-50/30">
                        {children}
                      </thead>
                    ),
                    th: ({ children }) => (
                      <th className={`${inter.className} px-4 py-3 text-left text-sm font-semibold text-[#0E1B2E]`}>
                        {children}
                      </th>
                    ),
                    td: ({ children }) => (
                      <td className={`${inter.className} px-4 py-3 text-sm text-slate-700`}>
                        {children}
                      </td>
                    ),
                  }}
                >
                  {section.content}
                </ReactMarkdown>
              </div>
            )}

            {section.type === 'code' && (
              <div
                ref={el => { if (el) codeRefs.current[idx] = el; }}
                className="rounded-xl overflow-hidden shadow-lg border border-slate-200/60 bg-[#282c34]"
              >
                
                {/* Header */}
                <div className="flex items-center justify-between px-5 py-3 bg-gradient-to-r from-slate-800 to-slate-900 border-b border-slate-700/50">
                  <div className="flex items-center space-x-3">
                    <div className="text-slate-300">
                      {getLanguageIcon(section.language)}
                    </div>
                    <span className={`${inter.className} text-sm font-semibold text-slate-200`}>
                      {getLanguageLabel(section.language)}
                    </span>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => toggleCollapse(idx)}
                      className={`${inter.className} text-xs px-3 py-2 rounded-lg font-medium transition-all
                        bg-slate-700/50 hover:bg-slate-600 text-slate-200
                        border border-slate-600/50`}
                    >
                      {collapsedCodes[idx] ? 'Expand' : 'Collapse'}
                    </button>

                    <button
                      onClick={() => copyToClipboard(section.content, idx)}
                      className={`${inter.className} text-xs px-4 py-2 rounded-lg font-medium transition-all
                        ${
                          copiedCodeIdx === idx
                            ? 'bg-green-600 text-white border-green-500'
                            : 'bg-slate-700/50 hover:bg-slate-600 text-slate-200 hover:text-white border-slate-600/50 hover:border-slate-500'
                        }`}
                    >
                      {copiedCodeIdx === idx ? 'Copied' : 'Copy Code'}
                    </button>
                  </div>
                </div>

                {/* Code Body */}
                {!collapsedCodes[idx] && (
                  <div
                    className="max-h-[420px] overflow-y-auto overflow-x-auto"
                    onScroll={() => copiedCodeIdx === idx && setCopiedCodeIdx(null)}
                  >
                    <SyntaxHighlighter
                      language={section.language || 'text'}
                      style={oneDark}
                      customStyle={{
                        margin: 0,
                        padding: '1.25rem',
                        background: '#282c34',
                        fontSize: '0.875rem',
                        lineHeight: '1.7',
                      }}
                      showLineNumbers
                      wrapLines
                      codeTagProps={{
                        className: sourceCodePro.className,
                      }}
                    >
                      {section.content}
                    </SyntaxHighlighter>
                  </div>
                )}
              </div>
            )}
           {section.type === 'mermaid' && section.content && (
            <MermaidDiagram code={section.content} />
          )}
          </div>
        );
      })}
    </div>
  );
}