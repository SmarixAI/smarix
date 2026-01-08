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
    <div className="space-y-8">
      {sections.map((section, idx) => {
        return (
          <div key={idx}>
            {section.type === 'text' && (
              <div className="prose prose-lg max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ children }) => (
                      <h1 className="text-3xl font-extrabold mb-6 mt-8 pb-3 border-b-2 text-gray-900 border-gray-200">
                        {children}
                      </h1>
                    ),
                    h2: ({ children }) => (
                      <h2 className="text-2xl font-bold mb-5 mt-8 pb-2 border-b text-gray-800 border-gray-200">
                        {children}
                      </h2>
                    ),
                    h3: ({ children }) => (
                      <h3 className="text-xl font-bold mb-4 mt-6 flex items-center text-gray-800">
                        <span className="w-1.5 h-6 mr-3 rounded-full bg-gray-600" />
                        {children}
                      </h3>
                    ),
                    h4: ({ children }) => (
                      <h4 className="text-lg font-semibold mb-3 mt-5 text-gray-700">
                        {children}
                      </h4>
                    ),
                    p: ({ children }) => (
                      <p className="mb-5 leading-loose text-base text-gray-700">
                        {children}
                      </p>
                    ),
                    ul: ({ children }) => (
                      <ul className="list-none mb-6 space-y-3 text-gray-700">
                        {children}
                      </ul>
                    ),
                    ol: ({ children }) => (
                      <ol className="list-decimal list-inside mb-6 space-y-3 ml-2 text-gray-700">
                        {children}
                      </ol>
                    ),
                    li: ({ children }) => (
                      <li className="flex items-start">
                        <span className="inline-block w-2 h-2 rounded-full mt-2 mr-3 flex-shrink-0 bg-gray-600" />
                        <span className="flex-1">{children}</span>
                      </li>
                    ),
                    strong: ({ children }) => (
                      <strong className="font-bold text-gray-900">
                        {children}
                      </strong>
                    ),
                    em: ({ children }) => (
                      <em className="italic text-gray-700">
                        {children}
                      </em>
                    ),
                    code: ({ children }) => (
                      <code className="px-2 py-1 rounded-lg text-sm font-mono bg-gray-100 text-gray-800">
                        {children}
                      </code>
                    ),
                    blockquote: ({ children }) => (
                      <blockquote className="border-l-4 pl-6 py-3 my-6 italic rounded-r-lg border-gray-400 bg-gray-50 text-gray-700">
                        {children}
                      </blockquote>
                    ),
                    a: ({ href, children }) => (
                      <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-medium underline decoration-2 underline-offset-2 transition-colors text-gray-900 hover:text-gray-700"
                      >
                        {children}
                      </a>
                    ),
                    hr: () => (
                      <hr className="my-8 border-t-2 border-gray-200" />
                    ),
                    table: ({ children }) => (
                      <div className="overflow-x-auto my-6">
                        <table className="min-w-full divide-y divide-gray-200">
                          {children}
                        </table>
                      </div>
                    ),
                    thead: ({ children }) => (
                      <thead className="bg-gray-50">
                        {children}
                      </thead>
                    ),
                    th: ({ children }) => (
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-700">
                        {children}
                      </th>
                    ),
                    td: ({ children }) => (
                      <td className="px-4 py-3 text-sm text-gray-600">
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
              <div className="rounded-lg overflow-hidden shadow-sm bg-gray-50 border border-gray-200">
                <div className="flex items-center justify-between px-6 py-4 border-b bg-gray-100 border-gray-200">
                  <div className="flex items-center space-x-3">
                    <div className="text-gray-700">
                      {getLanguageIcon(section.language)}
                    </div>
                    <span className="text-sm font-bold uppercase tracking-wider text-gray-700">
                      {getLanguageLabel(section.language)}
                    </span>
                  </div>
                  <button
                    onClick={() => copyToClipboard(section.content)}
                    className="text-xs px-4 py-2 rounded-lg font-medium transition-all hover:bg-gray-200 text-gray-600 hover:text-gray-900"
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
                      padding: '1.5rem',
                      background: 'transparent',
                      fontSize: '0.9rem',
                      lineHeight: '1.7',
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
              <div className="my-6">
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
