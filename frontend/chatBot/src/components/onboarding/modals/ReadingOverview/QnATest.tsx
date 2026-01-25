"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Clock, CheckCircle2, XCircle, FileText, Send } from "lucide-react";
import { Inter, JetBrains_Mono } from 'next/font/google';

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700'] });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], weight: ['400', '500', '600'] });

interface QnATestProps {
  questions: Array<{
    question: string;
    options: { [key: string]: string };
    correct_answer: string;
    explanation: string;
    subsection?: string;
  }>;
  sectionTitle?: string;
  employeeId?: string | null;
  moduleId?: string;
  onProgressUpdate?: () => void;
}

export default function QnATest({ questions, sectionTitle, employeeId, moduleId, onProgressUpdate }: QnATestProps) {
  const [selectedAnswers, setSelectedAnswers] = useState<{ [key: number]: string }>({});
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(600); // 10 minutes in seconds
  const [isTimerRunning, setIsTimerRunning] = useState(true);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Calculate time based on number of questions (1 minute per question, minimum 5 minutes)
  useEffect(() => {
    const calculatedTime = Math.max(300, questions.length * 60); // 5 min minimum, 1 min per question
    setTimeRemaining(calculatedTime);
  }, [questions.length]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleAnswerSelect = (questionIndex: number, answer: string) => {
    if (!isSubmitted) {
      setSelectedAnswers((prev) => ({
        ...prev,
        [questionIndex]: answer,
      }));
    }
  };

  const handleSubmit = async () => {
    setIsSubmitted(true);
    setIsTimerRunning(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    // Progress will be saved in the useEffect hook when isSubmitted becomes true
  };

  const calculateScore = useCallback(() => {
    let correct = 0;
    questions.forEach((q, index) => {
      if (selectedAnswers[index] === q.correct_answer) {
        correct++;
      }
    });
    return { correct, total: questions.length, percentage: Math.round((correct / questions.length) * 100) };
  }, [questions, selectedAnswers]);

  // Timer effect
  useEffect(() => {
    if (isTimerRunning && !isSubmitted && timeRemaining > 0) {
      intervalRef.current = setInterval(() => {
        setTimeRemaining((prev) => {
          if (prev <= 1) {
            setIsTimerRunning(false);
            // Trigger submit when time runs out
            setIsSubmitted(true);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isTimerRunning, isSubmitted, timeRemaining]);

  // Save progress when test is submitted (either manually or by timer)
  useEffect(() => {
    if (isSubmitted && employeeId && moduleId) {
      const scoreData = calculateScore();
      
      const saveProgress = async () => {
        try {
          const response = await fetch('/api/onboarding/progress', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              employeeId,
              section: 'qa',
              itemId: moduleId,
              updates: {
                status: 'completed',
                score: scoreData.correct,
                totalQuestions: scoreData.total,
                percentage: scoreData.percentage,
                progress: 100,
                completedAt: new Date().toISOString(),
              },
            }),
          });

          if (response.ok && onProgressUpdate) {
            onProgressUpdate();
          }
        } catch (error) {
          console.error('Error saving QnA progress:', error);
        }
      };

      saveProgress();
    }
  }, [isSubmitted, employeeId, moduleId, calculateScore, onProgressUpdate]);

  const score = isSubmitted ? calculateScore() : null;

  return (
    <div className="space-y-6">
      {/* Header with Timer */}
      <div className="flex items-center justify-between px-6 py-4 rounded-2xl bg-white border border-slate-200 shadow-sm">
        <div>
          <h3 className={`${inter.className} text-lg font-bold text-[#0E1B2E] mb-1`}>
            {sectionTitle || "Tech Stack Assessment"}
          </h3>
          <p className={`${inter.className} text-sm text-slate-600`}>
            {questions.length} Questions • Complete the test to see your results
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div
            className={`${jetbrainsMono.className} flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold ${
              timeRemaining < 60
                ? 'bg-red-100 text-red-700 border-2 border-red-300'
                : timeRemaining < 300
                ? 'bg-yellow-100 text-yellow-700 border-2 border-yellow-300'
                : 'bg-white text-blue-700 border-2 border-blue-300'
            }`}
          >
            <Clock className="w-5 h-5" />
            {formatTime(timeRemaining)}
          </div>
        </div>
      </div>

      {/* Questions */}
      <div className="space-y-6">
        {questions.map((qnaItem, qnaIndex) => {
          const userAnswer = selectedAnswers[qnaIndex];
          const isCorrect = userAnswer === qnaItem.correct_answer;
          const showResults = isSubmitted;

          return (
            <div
              key={qnaIndex}
              className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-5"
            >
              <div className="mb-4">
                <div className="flex items-center space-x-2 mb-3">
                  <span
                    className={`${jetbrainsMono.className} text-xs font-bold text-blue-600 bg-blue-50 px-3 py-1.5 rounded-lg border border-blue-200`}
                  >
                    Question {qnaIndex + 1}
                  </span>
                  {qnaItem.subsection && (
                    <span className={`${inter.className} text-xs text-slate-500 italic`}>
                      {qnaItem.subsection}
                    </span>
                  )}
                  {showResults && (
                    <span
                      className={`text-xs font-semibold px-3 py-1 rounded-full ${
                        isCorrect
                          ? "bg-emerald-50 text-emerald-700"
                          : "bg-rose-50 text-rose-700"
                      }`}
                    >
                      {isCorrect ? (
                        <span className="flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" />
                          Correct
                        </span>
                      ) : (
                        <span className="flex items-center gap-1">
                          <XCircle className="w-3 h-3" />
                          Incorrect
                        </span>
                      )}
                    </span>
                  )}
                </div>
                <h4 className={`${inter.className} text-base font-semibold text-[#0E1B2E] mb-4 leading-relaxed`}>
                  {qnaItem.question}
                </h4>
              </div>

              {qnaItem.options && (
                <div className="mb-5">
                  <div className="space-y-3">
                    {Object.entries(qnaItem.options).map(([key, value]) => {
                      const isSelected = userAnswer === key;
                      const isCorrectOption = key === qnaItem.correct_answer;
                      const showCorrect = showResults && isCorrectOption;
                      const showIncorrect = showResults && isSelected && !isCorrectOption;

                      return (
                        <div
                          key={key}
                          onClick={() => handleAnswerSelect(qnaIndex, key)}
                          className={`p-4 rounded-xl border-2 transition-all cursor-pointer ${
                            !showResults
                              ? isSelected
                                ? 'bg-blue-50 border-blue-300 shadow-sm'
                                : 'bg-slate-50 border-slate-200 hover:border-blue-300 hover:bg-blue-50/50'
                              : showCorrect
                              ? 'bg-green-50 border-green-300 shadow-sm'
                              : showIncorrect
                              ? 'bg-red-50 border-red-300 shadow-sm'
                              : isSelected
                              ? 'bg-slate-100 border-slate-300'
                              : 'bg-slate-50 border-slate-200'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <span
                                className={`${inter.className} font-bold text-[#0E1B2E] w-8 h-8 rounded-lg flex items-center justify-center ${
                                  !showResults
                                    ? isSelected
                                      ? 'bg-blue-200 text-blue-700'
                                      : 'bg-slate-200 text-slate-600'
                                    : showCorrect
                                    ? 'bg-green-200 text-green-700'
                                    : showIncorrect
                                    ? 'bg-red-200 text-red-700'
                                    : 'bg-slate-200 text-slate-600'
                                }`}
                              >
                                {key}
                              </span>
                              <span className={`${inter.className} text-sm text-slate-700`}>
                                {value as string}
                              </span>
                            </div>
                            {showResults && showCorrect && (
                              <span
                                className={`${inter.className} text-xs font-bold text-green-700 bg-green-100 px-2 py-1 rounded-md flex items-center gap-1`}
                              >
                                <CheckCircle2 className="w-3 h-3" />
                                Correct Answer
                              </span>
                            )}
                            {showResults && showIncorrect && (
                              <span
                                className={`${inter.className} text-xs font-bold text-red-700 bg-red-100 px-2 py-1 rounded-md flex items-center gap-1`}
                              >
                                <XCircle className="w-3 h-3" />
                                Your Answer
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {showResults && qnaItem.explanation && (
                <div className="mt-4 p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <h5
                    className={`${inter.className} text-sm font-bold text-blue-900 mb-3 flex items-center gap-2`}
                  >
                    <FileText className="w-4 h-4" />
                    Explanation:
                  </h5>
                  <p className={`${inter.className} text-sm text-blue-800 leading-relaxed`}>
                    {qnaItem.explanation}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Submit Button at Bottom */}
      {!isSubmitted && (
        <div className="mt-8 pt-6 border-t-2 border-slate-200">
          <div className="flex items-center justify-between">
            <div className={`${inter.className} text-sm text-slate-600`}>
              {Object.keys(selectedAnswers).length} of {questions.length} questions answered
            </div>
            <button
              onClick={handleSubmit}
              disabled={Object.keys(selectedAnswers).length === 0}
              className={`${inter.className} flex items-center gap-2 px-8 py-3 rounded-xl font-semibold text-base transition-all ${
                Object.keys(selectedAnswers).length === 0
                  ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700 shadow-md hover:shadow-lg transform hover:scale-105'
              }`}
            >
              <Send className="w-5 h-5" />
              Submit Test
            </button>
          </div>
        </div>
      )}

      {/* Results Summary */}
      {isSubmitted && score && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 text-center space-y-4">
          <div className="text-center mb-4">
            <h3 className={`${inter.className} text-2xl font-bold text-[#0E1B2E] mb-2`}>
              Test Results
            </h3>
            <div className={`${jetbrainsMono.className} text-5xl font-bold mb-2 ${
              score.percentage >= 80
                ? 'text-green-600'
                : score.percentage >= 60
                ? 'text-yellow-600'
                : 'text-red-600'
            }`}>
              {score.percentage}%
            </div>
            <p className={`${inter.className} text-base text-slate-600`}>
              You scored {score.correct} out of {score.total} questions correctly
            </p>
          </div>
          <div className="mt-4 pt-4 border-t border-blue-200">
            <div className="flex items-center justify-center gap-4">
              <div className="text-center">
                <div className={`${inter.className} text-2xl font-bold text-green-600`}>
                  {score.correct}
                </div>
                <div className={`${inter.className} text-xs text-slate-600`}>Correct</div>
              </div>
              <div className="w-px h-12 bg-blue-200"></div>
              <div className="text-center">
                <div className={`${inter.className} text-2xl font-bold text-red-600`}>
                  {score.total - score.correct}
                </div>
                <div className={`${inter.className} text-xs text-slate-600`}>Incorrect</div>
              </div>
              <div className="w-px h-12 bg-blue-200"></div>
              <div className="text-center">
                <div className={`${inter.className} text-2xl font-bold text-blue-600`}>
                  {score.total}
                </div>
                <div className={`${inter.className} text-xs text-slate-600`}>Total</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

