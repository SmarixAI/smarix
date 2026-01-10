'use client';

import { Code, GitBranch, Terminal, FileText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vs } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import type { ContentSection } from '../../../../../types/onboarding';

interface ContentRendererProps {
  sections: ContentSection[];
  renderedMermaid: { [key: number]: string };
}

export default function ContentRenderer({ sections, renderedMermaid }: ContentRendererProps) {

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
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
      <div className="p-8 rounded-lg text-center bg-yellow-50 border border-yellow-200">
        <p className="text-lg font-semibold text-yellow-700">
          No content available
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {sections.map((section, idx) => {
        return (
          <div key={idx}>
            {section.type === 'text' && (
              <div className="prose max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ children }) => (
                      <h1 className="text-base font-bold mb-3 mt-4 pb-2 border-b border-[#0E1B2E]/10 text-[#0E1B2E]">
                        {children}
                      </h1>
                    ),
                    h2: ({ children }) => (
                      <h2 className="text-sm font-semibold mb-2 mt-4 pb-1.5 border-b border-[#0E1B2E]/10 text-[#0E1B2E]">
                        {children}
                      </h2>
                    ),
                    h3: ({ children }) => (
                      <h3 className="text-sm font-semibold mb-2 mt-3 flex items-center text-[#0E1B2E]">
                        <span className="w-1 h-4 mr-2 rounded-full bg-[#0E1B2E]/30" />
                        {children}
                      </h3>
                    ),
                    h4: ({ children }) => (
                      <h4 className="text-xs font-semibold mb-1.5 mt-3 text-[#0E1B2E]/90">
                        {children}
                      </h4>
                    ),
                    p: ({ children }) => (
                      <p className="mb-3 leading-relaxed text-sm text-[#0E1B2E]/80">
                        {children}
                      </p>
                    ),
                    ul: ({ children }) => (
                      <ul className="list-none mb-3 space-y-1.5 text-[#0E1B2E]/80">
                        {children}
                      </ul>
                    ),
                    ol: ({ children }) => (
                      <ol className="list-decimal list-inside mb-3 space-y-1.5 ml-2 text-[#0E1B2E]/80">
                        {children}
                      </ol>
                    ),
                    li: ({ children }) => (
                      <li className="flex items-start text-sm">
                        <span className="inline-block w-1.5 h-1.5 rounded-full mt-2 mr-2 flex-shrink-0 bg-[#0E1B2E]/40" />
                        <span className="flex-1">{children}</span>
                      </li>
                    ),
                    strong: ({ children }) => (
                      <strong className="font-semibold text-[#0E1B2E]">
                        {children}
                      </strong>
                    ),
                    em: ({ children }) => (
                      <em className="italic text-[#0E1B2E]/80">
                        {children}
                      </em>
                    ),
                    code: ({ children }) => (
                      <code className="px-1.5 py-0.5 rounded text-xs font-mono bg-[#0E1B2E]/5 text-[#0E1B2E] border border-[#0E1B2E]/10">
                        {children}
                      </code>
                    ),
                    blockquote: ({ children }) => (
                      <blockquote className="border-l-3 pl-3 py-1.5 my-3 italic rounded-r border-[#0E1B2E]/20 bg-[#0E1B2E]/5 text-[#0E1B2E]/80 text-xs">
                        {children}
                      </blockquote>
                    ),
                    a: ({ href, children }) => (
                      <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-medium underline decoration-1 underline-offset-2 transition-colors text-[#0E1B2E] hover:text-[#0E1B2E]/70 text-xs"
                      >
                        {children}
                      </a>
                    ),
                    hr: () => (
                      <hr className="my-4 border-t border-[#0E1B2E]/10" />
                    ),
                    table: ({ children }) => (
                      <div className="overflow-x-auto my-4">
                        <table className="min-w-full divide-y divide-[#0E1B2E]/10">
                          {children}
                        </table>
                      </div>
                    ),
                    thead: ({ children }) => (
                      <thead className="bg-[#0E1B2E]/5">
                        {children}
                      </thead>
                    ),
                    th: ({ children }) => (
                      <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider text-[#0E1B2E]">
                        {children}
                      </th>
                    ),
                    td: ({ children }) => (
                      <td className="px-3 py-2 text-xs text-[#0E1B2E]/80">
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
              <div className="rounded-lg overflow-hidden shadow-sm bg-gray-50 border border-[#0E1B2E]/10">
                <div className="flex items-center justify-between px-4 py-2.5 border-b bg-[#0E1B2E]/5 border-[#0E1B2E]/10">
                  <div className="flex items-center space-x-2">
                    <div className="text-[#0E1B2E]/70">
                      {getLanguageIcon(section.language)}
                    </div>
                    <span className="text-xs font-bold uppercase tracking-wider text-[#0E1B2E]">
                      {getLanguageLabel(section.language)}
                    </span>
                  </div>
                  <button
                    onClick={() => copyToClipboard(section.content)}
                    className="text-xs px-3 py-1.5 rounded-lg font-medium transition-all hover:bg-[#0E1B2E]/10 text-[#0E1B2E]/70 hover:text-[#0E1B2E]"
                  >
                    Copy Code
                  </button>
                </div>
                <div className="overflow-x-auto">
                  <SyntaxHighlighter
                    language={section.language || 'text'}
                    style={vs}
                    customStyle={{
                      margin: 0,
                      padding: '1rem',
                      background: 'transparent',
                      fontSize: '0.8rem',
                      lineHeight: '1.6',
                    }}
                    showLineNumbers
                    wrapLines
                  >
                    {section.content}
                  </SyntaxHighlighter>
                </div>
              </div>
            )}

            {section.type === 'mermaid' && (
              <div className="my-4">
                {section.index !== undefined && renderedMermaid[section.index] ? (
                  <div
                    className="rounded-lg overflow-hidden border border-gray-200 bg-white"
                    dangerouslySetInnerHTML={{ __html: renderedMermaid[section.index] }}
                  />
                ) : (
                  <div className="text-sm italic text-gray-500">
                    <span className="opacity-50">[Diagram unavailable]</span>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
