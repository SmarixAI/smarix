'use client';

import { Code, GitBranch, Terminal, FileText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus, vs } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import type { ContentSection } from '../../../../../types/onboarding';

interface ContentRendererProps {
  sections: ContentSection[];
  darkMode: boolean;
  renderedMermaid: { [key: number]: string };
}

export default function ContentRenderer({ sections, darkMode, renderedMermaid }: ContentRendererProps) {

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
      <div className={`p-8 rounded-2xl text-center ${
        darkMode ? 'bg-yellow-500/10 border border-yellow-500/30' : 'bg-yellow-50 border border-yellow-200'
      }`}>
        <p className={`text-lg font-semibold ${darkMode ? 'text-yellow-400' : 'text-yellow-700'}`}>
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
              <div className={`prose prose-lg max-w-none ${darkMode ? 'prose-invert' : ''}`}>
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ children }) => (
                      <h1 className={`text-3xl font-extrabold mb-6 mt-8 pb-3 border-b-2 ${
                        darkMode 
                          ? 'text-blue-300 border-blue-500/30' 
                          : 'text-indigo-700 border-indigo-200'
                      }`}>
                        {children}
                      </h1>
                    ),
                    h2: ({ children }) => (
                      <h2 className={`text-2xl font-bold mb-5 mt-8 pb-2 border-b ${
                        darkMode 
                          ? 'text-purple-300 border-purple-500/20' 
                          : 'text-cyan-700 border-cyan-100'
                      }`}>
                        {children}
                      </h2>
                    ),
                    h3: ({ children }) => (
                      <h3 className={`text-xl font-bold mb-4 mt-6 flex items-center ${
                        darkMode ? 'text-pink-300' : 'text-teal-700'
                      }`}>
                        <span className={`w-1.5 h-6 mr-3 rounded-full ${
                          darkMode ? 'bg-pink-400' : 'bg-teal-500'
                        }`} />
                        {children}
                      </h3>
                    ),
                    h4: ({ children }) => (
                      <h4 className={`text-lg font-semibold mb-3 mt-5 ${
                        darkMode ? 'text-blue-200' : 'text-indigo-600'
                      }`}>
                        {children}
                      </h4>
                    ),
                    p: ({ children }) => (
                      <p className={`mb-5 leading-loose text-base ${
                        darkMode ? 'text-gray-300' : 'text-slate-700'
                      }`}>
                        {children}
                      </p>
                    ),
                    ul: ({ children }) => (
                      <ul className={`list-none mb-6 space-y-3 ${
                        darkMode ? 'text-gray-300' : 'text-slate-700'
                      }`}>
                        {children}
                      </ul>
                    ),
                    ol: ({ children }) => (
                      <ol className={`list-decimal list-inside mb-6 space-y-3 ml-2 ${
                        darkMode ? 'text-gray-300' : 'text-slate-700'
                      }`}>
                        {children}
                      </ol>
                    ),
                    li: ({ children }) => (
                      <li className="flex items-start">
                        <span className={`inline-block w-2 h-2 rounded-full mt-2 mr-3 flex-shrink-0 ${
                          darkMode ? 'bg-blue-400' : 'bg-indigo-500'
                        }`} />
                        <span className="flex-1">{children}</span>
                      </li>
                    ),
                    strong: ({ children }) => (
                      <strong className={`font-bold ${
                        darkMode ? 'text-blue-300' : 'text-indigo-700'
                      }`}>
                        {children}
                      </strong>
                    ),
                    em: ({ children }) => (
                      <em className={`italic ${
                        darkMode ? 'text-purple-300' : 'text-cyan-600'
                      }`}>
                        {children}
                      </em>
                    ),
                    code: ({ children }) => (
                      <code className={`px-2 py-1 rounded-lg text-sm font-mono ${
                        darkMode ? 'bg-gray-800 text-pink-300' : 'bg-indigo-50 text-indigo-700'
                      }`}>
                        {children}
                      </code>
                    ),
                    blockquote: ({ children }) => (
                      <blockquote className={`border-l-4 pl-6 py-3 my-6 italic rounded-r-lg ${
                        darkMode 
                          ? 'border-blue-500 bg-blue-500/10 text-gray-300' 
                          : 'border-indigo-500 bg-indigo-50 text-slate-600'
                      }`}>
                        {children}
                      </blockquote>
                    ),
                    a: ({ href, children }) => (
                      <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`font-medium underline decoration-2 underline-offset-2 transition-colors ${
                          darkMode
                            ? 'text-blue-400 hover:text-blue-300'
                            : 'text-indigo-600 hover:text-indigo-800'
                        }`}
                      >
                        {children}
                      </a>
                    ),
                    hr: () => (
                      <hr className={`my-8 border-t-2 ${
                        darkMode ? 'border-gray-700' : 'border-slate-200'
                      }`} />
                    ),
                    table: ({ children }) => (
                      <div className="overflow-x-auto my-6">
                        <table className={`min-w-full divide-y ${
                          darkMode ? 'divide-gray-700' : 'divide-slate-200'
                        }`}>
                          {children}
                        </table>
                      </div>
                    ),
                    thead: ({ children }) => (
                      <thead className={darkMode ? 'bg-gray-800' : 'bg-slate-50'}>
                        {children}
                      </thead>
                    ),
                    th: ({ children }) => (
                      <th className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider ${
                        darkMode ? 'text-gray-300' : 'text-slate-700'
                      }`}>
                        {children}
                      </th>
                    ),
                    td: ({ children }) => (
                      <td className={`px-4 py-3 text-sm ${
                        darkMode ? 'text-gray-300' : 'text-slate-600'
                      }`}>
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
              <div className={`rounded-2xl overflow-hidden shadow-xl ${
                darkMode ? 'bg-gray-900 ring-1 ring-gray-700' : 'bg-slate-50 ring-1 ring-slate-200'
              }`}>
                <div className={`flex items-center justify-between px-6 py-4 border-b ${
                  darkMode ? 'bg-gray-800 border-gray-700' : 'bg-slate-100 border-slate-200'
                }`}>
                  <div className="flex items-center space-x-3">
                    <div className={darkMode ? 'text-blue-400' : 'text-indigo-600'}>
                      {getLanguageIcon(section.language)}
                    </div>
                    <span className={`text-sm font-bold uppercase tracking-wider ${
                      darkMode ? 'text-gray-300' : 'text-slate-700'
                    }`}>
                      {getLanguageLabel(section.language)}
                    </span>
                  </div>
                  <button
                    onClick={() => copyToClipboard(section.content)}
                    className={`text-xs px-4 py-2 rounded-lg font-medium transition-all hover:scale-105 ${
                      darkMode 
                        ? 'hover:bg-gray-700 text-gray-300 hover:text-white' 
                        : 'hover:bg-slate-200 text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Copy Code
                  </button>
                </div>
                <div className="overflow-x-auto">
                  <SyntaxHighlighter
                    language={section.language || 'text'}
                    style={darkMode ? vscDarkPlus : vs}
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
                    className={`rounded-xl overflow-hidden border ${
                      darkMode ? 'border-gray-700 bg-gray-800/50' : 'border-slate-200 bg-white'
                    }`}
                    dangerouslySetInnerHTML={{ __html: renderedMermaid[section.index] }}
                  />
                ) : (
                  <div className={`text-sm italic ${
                    darkMode ? 'text-gray-500' : 'text-slate-500'
                  }`}>
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
