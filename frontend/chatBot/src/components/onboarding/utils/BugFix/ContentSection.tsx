'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface ContentSectionProps {
  title: string;
  content: string;
}

export default function ContentSection({ title, content }: ContentSectionProps) {
  return (
    <div className="rounded-lg border border-gray-200 overflow-hidden bg-white">
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <h3 className="text-xl font-semibold text-gray-900">{title}</h3>
      </div>
      
      <div className="px-6 py-6 bg-white">
        <div className="prose prose-sm max-w-none">
          <ReactMarkdown
            components={{
              code(props) {
                const { children, className, node, ref, ...rest } = props;
                const match = /language-(\w+)/.exec(className || '');
                return match ? (
                  <SyntaxHighlighter
                    PreTag="div"
                    language={match[1]}
                    style={oneLight}
                    customStyle={{
                      borderRadius: '0.5rem',
                      padding: '1.25rem',
                      fontSize: '0.875rem',
                      border: '1px solid #e5e7eb',
                    }}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className="px-2 py-1 rounded text-sm font-mono border bg-gray-100 text-gray-800 border-gray-200">
                    {children}
                  </code>
                );
              },
              p: ({ children }) => (
                <p className="mb-4 leading-relaxed text-gray-700">
                  {children}
                </p>
              ),
              ul: ({ children }) => (
                <ul className="list-disc list-outside mb-4 space-y-2 ml-6 text-gray-700">
                  {children}
                </ul>
              ),
              ol: ({ children }) => (
                <ol className="list-decimal list-outside mb-4 space-y-2 ml-6 text-gray-700">
                  {children}
                </ol>
              ),
              li: ({ children }) => (
                <li className="mb-1 leading-relaxed text-gray-700">
                  {children}
                </li>
              ),
              h3: ({ children }) => (
                <h3 className="text-lg font-semibold mb-3 mt-4 text-gray-900">
                  {children}
                </h3>
              ),
              blockquote: ({ children }) => (
                <blockquote className="border-l-4 pl-4 py-3 my-4 rounded-r italic border-gray-300 bg-gray-50 text-gray-700">
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
