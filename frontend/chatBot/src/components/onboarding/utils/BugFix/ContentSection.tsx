'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Inter, JetBrains_Mono } from 'next/font/google';

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700'] });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], weight: ['400', '500'] });

interface ContentSectionProps {
  title: string;
  content: string;
}

export default function ContentSection({ title, content }: ContentSectionProps) {
  return (
    <div className="rounded-2xl border-2 border-[#0E1B2E]/5 overflow-hidden bg-white shadow-sm hover:shadow-md transition-shadow duration-300">
      <div className="px-6 py-4 border-b border-[#0E1B2E]/5 bg-slate-50/50">
        <h3 className={`${inter.className} text-[15px] font-bold text-[#0E1B2E] uppercase tracking-wide flex items-center gap-2`}>
          <div className="w-1 h-4 bg-[#0E1B2E] rounded-full" />
          {title}
        </h3>
      </div>
      
      <div className="px-6 py-6 bg-white">
        <div className="prose prose-sm max-w-none prose-slate">
          <ReactMarkdown
            components={{
              code(props) {
                const { children, className, node, ref, ...rest } = props;
                const match = /language-(\w+)/.exec(className || '');
                return match ? (
                  <div className="my-4 rounded-xl overflow-hidden bg-[#282c34] border border-slate-800 shadow-inner">
                    <SyntaxHighlighter
                      PreTag="div"
                      language={match[1]}
                      style={oneDark}
                      customStyle={{
                        margin: 0,
                        padding: '1.25rem',
                        fontSize: '0.85rem',
                        backgroundColor: 'transparent',
                        fontFamily: jetbrainsMono.style.fontFamily,
                      }}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  </div>
                ) : (
                  <code className={`${jetbrainsMono.className} px-1.5 py-0.5 rounded text-[13px] bg-[#0E1B2E]/5 text-[#0E1B2E] border border-[#0E1B2E]/10`}>
                    {children}
                  </code>
                );
              },
              p: ({ children }) => (
                <p className={`${inter.className} mb-4 leading-relaxed text-[15px] text-[#0E1B2E]/80`}>
                  {children}
                </p>
              ),
              ul: ({ children }) => (
                <ul className="list-disc list-outside mb-4 space-y-2 ml-4 text-sm text-[#0E1B2E]/80 marker:text-[#0E1B2E]/40">
                  {children}
                </ul>
              ),
              ol: ({ children }) => (
                <ol className="list-decimal list-outside mb-4 space-y-2 ml-4 text-sm text-[#0E1B2E]/80 marker:text-[#0E1B2E]/60 marker:font-semibold">
                  {children}
                </ol>
              ),
              li: ({ children }) => (
                <li className={`${inter.className} leading-relaxed pl-1`}>
                  {children}
                </li>
              ),
              h3: ({ children }) => (
                <h3 className={`${inter.className} text-base font-bold mb-3 mt-6 text-[#0E1B2E]`}>
                  {children}
                </h3>
              ),
              blockquote: ({ children }) => (
                <blockquote className="border-l-4 pl-4 py-3 my-5 rounded-r bg-blue-50/50 border-blue-500/30 text-[15px] text-[#0E1B2E]/70 italic">
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