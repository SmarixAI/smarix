"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, Terminal, BookOpen, Code2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Inter, JetBrains_Mono } from "next/font/google";

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});
const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
});

interface Step {
  title: string;
  content: string;
}

interface StepByStepSectionProps {
  steps: Step[];
}

export default function StepByStepSection({ steps }: StepByStepSectionProps) {
  const [currentStep, setCurrentStep] = useState(1);

  const totalSteps = steps.length;
  const progress = (currentStep / totalSteps) * 100;
  const currentStepData = steps[currentStep - 1];

  return (
    <div className={`rounded-2xl border border-white/10 h-[95vh] bg-[#1E1F22] shadow-2xl flex flex-col overflow-hidden ${inter.className}`}>
      
      {/* HEADER: Editor Tab Style */}
      <div className="px-6 py-4 border-b border-white/5 bg-[#1B1B1D] flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[#2B2D31] border border-white/10 shadow-inner">
              <span className={`${jetbrainsMono.className} text-emerald-400 font-bold text-lg`}>
                {currentStep.toString().padStart(2, '0')}
              </span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <Code2 className="w-3.5 h-3.5 text-zinc-500" />
                <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-[0.2em]">
                  Implementation Phase
                </p>
              </div>
              <p className="text-sm font-semibold text-zinc-200">
                Step {currentStep} <span className="text-zinc-600 mx-1">/</span> {totalSteps}
              </p>
            </div>
          </div>
          
          <div className="flex flex-col items-end gap-1">
            <span className={`${jetbrainsMono.className} text-[10px] font-bold text-emerald-500/80 bg-emerald-500/5 px-2 py-1 rounded border border-emerald-500/10`}>
              {Math.round(progress)}% COMPILED
            </span>
          </div>
        </div>

        {/* Custom Progress Bar (Segmented) */}
        <div className="flex gap-1 h-1">
          {Array.from({ length: totalSteps }).map((_, idx) => (
            <div
              key={idx}
              className={`flex-1 rounded-full transition-all duration-500 ${
                idx < currentStep
                  ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]"
                  : "bg-zinc-800"
              }`}
            />
          ))}
        </div>
      </div>

      {/* CONTENT: Editor Area */}
      <div className="flex-1 overflow-y-auto px-8 py-8 bg-[#1E1F22] custom-scrollbar">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-xl font-bold mb-8 flex items-center gap-3 text-zinc-100">
            <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
              <Terminal className="w-4 h-4" />
            </span>
            <span>{currentStepData?.title}</span>
          </h2>

          <div className="prose prose-invert prose-sm max-w-none">
            <ReactMarkdown
              components={{
                code(props) {
                  const { children, className } = props;
                  const match = /language-(\w+)/.exec(className || "");
                  return match ? (
                    <div className="my-6 rounded-xl overflow-hidden border border-white/10 bg-[#0D0D0F]">
                      <div className="px-4 py-2 bg-[#161618] border-b border-white/5 flex items-center justify-between">
                        <div className="flex gap-1.5">
                          <div className="w-2.5 h-2.5 rounded-full bg-[#FF5F56]" />
                          <div className="w-2.5 h-2.5 rounded-full bg-[#FFBD2E]" />
                          <div className="w-2.5 h-2.5 rounded-full bg-[#27C93F]" />
                        </div>
                        <span className={`${jetbrainsMono.className} text-[10px] text-zinc-500 uppercase tracking-widest font-bold`}>
                          {match[1]}
                        </span>
                      </div>
                      <SyntaxHighlighter
                        PreTag="div"
                        language={match[1]}
                        style={oneDark}
                        customStyle={{
                          margin: 0,
                          padding: "1.5rem",
                          fontSize: "0.85rem",
                          backgroundColor: "#0D0D0F",
                          fontFamily: jetbrainsMono.style.fontFamily,
                          lineHeight: "1.6",
                        }}
                      >
                        {String(children).replace(/\n$/, "")}
                      </SyntaxHighlighter>
                    </div>
                  ) : (
                    <code className={`${jetbrainsMono.className} px-1.5 py-0.5 rounded text-[13px] bg-zinc-800 text-emerald-400 border border-white/5`}>
                      {children}
                    </code>
                  );
                },
                p: ({ children }) => (
                  <p className="mb-6 leading-relaxed text-[15px] text-zinc-400 font-medium">
                    {children}
                  </p>
                ),
                ul: ({ children }) => (
                  <ul className="list-none mb-6 space-y-3 ml-2">
                    {children}
                  </ul>
                ),
                li: ({ children }) => (
                  <li className="flex items-start gap-3 text-[15px] text-zinc-400">
                    <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-emerald-500/40 shrink-0" />
                    <span>{children}</span>
                  </li>
                ),
                h3: ({ children }) => (
                  <h3 className="text-zinc-100 font-bold text-lg mt-8 mb-4 border-l-2 border-emerald-500 pl-4">
                    {children}
                  </h3>
                ),
              }}
            >
              {currentStepData?.content}
            </ReactMarkdown>
          </div>
        </div>
      </div>

      {/* FOOTER: Navigation Bar */}
      <div className="mt-auto px-8 py-5 border-t border-white/5 bg-[#1B1B1D] flex items-center justify-between">
        <button
          onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
          disabled={currentStep === 1}
          className={`px-5 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 transition-all duration-200 border ${
            currentStep === 1
              ? "border-white/5 text-zinc-700 cursor-not-allowed"
              : "border-white/10 bg-[#2B2D31] text-zinc-300 hover:bg-[#32353B] hover:text-white active:scale-95"
          }`}
        >
          <ChevronLeft className="w-4 h-4" />
          PREVIOUS
        </button>

        <div className="flex items-center gap-2">
          {Array.from({ length: totalSteps }).map((_, idx) => (
            <div
              key={idx}
              className={`h-1 rounded-full transition-all duration-500 ${
                idx + 1 === currentStep
                  ? "bg-emerald-500 w-8"
                  : idx < currentStep
                  ? "bg-emerald-500/20 w-2"
                  : "bg-zinc-800 w-2"
              }`}
            />
          ))}
        </div>

        <button
          onClick={() => setCurrentStep(Math.min(totalSteps, currentStep + 1))}
          disabled={currentStep === totalSteps}
          className={`px-6 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 transition-all duration-200 ${
            currentStep === totalSteps
              ? "border border-white/5 text-zinc-700 cursor-not-allowed"
              : "bg-emerald-600 text-white hover:bg-emerald-500 shadow-lg shadow-emerald-500/10 active:scale-95"
          }`}
        >
          {currentStep === totalSteps ? "COMPLETE" : "NEXT STEP"}
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #1E1F22;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #2B2D31;
          border-radius: 10px;
          border: 2px solid #1E1F22;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #32353B;
        }
      `}</style>
    </div>
  );
}