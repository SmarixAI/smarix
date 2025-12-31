"use client";

import {
  X,
  BookOpen,
  CheckCircle2,
  XCircle,
  Loader2,
  Award,
} from "lucide-react";
import { useEffect, useState, useCallback, useMemo } from "react";
import { QAService } from "../../services/QASession/contentService";
import type { QuestionData } from "../../../../../types/onboarding";

interface QAModalProps {
  isOpen: boolean;
  onClose: () => void;
  darkMode: boolean;
  title: string;
  moduleId: string;
}

export default function QAModal({
  isOpen,
  onClose,
  darkMode,
  title,
  moduleId,
}: QAModalProps) {
  const [questions, setQuestions] = useState<QuestionData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedAnswers, setSelectedAnswers] = useState<{ [key: string]: string }>({});
  const [revealedAnswers, setRevealedAnswers] = useState<Set<string>>(new Set());
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    if (isOpen && moduleId) {
      setIsLoading(true);
      document.body.style.overflow = "hidden";

      const fetchQuestions = async () => {
        const response = await QAService.fetchQAModule(moduleId);

        if (response && response.questions) {
          setQuestions(response.questions);
        }

        setIsLoading(false);
      };

      fetchQuestions();
    } else {
      document.body.style.overflow = "unset";
      setQuestions([]);
      setSelectedAnswers({});
      setRevealedAnswers(new Set());
      setScrollProgress(0);
    }

    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen, moduleId]);

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const target = e.target as HTMLDivElement;
    const scrollHeight = target.scrollHeight - target.clientHeight;
    const progress = scrollHeight > 0 ? (target.scrollTop / scrollHeight) * 100 : 0;
    setScrollProgress(Math.min(100, Math.max(0, progress)));
  }, []);

  const handleAnswerSelect = useCallback((questionNumber: number, option: string) => {
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionNumber]: option,
    }));
  }, []);

  const handleRevealAnswer = useCallback((questionNumber: number) => {
    setRevealedAnswers((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(String(questionNumber))) {
        newSet.delete(String(questionNumber));
      } else {
        newSet.add(String(questionNumber));
      }
      return newSet;
    });
  }, []);

  const handleBackdropClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  }, [onClose]);

  const stats = useMemo(() => {
    const answered = Object.keys(selectedAnswers).length;
    const correct = questions.filter(
      (q) => selectedAnswers[q.question_number] === q.correct_answer
    ).length;
    const total = questions.length;
    const percentage = total > 0 ? Math.round((correct / total) * 100) : 0;

    return { answered, correct, total, percentage };
  }, [selectedAnswers, questions]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4"
      onClick={handleBackdropClick}
    >
      <style jsx global>{`
        @keyframes modalSlideUp {
          from {
            opacity: 0;
            transform: translateY(100px) scale(0.9);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }

        @keyframes backdropFade {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        @keyframes shimmer {
          0% { background-position: -200% center; }
          100% { background-position: 200% center; }
        }

        .modal-backdrop {
          animation: backdropFade 0.3s ease-out;
        }

        .modal-content {
          animation: modalSlideUp 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
          will-change: transform, opacity;
        }

        .shimmer-background {
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
          background-size: 200% 100%;
          animation: shimmer 3s infinite;
        }

        .custom-scrollbar {
          will-change: scroll-position;
          transform: translateZ(0);
        }

        .custom-scrollbar::-webkit-scrollbar {
          width: 10px;
        }

        .custom-scrollbar::-webkit-scrollbar-track {
          background: ${darkMode ? "#1f2937" : "#f1f5f9"};
          border-radius: 10px;
          margin: 8px 0;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: ${darkMode
            ? "linear-gradient(180deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%)"
            : "linear-gradient(180deg, #6366f1 0%, #06b6d4 50%, #14b8a6 100%)"};
          border-radius: 10px;
          border: 2px solid ${darkMode ? "#1f2937" : "#f1f5f9"};
        }

        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: ${darkMode
            ? "linear-gradient(180deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%)"
            : "linear-gradient(180deg, #4f46e5 0%, #0891b2 50%, #0d9488 100%)"};
        }
      `}</style>

      <div
        className={`absolute inset-0 modal-backdrop ${
          darkMode
            ? "bg-gradient-to-br from-gray-900/95 via-blue-900/90 to-purple-900/95"
            : "bg-gradient-to-br from-slate-900/60 via-indigo-900/50 to-cyan-900/60"
        } backdrop-blur-xl`}
      />

      <div
        className={`relative w-full max-w-7xl max-h-[92vh] rounded-3xl overflow-hidden modal-content ${
          darkMode ? "glass-card-dark" : "glass-card-light"
        }`}
        style={{
          boxShadow: darkMode
            ? "0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.1)"
            : "0 25px 50px -12px rgba(0, 0, 0, 0.25), 0 0 0 1px rgba(255, 255, 255, 0.5)",
        }}
      >
        <div className="absolute top-0 left-0 right-0 h-1 z-20 bg-gray-700/30">
          <div
            className={`h-full transition-all duration-300 ${
              darkMode
                ? "bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"
                : "bg-gradient-to-r from-indigo-500 via-cyan-500 to-teal-500"
            }`}
            style={{ width: `${scrollProgress}%` }}
          />
        </div>

        <div
          className={`sticky top-0 z-10 px-8 py-5 border-b backdrop-blur-2xl ${
            darkMode
              ? "bg-gray-800/98 border-gray-700/50"
              : "bg-white/98 border-indigo-100/50"
          }`}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1 pr-8">
              <div className="flex items-center space-x-4 mb-3">
                <div
                  className={`w-12 h-12 rounded-xl flex items-center justify-center shadow-2xl relative overflow-hidden ${
                    darkMode
                      ? "bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600"
                      : "bg-gradient-to-br from-indigo-500 via-cyan-500 to-teal-500"
                  }`}
                >
                  <div className="absolute inset-0 shimmer-background" />
                  <BookOpen className="w-6 h-6 text-white relative z-10" />
                </div>

                <div>
                  <h2
                    className={`text-3xl font-bold mb-1 ${
                      darkMode
                        ? "bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent"
                        : "bg-gradient-to-r from-indigo-600 via-cyan-600 to-teal-600 bg-clip-text text-transparent"
                    }`}
                  >
                    {title}
                  </h2>
                  <p className={`text-xs ${darkMode ? "text-gray-500" : "text-slate-500"}`}>
                    Q&A Session
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-6">
                <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg ${
                  darkMode ? "bg-blue-500/10" : "bg-indigo-50"
                }`}>
                  <Award className={`w-4 h-4 ${darkMode ? "text-blue-400" : "text-indigo-500"}`} />
                  <span className={`text-xs font-medium ${
                    darkMode ? "text-blue-300" : "text-indigo-700"
                  }`}>
                    {stats.answered}/{stats.total} Answered
                  </span>
                </div>

                <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg ${
                  darkMode ? "bg-green-500/10" : "bg-green-50"
                }`}>
                  <CheckCircle2 className={`w-4 h-4 ${darkMode ? "text-green-400" : "text-green-500"}`} />
                  <span className={`text-xs font-medium ${
                    darkMode ? "text-green-300" : "text-green-700"
                  }`}>
                    {stats.correct} Correct ({stats.percentage}%)
                  </span>
                </div>
              </div>
            </div>

            <button
              onClick={onClose}
              className={`p-3 rounded-xl transition-all duration-300 hover:rotate-90 hover:scale-110 group ${
                darkMode ? "hover:bg-gray-700" : "hover:bg-indigo-50"
              }`}
              aria-label="Close modal"
            >
              <X
                className={`w-6 h-6 transition-colors ${
                  darkMode
                    ? "text-gray-400 group-hover:text-white"
                    : "text-slate-500 group-hover:text-slate-900"
                }`}
              />
            </button>
          </div>
        </div>

        <div
          className="overflow-y-auto px-8 py-8 custom-scrollbar"
          style={{
            maxHeight: "calc(92vh - 200px)",
            minHeight: "300px",
          }}
          onScroll={handleScroll}
        >
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-32">
              <div className="relative">
                <Loader2 className={`w-20 h-20 animate-spin ${
                  darkMode ? "text-blue-400" : "text-indigo-600"
                }`} />
              </div>
              <p className={`mt-6 text-sm font-medium ${
                darkMode ? "text-gray-400" : "text-slate-600"
              }`}>
                Loading questions...
              </p>
            </div>
          ) : questions.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-32">
              <p className={`text-lg font-medium ${
                darkMode ? "text-gray-400" : "text-slate-600"
              }`}>
                No questions found
              </p>
            </div>
          ) : (
            <div className="space-y-8">
              {questions.map((question) => {
                const qKey = String(question.question_number);
                const selectedOption = selectedAnswers[question.question_number];
                const isRevealed = revealedAnswers.has(qKey);
                const isCorrect = selectedOption === question.correct_answer;

                return (
                  <div
                    key={question.question_number}
                    className={`rounded-2xl overflow-hidden transition-all ${
                      darkMode
                        ? "bg-gray-800/50 ring-1 ring-gray-700"
                        : "bg-white/50 ring-1 ring-slate-200"
                    }`}
                  >
                    <div
                      className={`px-6 py-4 border-b ${
                        darkMode
                          ? "bg-gray-800/80 border-gray-700"
                          : "bg-slate-50/80 border-slate-200"
                      }`}
                    >
                      <h3
                        className={`text-lg font-bold ${
                          darkMode ? "text-gray-100" : "text-slate-900"
                        }`}
                      >
                        {question.question_number}. {question.question}
                      </h3>
                    </div>

                    <div className="p-6 space-y-3">
                      {Object.entries(question.options).map(([optKey, optText]) => {
                        const isSelected = selectedOption === optKey;
                        const isCorrectOption = optKey === question.correct_answer;
                        const showCorrect = isRevealed && isCorrectOption;
                        const showWrong = isRevealed && isSelected && !isCorrect;

                        return (
                          <button
                            key={optKey}
                            onClick={() => handleAnswerSelect(question.question_number, optKey)}
                            className={`w-full text-left px-4 py-3 rounded-lg border text-sm transition-all ${
                              showCorrect
                                ? darkMode
                                  ? "bg-green-600/30 border-green-400 text-green-200"
                                  : "bg-green-100 border-green-500 text-green-900"
                                : showWrong
                                ? darkMode
                                  ? "bg-red-600/30 border-red-400 text-red-200"
                                  : "bg-red-100 border-red-500 text-red-900"
                                : isSelected
                                ? darkMode
                                  ? "bg-blue-600/40 border-blue-400 text-white"
                                  : "bg-indigo-200 border-indigo-500 text-slate-900"
                                : darkMode
                                ? "bg-gray-800/50 border-gray-700 text-gray-200 hover:bg-gray-800/70"
                                : "bg-white border-gray-300 text-slate-700 hover:bg-indigo-50"
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <span>
                                <strong>{optKey}:</strong> {optText as string}
                              </span>
                              {showCorrect && <CheckCircle2 className="w-5 h-5 text-green-500" />}
                              {showWrong && <XCircle className="w-5 h-5 text-red-500" />}
                            </div>
                          </button>
                        );
                      })}

                      <button
                        onClick={() => handleRevealAnswer(question.question_number)}
                        className={`mt-4 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                          darkMode
                            ? "bg-blue-600/30 border border-blue-400/40 text-blue-300 hover:bg-blue-600/50"
                            : "bg-indigo-100 text-indigo-700 border border-indigo-300 hover:bg-indigo-200"
                        }`}
                      >
                        {isRevealed ? "Hide Answer" : "Show Answer"}
                      </button>

                      {isRevealed && (
                        <div
                          className={`mt-4 p-4 rounded-lg ${
                            darkMode
                              ? "bg-gray-900/50 border border-gray-700"
                              : "bg-slate-50 border border-slate-200"
                          }`}
                        >
                          <p
                            className={`font-semibold mb-2 ${
                              darkMode ? "text-green-300" : "text-green-700"
                            }`}
                          >
                            Correct Answer: <strong>{question.correct_answer}</strong>
                          </p>
                          <p
                            className={`text-sm leading-relaxed ${
                              darkMode ? "text-gray-300" : "text-slate-700"
                            }`}
                          >
                            {question.explanation}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div
          className={`sticky bottom-0 px-8 py-5 border-t backdrop-blur-2xl ${
            darkMode
              ? "bg-gray-800/98 border-gray-700/50"
              : "bg-white/98 border-indigo-100/50"
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className={`text-xs font-medium ${
                darkMode ? "text-gray-500" : "text-slate-500"
              }`}>
                {isLoading
                  ? `Loading questions...`
                  : `${Math.round(scrollProgress)}% Complete`}
              </div>
            </div>

            <button
              onClick={onClose}
              className={`px-8 py-3 rounded-xl font-bold transition-all transform hover:scale-105 active:scale-95 shadow-xl relative overflow-hidden group ${
                darkMode
                  ? "bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 hover:from-blue-500 hover:via-purple-500 hover:to-pink-500 text-white"
                  : "bg-gradient-to-r from-indigo-500 via-cyan-500 to-teal-500 hover:from-indigo-600 hover:via-cyan-600 hover:to-teal-600 text-white"
              }`}
            >
              <span className="relative z-10">Close Quiz</span>
              <div className="absolute inset-0 shimmer-background" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
