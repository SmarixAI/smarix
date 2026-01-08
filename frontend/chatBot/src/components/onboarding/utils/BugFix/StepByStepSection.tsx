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
    <div className="rounded-lg border border-gray-200 overflow-hidden bg-white">
      {/* Progress Header */}
      <div className="px-6 py-5 border-b bg-gray-50 border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-gray-800">
              <span className="text-white font-semibold text-lg">{currentStep}</span>
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-900">
                Step {currentStep} of {totalSteps}
              </p>
              <p className="text-xs text-gray-600">
                Step-by-Step Implementation
              </p>
            </div>
          </div>
          <span className="text-sm font-semibold text-gray-700">
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
      <div className="px-6 py-6 bg-white">
        <h2 className="text-2xl font-semibold mb-4 flex items-center space-x-2 text-gray-900">
          <span className="text-gray-600">▸</span>
          <span>{currentStepData?.title}</span>
        </h2>
        
        <hr className="border-t-2 mb-6 border-gray-200" />
        
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
                <p className="mb-4 leading-relaxed text-base text-gray-700">
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
