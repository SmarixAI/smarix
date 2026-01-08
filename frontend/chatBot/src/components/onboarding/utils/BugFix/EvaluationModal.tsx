'use client';

import { X, Trophy, AlertCircle, CheckCircle, TrendingUp, Lightbulb } from 'lucide-react';

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
    if (score >= 8) return 'text-green-700';
    if (score >= 6) return 'text-yellow-700';
    if (score >= 4) return 'text-orange-700';
    return 'text-red-700';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 8) return 'bg-green-50 border-green-200';
    if (score >= 6) return 'bg-yellow-50 border-yellow-200';
    if (score >= 4) return 'bg-orange-50 border-orange-200';
    return 'bg-red-50 border-red-200';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-xl shadow-2xl bg-white">
        {/* Header */}
        <div className="sticky top-0 z-10 px-6 py-4 border-b flex items-center justify-between bg-white border-gray-200">
          <div className="flex items-center space-x-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
              evaluationData.overall_score >= 6 ? 'bg-green-100' : 'bg-red-100'
            }`}>
              <Trophy className={`w-6 h-6 ${
                evaluationData.overall_score >= 6 ? 'text-green-600' : 'text-red-600'
              }`} />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Evaluation Results
              </h2>
              <p className="text-sm text-gray-600">
                PR #{evaluationData.pr_number} - {new Date(evaluationData.evaluated_at).toLocaleString()}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg transition-colors hover:bg-gray-100 text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Overall Score */}
          <div className={`p-6 rounded-xl border ${getScoreBgColor(evaluationData.overall_score)}`}>
            <div className="text-center">
              <div className={`text-5xl font-bold mb-2 ${getScoreColor(evaluationData.overall_score)}`}>
                {evaluationData.overall_score.toFixed(1)}/10
              </div>
              <div className="text-sm font-medium text-gray-700">
                Overall Score
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 mt-6">
              <div className="text-center">
                <div className={`text-2xl font-semibold ${getScoreColor(evaluationData.correctness_score)}`}>
                  {evaluationData.correctness_score.toFixed(1)}
                </div>
                <div className="text-xs text-gray-600">
                  Correctness
                </div>
              </div>
              <div className="text-center">
                <div className={`text-2xl font-semibold ${getScoreColor(evaluationData.code_quality_score)}`}>
                  {evaluationData.code_quality_score.toFixed(1)}
                </div>
                <div className="text-xs text-gray-600">
                  Code Quality
                </div>
              </div>
              <div className="text-center">
                <div className={`text-2xl font-semibold ${getScoreColor(evaluationData.completeness_score)}`}>
                  {evaluationData.completeness_score.toFixed(1)}
                </div>
                <div className="text-xs text-gray-600">
                  Completeness
                </div>
              </div>
            </div>
          </div>

          {/* Summary */}
          <div className="p-5 rounded-lg border bg-gray-50 border-gray-200">
            <h3 className="font-semibold mb-2 text-gray-900">
              Summary
            </h3>
            <p className="text-sm text-gray-700">
              {evaluationData.evaluation_summary}
            </p>
          </div>

          {/* Strengths */}
          {evaluationData.strengths.length > 0 && (
            <div className="p-5 rounded-lg border bg-gray-50 border-gray-200">
              <div className="flex items-center space-x-2 mb-3">
                <CheckCircle className="w-5 h-5 text-gray-700" />
                <h3 className="font-semibold text-gray-900">
                  Strengths
                </h3>
              </div>
              <ul className="space-y-2">
                {evaluationData.strengths.map((strength, idx) => (
                  <li key={idx} className="text-sm flex items-start text-gray-700">
                    <span className="mr-2 text-gray-600">✓</span>
                    <span>{strength}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Areas for Improvement */}
          {evaluationData.areas_for_improvement.length > 0 && (
            <div className="p-5 rounded-lg border bg-gray-50 border-gray-200">
              <div className="flex items-center space-x-2 mb-3">
                <AlertCircle className="w-5 h-5 text-gray-700" />
                <h3 className="font-semibold text-gray-900">
                  Areas for Improvement
                </h3>
              </div>
              <ul className="space-y-2">
                {evaluationData.areas_for_improvement.map((area, idx) => (
                  <li key={idx} className="text-sm flex items-start text-gray-700">
                    <span className="mr-2 text-gray-600">→</span>
                    <span>{area}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Suggestions */}
          {evaluationData.suggestions.length > 0 && (
            <div className="p-5 rounded-lg border bg-gray-50 border-gray-200">
              <div className="flex items-center space-x-2 mb-3">
                <Lightbulb className="w-5 h-5 text-gray-700" />
                <h3 className="font-semibold text-gray-900">
                  Suggestions
                </h3>
              </div>
              <ul className="space-y-2">
                {evaluationData.suggestions.map((suggestion, idx) => (
                  <li key={idx} className="text-sm flex items-start text-gray-700">
                    <span className="mr-2 text-gray-600">💡</span>
                    <span>{suggestion}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* File-by-File Evaluation */}
          <div>
            <h3 className="font-semibold text-lg mb-4 text-gray-900">
              File Evaluations
            </h3>
            <div className="space-y-4">
              {evaluationData.file_evaluations.map((fileEval, idx) => (
                <div key={idx} className="p-4 rounded-lg border bg-gray-50 border-gray-200">
                  <div className="flex items-center justify-between mb-3">
                    <div className="font-medium text-sm text-gray-900">
                      {fileEval.file_path}
                    </div>
                    <div className="flex items-center space-x-3 text-xs">
                      <div>
                        <span className="text-gray-600">Similarity: </span>
                        <span className={`font-semibold ${getScoreColor(fileEval.similarity_to_solution / 10)}`}>
                          {fileEval.similarity_to_solution.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-3 mb-3">
                    <div className={`text-center p-2 rounded border ${getScoreBgColor(fileEval.correctness_score)}`}>
                      <div className={`text-lg font-semibold ${getScoreColor(fileEval.correctness_score)}`}>
                        {fileEval.correctness_score.toFixed(1)}
                      </div>
                      <div className="text-xs text-gray-600">
                        Correctness
                      </div>
                    </div>
                    <div className={`text-center p-2 rounded border ${getScoreBgColor(fileEval.quality_score)}`}>
                      <div className={`text-lg font-semibold ${getScoreColor(fileEval.quality_score)}`}>
                        {fileEval.quality_score.toFixed(1)}
                      </div>
                      <div className="text-xs text-gray-600">
                        Quality
                      </div>
                    </div>
                    <div className={`text-center p-2 rounded border ${getScoreBgColor(fileEval.completeness_score)}`}>
                      <div className={`text-lg font-semibold ${getScoreColor(fileEval.completeness_score)}`}>
                        {fileEval.completeness_score.toFixed(1)}
                      </div>
                      <div className="text-xs text-gray-600">
                        Completeness
                      </div>
                    </div>
                  </div>

                  <p className="text-sm mb-2 text-gray-700">
                    {fileEval.feedback}
                  </p>

                  {fileEval.improvements.length > 0 && (
                    <div className="text-xs mt-2 text-gray-600">
                      <strong>Improvements:</strong>
                      <ul className="list-disc list-inside mt-1">
                        {fileEval.improvements.map((imp, i) => (
                          <li key={i}>{imp}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
