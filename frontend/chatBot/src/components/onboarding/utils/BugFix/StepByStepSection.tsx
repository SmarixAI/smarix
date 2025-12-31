'use client';

import { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight, vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface Step {
  title: string;
  content: string;
}

interface StepByStepSectionProps {
  steps: Step[];
  darkMode: boolean;
}

export default function StepByStepSection({ steps, darkMode }: StepByStepSectionProps) {
  const [currentStep, setCurrentStep] = useState(1);
  
  const totalSteps = steps.length;
  const progress = (currentStep / totalSteps) * 100;
  const currentStepData = steps[currentStep - 1];

  return (
    <div className={`rounded-2xl border-2 overflow-hidden shadow-xl ${
      darkMode
        ? 'border-orange-700 bg-gradient-to-br from-orange-900/30 to-amber-900/30'
        : 'border-orange-200 bg-gradient-to-br from-orange-50 to-amber-50'
    }`}>
      {/* Progress Header */}
      <div className={`px-6 py-5 border-b ${
        darkMode
          ? 'bg-gray-800 border-orange-700'
          : 'bg-white border-orange-200'
      }`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
              darkMode ? 'bg-orange-600' : 'bg-orange-500'
            }`}>
              <span className="text-white font-bold text-lg">{currentStep}</span>
            </div>
            <div>
              <p className={`text-sm font-semibold ${darkMode ? 'text-gray-200' : 'text-slate-700'}`}>
                Step {currentStep} of {totalSteps}
              </p>
              <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-slate-500'}`}>
                Step-by-Step Implementation
              </p>
            </div>
          </div>
          <span className={`text-sm font-bold ${darkMode ? 'text-orange-400' : 'text-orange-600'}`}>
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
                  ? 'bg-gradient-to-r from-red-500 to-orange-500 shadow-md' 
                  : darkMode ? 'bg-gray-700' : 'bg-gray-200'
              }`}
            />
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className={`px-6 py-6 ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
        <h2 className={`text-2xl font-bold mb-4 flex items-center space-x-2 ${
          darkMode ? 'text-white' : 'text-slate-900'
        }`}>
          <span className={darkMode ? 'text-orange-400' : 'text-orange-500'}>▸</span>
          <span>{currentStepData?.title}</span>
        </h2>
        
        <hr className={`border-t-2 mb-6 ${darkMode ? 'border-orange-800' : 'border-orange-100'}`} />
        
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
                      border: darkMode ? '2px solid #9a3412' : '2px solid #fed7aa',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                    }}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className={`px-2 py-1 rounded text-sm font-mono border ${
                    darkMode
                      ? 'bg-orange-900/50 text-orange-300 border-orange-700'
                      : 'bg-orange-100 text-orange-800 border-orange-200'
                  }`}>
                    {children}
                  </code>
                );
              },
              p: ({ children }) => (
                <p className={`mb-4 leading-relaxed text-base ${
                  darkMode ? 'text-gray-300' : 'text-slate-700'
                }`}>
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
      <div className={`px-6 py-4 border-t flex items-center justify-between ${
        darkMode
          ? 'bg-gradient-to-r from-orange-900/30 to-amber-900/30 border-orange-700'
          : 'bg-gradient-to-r from-orange-50 to-amber-50 border-orange-200'
      }`}>
        <button
          onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
          disabled={currentStep === 1}
          className={`px-6 py-3 rounded-xl font-semibold flex items-center space-x-2 transition-all shadow-md ${
            currentStep === 1
              ? darkMode
                ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              : darkMode
              ? 'bg-gray-700 text-gray-200 hover:bg-gray-600 border-2 border-gray-600 hover:scale-105'
              : 'bg-white text-slate-700 hover:bg-slate-50 border-2 border-slate-300 hover:scale-105'
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
              className={`w-3 h-3 rounded-full transition-all ${
                idx + 1 === currentStep
                  ? darkMode ? 'bg-orange-500 w-8' : 'bg-orange-500 w-8'
                  : idx < currentStep
                  ? darkMode ? 'bg-orange-600' : 'bg-orange-300'
                  : darkMode ? 'bg-gray-600' : 'bg-gray-300'
              }`}
            />
          ))}
        </div>

        <button
          onClick={() => setCurrentStep(Math.min(totalSteps, currentStep + 1))}
          disabled={currentStep === totalSteps}
          className={`px-6 py-3 rounded-xl font-semibold flex items-center space-x-2 transition-all shadow-md ${
            currentStep === totalSteps
              ? darkMode
                ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-red-600 to-orange-600 text-white hover:from-red-700 hover:to-orange-700 hover:scale-105'
          }`}
        >
          <span>Next Step</span>
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
