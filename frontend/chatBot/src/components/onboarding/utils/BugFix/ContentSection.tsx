'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight, vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface ContentSectionProps {
  title: string;
  content: string;
  color?: 'blue' | 'purple' | 'green' | 'orange' | 'pink' | 'indigo';
  darkMode: boolean;
}

export default function ContentSection({ title, content, color = 'blue', darkMode }: ContentSectionProps) {
  const colorClasses = {
    blue: {
      border: darkMode ? 'border-blue-700' : 'border-blue-200',
      bg: darkMode ? 'bg-gradient-to-br from-blue-900/30 to-cyan-900/30' : 'bg-gradient-to-br from-blue-50 to-cyan-50',
      title: darkMode ? 'text-blue-300' : 'text-blue-700',
      accent: darkMode ? 'border-blue-700' : 'border-blue-300',
    },
    purple: {
      border: darkMode ? 'border-purple-700' : 'border-purple-200',
      bg: darkMode ? 'bg-gradient-to-br from-purple-900/30 to-pink-900/30' : 'bg-gradient-to-br from-purple-50 to-pink-50',
      title: darkMode ? 'text-purple-300' : 'text-purple-700',
      accent: darkMode ? 'border-purple-700' : 'border-purple-300',
    },
    green: {
      border: darkMode ? 'border-green-700' : 'border-green-200',
      bg: darkMode ? 'bg-gradient-to-br from-green-900/30 to-emerald-900/30' : 'bg-gradient-to-br from-green-50 to-emerald-50',
      title: darkMode ? 'text-green-300' : 'text-green-700',
      accent: darkMode ? 'border-green-700' : 'border-green-300',
    },
    orange: {
      border: darkMode ? 'border-orange-700' : 'border-orange-200',
      bg: darkMode ? 'bg-gradient-to-br from-orange-900/30 to-amber-900/30' : 'bg-gradient-to-br from-orange-50 to-amber-50',
      title: darkMode ? 'text-orange-300' : 'text-orange-700',
      accent: darkMode ? 'border-orange-700' : 'border-orange-300',
    },
    pink: {
      border: darkMode ? 'border-pink-700' : 'border-pink-200',
      bg: darkMode ? 'bg-gradient-to-br from-pink-900/30 to-rose-900/30' : 'bg-gradient-to-br from-pink-50 to-rose-50',
      title: darkMode ? 'text-pink-300' : 'text-pink-700',
      accent: darkMode ? 'border-pink-700' : 'border-pink-300',
    },
    indigo: {
      border: darkMode ? 'border-indigo-700' : 'border-indigo-200',
      bg: darkMode ? 'bg-gradient-to-br from-indigo-900/30 to-purple-900/30' : 'bg-gradient-to-br from-indigo-50 to-purple-50',
      title: darkMode ? 'text-indigo-300' : 'text-indigo-700',
      accent: darkMode ? 'border-indigo-700' : 'border-indigo-300',
    },
  };

  const colors = colorClasses[color];

  return (
    <div className={`rounded-xl border-2 ${colors.border} ${colors.bg} overflow-hidden shadow-lg`}>
      <div className={`px-6 py-4 border-b-2 ${colors.accent} ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
        <h3 className={`text-xl font-bold ${colors.title}`}>{title}</h3>
      </div>
      
      <div className={`px-6 py-6 ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
        <div className={`prose prose-sm max-w-none ${darkMode ? 'prose-invert' : ''}`}>
          <ReactMarkdown
            components={{
              code(props) {
                const { children, className, node, ref, ...rest } = props;
                const match = /language-(\w+)/.exec(className || '');
                return match ? (
                  <SyntaxHighlighter
                    PreTag="div"
                    language={match[1]}
                    style={darkMode ? vscDarkPlus : oneLight}
                    customStyle={{
                      borderRadius: '0.75rem',
                      padding: '1.25rem',
                      fontSize: '0.875rem',
                      border: darkMode ? '1px solid #374151' : '1px solid #e5e7eb',
                      boxShadow: '0 2px 4px rgba(0, 0, 0, 0.05)',
                    }}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className={`px-2 py-1 rounded text-sm font-mono border ${
                    darkMode
                      ? 'bg-gray-900 text-gray-300 border-gray-700'
                      : 'bg-slate-100 text-slate-800 border-slate-200'
                  }`}>
                    {children}
                  </code>
                );
              },
              p: ({ children }) => (
                <p className={`mb-4 leading-relaxed ${darkMode ? 'text-gray-300' : 'text-slate-700'}`}>
                  {children}
                </p>
              ),
              ul: ({ children }) => (
                <ul className={`list-disc list-outside mb-4 space-y-2 ml-6 ${darkMode ? 'text-gray-300' : 'text-slate-700'}`}>
                  {children}
                </ul>
              ),
              ol: ({ children }) => (
                <ol className={`list-decimal list-outside mb-4 space-y-2 ml-6 ${darkMode ? 'text-gray-300' : 'text-slate-700'}`}>
                  {children}
                </ol>
              ),
              li: ({ children }) => (
                <li className={`mb-1 leading-relaxed ${darkMode ? 'text-gray-300' : 'text-slate-700'}`}>
                  {children}
                </li>
              ),
              h3: ({ children }) => (
                <h3 className={`text-lg font-bold mb-3 mt-4 ${darkMode ? 'text-white' : 'text-slate-900'}`}>
                  {children}
                </h3>
              ),
              blockquote: ({ children }) => (
                <blockquote className={`border-l-4 pl-4 py-3 my-4 rounded-r italic ${
                  darkMode
                    ? 'border-blue-500 bg-blue-900/30 text-gray-300'
                    : 'border-blue-400 bg-blue-50 text-slate-700'
                }`}>
                  {children}
                </blockquote>
              ),
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
