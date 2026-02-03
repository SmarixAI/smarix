"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, Terminal } from "lucide-react";
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
    <div className="rounded-2xl border-2 border-[#0E1B2E]/5 h-[95vh] bg-white shadow-lg shadow-[#0E1B2E]/5 flex flex-col">
      {/* Progress Header */}
      <div className="px-6 py-5 border-b border-[#0E1B2E]/5 bg-gradient-to-r from-slate-50/50 to-white">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-[#0E1B2E] to-blue-900 shadow-md">
              <span
                className={`${jetbrainsMono.className} text-white font-bold text-lg`}
              >
                {currentStep}
              </span>
            </div>
            <div>
              <p
                className={`${inter.className} text-sm font-bold text-[#0E1B2E]`}
              >
                Step {currentStep} of {totalSteps}
              </p>
              <p
                className={`${inter.className} text-xs text-[#0E1B2E]/50 font-medium`}
              >
                Implementation Guide
              </p>
            </div>
          </div>
          <span
            className={`${jetbrainsMono.className} text-xs font-bold text-[#0E1B2E] bg-[#0E1B2E]/5 px-3 py-1.5 rounded-lg border border-[#0E1B2E]/5`}
          >
            {Math.round(progress)}% Complete
          </span>
        </div>

        {/* Progress Bar */}
        <div className="flex gap-1.5 h-1.5">
          {Array.from({ length: totalSteps }).map((_, idx) => (
            <div
              key={idx}
              className={`flex-1 rounded-full transition-all duration-500 ${
                idx < currentStep
                  ? "bg-gradient-to-r from-[#0E1B2E] to-blue-600"
                  : "bg-slate-200"
              }`}
            />
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="flex-1 overflow-y-auto px-6 py-6 bg-white min-h-[300px]">
        <h2
          className={`${inter.className} text-lg font-bold mb-4 flex items-center gap-3 text-[#0E1B2E]`}
        >
          <span className="flex items-center justify-center w-6 h-6 rounded bg-[#0E1B2E]/5 text-[#0E1B2E]/40 text-xs">
            <Terminal className="w-3.5 h-3.5" />
          </span>
          <span>{currentStepData?.title}</span>
        </h2>

        <div className="prose prose-sm max-w-none prose-neutral">
          <ReactMarkdown
            components={{
              code(props) {
                const { children, className, node, ref, ...rest } = props;
                const match = /language-(\w+)/.exec(className || "");
                return match ? (
                  <div className="my-4 rounded-xl overflow-hidden shadow-lg shadow-black/20 border border-slate-700/50">
                    <div className="px-4 py-2 bg-[#1e222a] border-b border-slate-700/50 flex items-center gap-2">
                      <div className="flex gap-1.5">
                        <div className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
                        <div className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
                        <div className="w-2.5 h-2.5 rounded-full bg-green-500/80" />
                      </div>
                      <span
                        className={`${jetbrainsMono.className} text-[10px] text-slate-400 ml-2 uppercase tracking-wider`}
                      >
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
                        backgroundColor: "#282c34",
                        fontFamily: jetbrainsMono.style.fontFamily,
                      }}
                    >
                      {String(children).replace(/\n$/, "")}
                    </SyntaxHighlighter>
                  </div>
                ) : (
                  <code
                    className={`${jetbrainsMono.className} px-1.5 py-0.5 rounded text-[13px] bg-[#0E1B2E]/5 text-[#0E1B2E] border border-[#0E1B2E]/10`}
                  >
                    {children}
                  </code>
                );
              },
              p: ({ children }) => (
                <p
                  className={`${inter.className} mb-4 leading-relaxed text-[15px] text-[#0E1B2E]/80`}
                >
                  {children}
                </p>
              ),
              ul: ({ children }) => (
                <ul className="list-disc list-outside mb-4 space-y-2 ml-4 text-[#0E1B2E] marker:text-[#0E1B2E]/40">
                  {children}
                </ul>
              ),
              li: ({ children }) => (
                <li
                  className={`${inter.className} leading-relaxed text-[15px] text-[#0E1B2E]/80`}
                >
                  {children}
                </li>
              ),
              h3: ({ children }) => (
                <h3
                  className={`${inter.className} leading-relaxed text-black mb-2`}
                >
                  {children}
                </h3>
              ),
            }}
          >
            {currentStepData?.content}
          </ReactMarkdown>
        </div>
      </div>

      {/* Navigation */}
      <div className="mt-auto px-6 py-5 border-t border-[#0E1B2E]/5 flex items-center justify-between bg-slate-50/90">
        <button
          onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
          disabled={currentStep === 1}
          className={`px-5 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-2 transition-all duration-200 ${
            currentStep === 1
              ? "bg-slate-100 text-slate-400 cursor-not-allowed"
              : "bg-white text-[#0E1B2E] border border-[#0E1B2E]/10 hover:bg-slate-50 hover:border-[#0E1B2E]/20 shadow-sm"
          }`}
        >
          <ChevronLeft className="w-4 h-4" />
          <span>Previous</span>
        </button>

        <div className="flex items-center gap-1.5">
          {Array.from({ length: totalSteps }).map((_, idx) => (
            <button
              key={idx}
              onClick={() => setCurrentStep(idx + 1)}
              className={`h-1.5 rounded-full transition-all duration-300 ${
                idx + 1 === currentStep
                  ? "bg-[#0E1B2E] w-6"
                  : idx < currentStep
                    ? "bg-blue-400 w-1.5"
                    : "bg-slate-300 w-1.5 hover:bg-slate-400"
              }`}
            />
          ))}
        </div>

        <button
          onClick={() => setCurrentStep(Math.min(totalSteps, currentStep + 1))}
          disabled={currentStep === totalSteps}
          className={`px-6 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-2 transition-all duration-200 ${
            currentStep === totalSteps
              ? "bg-slate-100 text-slate-400 cursor-not-allowed"
              : "bg-[#0E1B2E] text-white hover:bg-blue-900 shadow-md hover:shadow-lg"
          }`}
        >
          <span>Next Step</span>
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
