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
    <div className="rounded-xl border border-white/25 overflow-hidden bg-white/35 backdrop-blur-xl shadow-md shadow-black/5">
      <div className="px-6 py-3 border-b border-[#0E1B2E]/10 bg-white/40 backdrop-blur-sm">
        <h3 className="text-base font-semibold text-[#0E1B2E]">{title}</h3>
      </div>
      
      <div className="px-6 py-4 bg-white">
        <div className="prose max-w-none">
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
                      padding: '1rem',
                      fontSize: '0.8rem',
                      border: '1px solid #e5e7eb',
                    }}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className="px-1.5 py-0.5 rounded text-xs font-mono border bg-[#0E1B2E]/5 text-[#0E1B2E] border-[#0E1B2E]/10">
                    {children}
                  </code>
                );
              },
              p: ({ children }) => (
                <p className="mb-3 leading-relaxed text-sm text-[#0E1B2E]/80">
                  {children}
                </p>
              ),
              ul: ({ children }) => (
                <ul className="list-disc list-outside mb-3 space-y-1.5 ml-5 text-sm text-[#0E1B2E]/80">
                  {children}
                </ul>
              ),
              ol: ({ children }) => (
                <ol className="list-decimal list-outside mb-3 space-y-1.5 ml-5 text-sm text-[#0E1B2E]/80">
                  {children}
                </ol>
              ),
              li: ({ children }) => (
                <li className="mb-1 leading-relaxed text-sm text-[#0E1B2E]/80">
                  {children}
                </li>
              ),
              h3: ({ children }) => (
                <h3 className="text-sm font-semibold mb-2 mt-3 text-[#0E1B2E]">
                  {children}
                </h3>
              ),
              blockquote: ({ children }) => (
                <blockquote className="border-l-3 pl-3 py-2 my-3 rounded-r italic border-[#0E1B2E]/20 bg-[#0E1B2E]/5 text-sm text-[#0E1B2E]/80">
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
