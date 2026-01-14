'use client';

import { X, Trophy, AlertCircle, CheckCircle, Lightbulb, FileText, ArrowRight } from 'lucide-react';
import { Inter, JetBrains_Mono } from 'next/font/google';

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700'] });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], weight: ['400', '500', '600'] });

interface FileEvaluation {
  file_path: string;
  similarity_to_solution: number;
  similarity_to_original: number;
  changes_made: number;
  correctness_score: number;
  quality_score: number;
  completeness_score: number;
  feedback: string;
  strengths: string[];
  improvements: string[];
}

interface EvaluationData {
  submission_id: string;
  pr_number: number;
  overall_score: number;
  correctness_score: number;
  code_quality_score: number;
  completeness_score: number;
  evaluation_summary: string;
  file_evaluations: FileEvaluation[];
  suggestions: string[];
  strengths: string[];
  areas_for_improvement: string[];
  evaluated_at: string;
}

interface EvaluationModalProps {
  evaluationData: EvaluationData | null;
  onClose: () => void;
}

export default function EvaluationModal({ evaluationData, onClose }: EvaluationModalProps) {
  if (!evaluationData) return null;

  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-emerald-600';
    if (score >= 6) return 'text-amber-600';
    if (score >= 4) return 'text-orange-600';
    return 'text-rose-600';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 8) return 'bg-emerald-50 border-emerald-100';
    if (score >= 6) return 'bg-amber-50 border-amber-100';
    if (score >= 4) return 'bg-orange-50 border-orange-100';
    return 'bg-rose-50 border-rose-100';
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-[#0E1B2E]/40 backdrop-blur-sm p-4 animate-in fade-in duration-300">
      <div className="w-full max-w-4xl max-h-[90vh] flex flex-col rounded-2xl shadow-2xl bg-white overflow-hidden animate-in zoom-in-95 duration-300">
        
        {/* Header */}
        <div className="px-8 py-5 border-b border-[#0E1B2E]/5 flex items-center justify-between bg-white sticky top-0 z-20">
          <div className="flex items-center gap-4">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center border-2 ${
              evaluationData.overall_score >= 6 ? 'bg-emerald-50 border-emerald-100' : 'bg-rose-50 border-rose-100'
            }`}>
              <Trophy className={`w-6 h-6 ${
                evaluationData.overall_score >= 6 ? 'text-emerald-600' : 'text-rose-600'
              }`} />
            </div>
            <div>
              <h2 className={`${inter.className} text-xl font-bold text-[#0E1B2E]`}>
                Evaluation Results
              </h2>
              <div className="flex items-center gap-2 mt-1">
                 <span className={`${jetbrainsMono.className} text-xs font-bold px-2 py-0.5 rounded bg-[#0E1B2E]/5 text-[#0E1B2E]/60`}>
                    PR #{evaluationData.pr_number}
                 </span>
                 <span className={`${inter.className} text-xs text-[#0E1B2E]/40`}>
                    {new Date(evaluationData.evaluated_at).toLocaleString()}
                 </span>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 text-[#0E1B2E]/40 hover:text-[#0E1B2E] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="overflow-y-auto p-8 space-y-8 bg-slate-50/50">
          {/* Score Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
             <div className={`p-6 rounded-2xl border-2 flex flex-col items-center justify-center bg-white ${getScoreBgColor(evaluationData.overall_score)}`}>
                <div className={`${jetbrainsMono.className} text-4xl font-bold mb-1 ${getScoreColor(evaluationData.overall_score)}`}>
                   {evaluationData.overall_score.toFixed(1)}
                </div>
                <div className={`${inter.className} text-xs font-bold uppercase tracking-wider text-[#0E1B2E]/60`}>Overall Score</div>
             </div>
             
             {[
                { label: 'Correctness', score: evaluationData.correctness_score },
                { label: 'Code Quality', score: evaluationData.code_quality_score },
                { label: 'Completeness', score: evaluationData.completeness_score },
             ].map((item, i) => (
                <div key={i} className="p-4 rounded-xl bg-white border border-[#0E1B2E]/5 shadow-sm flex flex-col items-center justify-center">
                   <div className={`${jetbrainsMono.className} text-2xl font-bold mb-1 ${getScoreColor(item.score)}`}>
                      {item.score.toFixed(1)}
                   </div>
                   <div className={`${inter.className} text-xs font-semibold text-[#0E1B2E]/40`}>{item.label}</div>
                </div>
             ))}
          </div>

          {/* Summary */}
          <div className="bg-white rounded-xl border border-[#0E1B2E]/5 p-6 shadow-sm">
            <h3 className={`${inter.className} text-sm font-bold uppercase tracking-wide text-[#0E1B2E] mb-3`}>
              Executive Summary
            </h3>
            <p className={`${inter.className} text-sm leading-relaxed text-[#0E1B2E]/70`}>
              {evaluationData.evaluation_summary}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Strengths */}
            {evaluationData.strengths.length > 0 && (
              <div className="bg-white rounded-xl border border-emerald-100 p-6 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <CheckCircle className="w-5 h-5 text-emerald-500" />
                  <h3 className={`${inter.className} font-bold text-[#0E1B2E]`}>Key Strengths</h3>
                </div>
                <ul className="space-y-3">
                  {evaluationData.strengths.map((strength, idx) => (
                    <li key={idx} className="flex gap-3 text-sm text-[#0E1B2E]/70">
                      <span className="text-emerald-500 mt-0.5 font-bold">✓</span>
                      <span>{strength}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Improvements */}
            {evaluationData.areas_for_improvement.length > 0 && (
              <div className="bg-white rounded-xl border border-rose-100 p-6 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <AlertCircle className="w-5 h-5 text-rose-500" />
                  <h3 className={`${inter.className} font-bold text-[#0E1B2E]`}>Areas for Improvement</h3>
                </div>
                <ul className="space-y-3">
                  {evaluationData.areas_for_improvement.map((area, idx) => (
                    <li key={idx} className="flex gap-3 text-sm text-[#0E1B2E]/70">
                      <span className="text-rose-500 mt-0.5 font-bold">!</span>
                      <span>{area}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Detailed File Breakdown */}
          <div>
            <h3 className={`${inter.className} text-lg font-bold text-[#0E1B2E] mb-4 flex items-center gap-2`}>
               <FileText className="w-5 h-5 text-[#0E1B2E]/40" />
               File Analysis
            </h3>
            <div className="space-y-4">
              {evaluationData.file_evaluations.map((fileEval, idx) => (
                <div key={idx} className="bg-white rounded-xl border border-[#0E1B2E]/10 overflow-hidden shadow-sm">
                  <div className="px-6 py-4 bg-[#0E1B2E]/[0.02] border-b border-[#0E1B2E]/5 flex items-center justify-between">
                    <div className={`${jetbrainsMono.className} text-sm font-bold text-[#0E1B2E]`}>
                      {fileEval.file_path}
                    </div>
                    <div className={`${jetbrainsMono.className} text-xs font-bold px-2 py-1 rounded bg-white border border-[#0E1B2E]/10 text-[#0E1B2E]/60`}>
                      Match: {fileEval.similarity_to_solution.toFixed(1)}%
                    </div>
                  </div>

                  <div className="p-6">
                     <div className="grid grid-cols-3 gap-4 mb-6">
                        {[
                           { label: 'Correctness', score: fileEval.correctness_score },
                           { label: 'Quality', score: fileEval.quality_score },
                           { label: 'Completeness', score: fileEval.completeness_score },
                        ].map((metric, i) => (
                           <div key={i} className="bg-slate-50 rounded-lg p-3 text-center border border-slate-100">
                              <div className={`${jetbrainsMono.className} font-bold ${getScoreColor(metric.score)}`}>
                                 {metric.score.toFixed(1)}
                              </div>
                              <div className="text-[10px] uppercase font-bold text-slate-400 mt-1">{metric.label}</div>
                           </div>
                        ))}
                     </div>

                    <p className={`${inter.className} text-sm text-[#0E1B2E]/70 mb-4 bg-slate-50 p-4 rounded-lg border border-slate-100 italic`}>
                      "{fileEval.feedback}"
                    </p>

                    {fileEval.improvements.length > 0 && (
                      <div>
                        <h4 className="text-xs font-bold uppercase tracking-wide text-[#0E1B2E]/40 mb-2">Specific Improvements</h4>
                        <ul className="space-y-1.5">
                          {fileEval.improvements.map((imp, i) => (
                            <li key={i} className="text-sm flex gap-2 text-[#0E1B2E]/60">
                               <ArrowRight className="w-4 h-4 text-[#0E1B2E]/20 flex-shrink-0 mt-0.5" />
                               <span>{imp}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        <div className="p-4 border-t border-[#0E1B2E]/5 bg-white flex justify-end">
           <button 
             onClick={onClose}
             className={`${inter.className} px-6 py-2.5 bg-[#0E1B2E] text-white rounded-lg font-bold text-sm hover:bg-blue-900 transition-colors shadow-lg shadow-[#0E1B2E]/10`}
           >
             Close Evaluation
           </button>
        </div>
      </div>
    </div>
  );
}