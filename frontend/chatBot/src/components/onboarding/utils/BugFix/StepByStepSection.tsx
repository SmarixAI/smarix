'use client';

import { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';

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
    <div className="rounded-xl border border-white/25 overflow-hidden bg-white/35 backdrop-blur-xl shadow-md shadow-black/5">
      {/* Progress Header */}
      <div className="px-6 py-3 border-b bg-white/40 backdrop-blur-sm border-[#0E1B2E]/10">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-[#0E1B2E]">
              <span className="text-white font-semibold text-sm">{currentStep}</span>
            </div>
            <div>
              <p className="text-xs font-semibold text-[#0E1B2E]">
                Step {currentStep} of {totalSteps}
              </p>
              <p className="text-[10px] text-[#0E1B2E]/60">
                Step-by-Step Implementation
              </p>
            </div>
          </div>
          <span className="text-xs font-semibold text-[#0E1B2E]">
            {Math.round(progress)}% Complete
          </span>
        </div>
        
        {/* Progress Bar */}
        <div className="flex space-x-1">
          {Array.from({ length: totalSteps }).map((_, idx) => (
            <div
              key={idx}
              className={`h-2.5 flex-1 rounded-full transition-all duration-500 ${
                idx < currentStep 
                  ? 'bg-gray-700' 
                  : 'bg-gray-200'
              }`}
            />
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="px-6 py-4 bg-white">
        <h2 className="text-base font-semibold mb-3 flex items-center space-x-2 text-[#0E1B2E]">
          <span className="text-[#0E1B2E]/60">▸</span>
          <span>{currentStepData?.title}</span>
        </h2>
        
        <hr className="border-t mb-4 border-[#0E1B2E]/10" />
        
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
            }}
          >
            {currentStepData?.content}
          </ReactMarkdown>
        </div>
      </div>

      {/* Navigation */}
      <div className="px-6 py-4 border-t flex items-center justify-between bg-gray-50 border-gray-200">
        <button
          onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
          disabled={currentStep === 1}
          className={`px-6 py-3 rounded-lg font-medium flex items-center space-x-2 transition-all ${
            currentStep === 1
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-gray-900 text-white hover:bg-gray-800'
          }`}
        >
          <ChevronLeft className="w-5 h-5" />
          <span>Previous</span>
        </button>

        <div className="flex items-center space-x-2">
          {Array.from({ length: totalSteps }).map((_, idx) => (
            <button
              key={idx}
              onClick={() => setCurrentStep(idx + 1)}
              className={`w-2 h-2 rounded-full transition-all ${
                idx + 1 === currentStep
                  ? 'bg-gray-700 w-8'
                  : idx < currentStep
                  ? 'bg-gray-400'
                  : 'bg-gray-300 hover:bg-gray-400'
              }`}
            />
          ))}
        </div>

        <button
          onClick={() => setCurrentStep(Math.min(totalSteps, currentStep + 1))}
          disabled={currentStep === totalSteps}
          className={`px-6 py-3 rounded-lg font-medium flex items-center space-x-2 transition-all ${
            currentStep === totalSteps
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-gray-900 text-white hover:bg-gray-800'
          }`}
        >
          <span>Next Step</span>
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
