'use client';

import { useState, useEffect } from 'react';
import { RotateCcw, Download, Loader2, CheckCircle, ChevronLeft, ChevronRight, FileCode, MoveHorizontal, Minimize2, Sparkles, ChevronsLeftRight } from 'lucide-react';
import Editor from '@monaco-editor/react';

interface FileChange {
  file_path: string;
  change_type: string;
  diff: string;
  before_code: string;
  after_code: string;
  statistics: {
    lines_added: number;
    lines_deleted: number;
    total_changes: number;
  };
}

interface PullRequest {
  pr_number: number;
  file_changes: FileChange[];
}

interface CodeEditorProps {
  prData?: PullRequest;
  isFullscreen?: boolean;
  onToggleFullscreen?: () => void;
  onEvaluationComplete?: (evaluationData: any) => void;
}

interface FileEditorState {
  [filePath: string]: string;
}

export default function CodeEditor({ 
  prData, 
  isFullscreen, 
  onToggleFullscreen,
  onEvaluationComplete 
}: CodeEditorProps) {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContents, setFileContents] = useState<FileEditorState>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [submissionStatus, setSubmissionStatus] = useState<'idle' | 'submitting' | 'evaluating' | 'complete'>('idle');
  const [showFileList, setShowFileList] = useState(true);
  const [filesWidth, setFilesWidth] = useState(288); // Default 72 * 4 = 288px (w-72)
  const [isResizingFiles, setIsResizingFiles] = useState(false);

  useEffect(() => {
    if (prData && prData.file_changes.length > 0) {
      const initialContents: FileEditorState = {};
      prData.file_changes.forEach((fileChange) => {
        initialContents[fileChange.file_path] = fileChange.before_code;
      });
      setFileContents(initialContents);
      setSelectedFile(prData.file_changes[0].file_path);
    }
  }, [prData]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizingFiles) return;
      
      const container = document.querySelector('.code-editor-container');
      if (!container) return;
      
      const rect = container.getBoundingClientRect();
      const newWidth = e.clientX - rect.left;
      
      // Constrain between 200px and 600px
      const constrainedWidth = Math.max(200, Math.min(600, newWidth));
      setFilesWidth(constrainedWidth);
    };

    const handleMouseUp = () => {
      setIsResizingFiles(false);
    };

    if (isResizingFiles) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizingFiles]);

  const getLanguageFromPath = (filePath: string): string => {
    const ext = filePath.split('.').pop()?.toLowerCase();
    const langMap: Record<string, string> = {
      js: 'javascript',
      jsx: 'javascript',
      ts: 'typescript',
      tsx: 'typescript',
      py: 'python',
      java: 'java',
      cpp: 'cpp',
      c: 'c',
      cs: 'csharp',
      go: 'go',
      rs: 'rust',
      php: 'php',
      rb: 'ruby',
      swift: 'swift',
      kt: 'kotlin',
      r: 'r',
      sql: 'sql',
      sh: 'shell',
      bash: 'shell',
      pl: 'perl',
      lua: 'lua',
      dart: 'dart',
      scala: 'scala',
      hs: 'haskell',
      groovy: 'groovy',
      pas: 'pascal',
      md: 'markdown',
      json: 'json',
      xml: 'xml',
      yaml: 'yaml',
      yml: 'yaml',
      html: 'html',
      css: 'css',
      scss: 'scss',
      lock: 'yaml',
      cmake: 'cmake',
    };
    return langMap[ext || ''] || 'plaintext';
  };

  const handleCodeChange = (filePath: string, value: string | undefined) => {
    if (value !== undefined) {
      setFileContents((prev) => ({
        ...prev,
        [filePath]: value,
      }));
    }
  };

  const handleReset = () => {
    if (prData) {
      const resetContents: FileEditorState = {};
      prData.file_changes.forEach((fileChange) => {
        resetContents[fileChange.file_path] = fileChange.before_code;
      });
      setFileContents(resetContents);
      setSubmissionStatus('idle');
    }
  };

  const handleDownload = () => {
    if (!selectedFile) return;

    const code = fileContents[selectedFile];
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = selectedFile.split('/').pop() || 'code.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const handleSubmitCode = async () => {
    setIsSubmitting(true);
    setSubmissionStatus('submitting');

    try {
      const submissionData = {
        pr_number: prData?.pr_number,
        file_changes: Object.entries(fileContents).map(([filePath, code]) => ({
          file_path: filePath,
          submitted_code: code,
        })),
        timestamp: new Date().toISOString(),
      };

      const response = await fetch('/api/onboarding/bugFix/challenges', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submissionData),
      });

      const result = await response.json();

      if (result.success) {
        setSubmissionStatus('evaluating');
        setIsEvaluating(true);

        // Call the evaluation API
        if (result.submission_id && prData?.pr_number) {
          setTimeout(async () => {
            try {
              const evalResponse = await fetch(`${baseURL}/evaluate-submission`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                  submission_id: result.submission_id,
                  pr_number: prData.pr_number,
                }),
              });

              const evalResult = await evalResponse.json();

              if (evalResponse.ok) {
                setSubmissionStatus('complete');
                setIsEvaluating(false);
                setIsSubmitting(false);
                
                // Pass evaluation to parent component
                if (onEvaluationComplete) {
                  onEvaluationComplete(evalResult);
                }
              } else {
                throw new Error(evalResult.detail || 'Evaluation failed');
              }
            } catch (evalError) {
              console.error('Evaluation error:', evalError);
              setSubmissionStatus('idle');
              setIsEvaluating(false);
              setIsSubmitting(false);
              alert(`Evaluation failed: ${evalError instanceof Error ? evalError.message : 'Unknown error'}`);
            }
          }, 1000);
        }
      } else {
        throw new Error(result.message || 'Submission failed');
      }
    } catch (error) {
      console.error('Submission error:', error);
      setSubmissionStatus('idle');
      setIsSubmitting(false);
      alert(`Submission failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const getFileIcon = (filePath: string) => {
    const ext = filePath.split('.').pop()?.toLowerCase();
    if (['js', 'jsx', 'ts', 'tsx'].includes(ext || '')) return '📜';
    if (['py'].includes(ext || '')) return '🐍';
    if (['java'].includes(ext || '')) return '☕';
    if (['dart'].includes(ext || '')) return '🎯';
    if (['cpp', 'c'].includes(ext || '')) return '⚙️';
    if (['lock', 'json', 'yaml'].includes(ext || '')) return '📦';
    if (['cmake'].includes(ext || '')) return '🔧';
    return '📄';
  };

  const getChangeTypeColor = (changeType: string) => {
    switch (changeType) {
      case 'modified': return 'text-yellow-700 bg-yellow-50 border-yellow-200';
      case 'added': return 'text-green-700 bg-green-50 border-green-200';
      case 'removed': return 'text-red-700 bg-red-50 border-red-200';
      default: return 'text-gray-700 bg-gray-50 border-gray-200';
    }
  };

  if (!prData || prData.file_changes.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 h-full overflow-hidden shadow-sm flex items-center justify-center bg-white">
        <div className="flex flex-col items-center justify-center py-16 px-8">
          <FileCode className="w-16 h-16 mb-4 text-gray-400" />
          <p className="font-medium text-center text-lg text-gray-700">
            No PR data available
          </p>
          <p className="text-sm text-center mt-2 text-gray-500">
            Select a challenge to see the code editor
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 overflow-hidden shadow-sm h-full flex flex-col bg-white">
      {/* Header */}
      <div className="px-6 py-4 border-b flex-shrink-0 bg-gray-900 border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-gray-800 flex items-center justify-center">
              <FileCode className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Code Editor</h3>
              <p className="text-xs text-gray-400">PR #{prData.pr_number}</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {onToggleFullscreen && (
              <button
                onClick={onToggleFullscreen}
                className="px-3 py-2 rounded-lg text-white text-sm font-medium transition-all flex items-center space-x-2 bg-gray-700 hover:bg-gray-600"
                title={isFullscreen ? 'Collapse Width Horizontally' : 'Expand Width Horizontally'}
              >
                {isFullscreen ? <ChevronsLeftRight className="w-4 h-4" /> : <MoveHorizontal className="w-4 h-4" />}
              </button>
            )}
            
            <button
              onClick={handleReset}
              disabled={isSubmitting}
              className={`px-3 py-2 rounded-lg text-white text-sm font-medium transition-all flex items-center space-x-2 ${
                isSubmitting 
                  ? 'opacity-50 cursor-not-allowed bg-gray-700'
                  : 'bg-gray-700 hover:bg-gray-600'
              }`}
              title="Reset Code"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Reset</span>
            </button>

            <button
              onClick={handleDownload}
              disabled={!selectedFile || isSubmitting}
              className={`px-3 py-2 rounded-lg text-white text-sm font-medium transition-all flex items-center space-x-2 ${
                !selectedFile || isSubmitting ? 'opacity-50 cursor-not-allowed bg-gray-700' :
                'bg-gray-700 hover:bg-gray-600'
              }`}
              title="Download File"
            >
              <Download className="w-4 h-4" />
              <span>Download</span>
            </button>
          </div>
        </div>
      </div>

      {/* Editor Area */}
      <div className="flex flex-1 min-h-0 code-editor-container">
        {/* File Sidebar */}
        <div 
          className={`${showFileList ? '' : 'w-12'} border-r overflow-hidden flex-shrink-0 transition-all duration-300 border-gray-200 bg-gray-50`}
          style={showFileList ? { width: `${filesWidth}px` } : {}}
        >
          <div
            className="px-4 py-3 border-b cursor-pointer flex items-center justify-between sticky top-0 z-10 border-gray-200 bg-gray-50"
            onClick={() => setShowFileList(!showFileList)}
          >
            <div className={`flex items-center space-x-2 ${showFileList ? '' : 'opacity-0 w-0 overflow-hidden'}`}>
              <span className="font-semibold text-sm text-gray-900">
                Files
              </span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-gray-200 text-gray-700">
                {prData.file_changes.length}
              </span>
            </div>
            <div className="flex-shrink-0">
              {showFileList ? (
                <ChevronLeft className="w-4 h-4 text-gray-600" />
              ) : (
                <ChevronRight className="w-4 h-4 text-gray-600" />
              )}
            </div>
          </div>

          {showFileList && (
            <div className="py-1 overflow-y-auto h-[calc(100%-60px)]">
              {prData.file_changes.map((fileChange) => (
                <button
                  key={fileChange.file_path}
                  onClick={() => setSelectedFile(fileChange.file_path)}
                  className={`w-full px-4 py-3 text-left transition-all border-b ${
                    selectedFile === fileChange.file_path
                      ? 'bg-gray-100 border-gray-300'
                      : 'hover:bg-gray-100 border-gray-100'
                  }`}
                >
                  <div className="flex items-start space-x-2">
                    <span className="text-lg mt-0.5">{getFileIcon(fileChange.file_path)}</span>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold truncate text-sm mb-1 text-gray-900">
                        {fileChange.file_path.split('/').pop()}
                      </p>
                      <p className="text-xs truncate mb-1.5 text-gray-600">
                        {fileChange.file_path}
                      </p>
                      <div className="flex items-center space-x-2">
                        <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${getChangeTypeColor(fileChange.change_type)}`}>
                          {fileChange.change_type}
                        </span>
                        <span className="text-xs font-mono text-green-500">
                          +{fileChange.statistics.lines_added}
                        </span>
                        <span className="text-xs font-mono text-red-500">
                          -{fileChange.statistics.lines_deleted}
                        </span>
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Files Resizer */}
        {showFileList && (
          <div
            onMouseDown={(e) => {
              e.preventDefault();
              setIsResizingFiles(true);
            }}
            className={`w-1 cursor-col-resize hover:bg-gray-400 transition-colors flex-shrink-0 ${
              isResizingFiles ? 'bg-gray-400' : 'bg-gray-300'
            }`}
            style={{ width: '4px' }}
          >
            <div className="w-full h-full" />
          </div>
        )}

        {/* Editor */}
        <div className="flex-1 flex flex-col min-w-0">
          {selectedFile ? (
            <>
              <div className="px-4 py-2.5 border-b flex items-center justify-between flex-shrink-0 bg-gray-50 border-gray-200">
                <div className="flex items-center space-x-2">
                  <span className="text-base">{getFileIcon(selectedFile)}</span>
                  <span className="font-medium text-sm text-gray-900">
                    {selectedFile}
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded bg-gray-200 text-gray-700">
                    {getLanguageFromPath(selectedFile)}
                  </span>
                </div>
              </div>

              <div className="flex-1 min-h-0">
                <Editor
                  height="100%"
                  language={getLanguageFromPath(selectedFile)}
                  value={fileContents[selectedFile] || ''}
                  onChange={(value) => handleCodeChange(selectedFile, value)}
                  theme="vs-light"
                  options={{
                    minimap: { enabled: true },
                    fontSize: 14,
                    lineNumbers: 'on',
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    tabSize: 2,
                    wordWrap: 'on',
                    padding: { top: 16, bottom: 16 },
                    lineHeight: 22,
                    fontFamily: "'Fira Code', 'Consolas', 'Monaco', monospace",
                    readOnly: isSubmitting,
                  }}
                />
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <FileCode className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                <p className="font-medium text-sm text-gray-600">
                  Select a file to edit
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Submit Button and Status */}
      <div className="px-6 py-3 border-t flex-shrink-0 bg-gray-50 border-gray-200">
        {submissionStatus === 'idle' || submissionStatus === 'complete' ? (
          <button
            onClick={handleSubmitCode}
            disabled={isSubmitting}
            className={`w-full px-6 py-3 rounded-lg font-semibold flex items-center justify-center space-x-2 transition-all ${
              isSubmitting
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-gray-900 text-white hover:bg-gray-800'
            }`}
          >
            <CheckCircle className="w-5 h-5" />
            <span>Submit Solution</span>
          </button>
        ) : (
          <div className={`w-full px-6 py-3 rounded-lg border flex items-center justify-center space-x-3 ${
            submissionStatus === 'submitting'
              ? 'bg-blue-50 border-blue-200'
              : 'bg-gray-50 border-gray-200'
          }`}>
            {submissionStatus === 'submitting' ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                <span className="font-medium text-blue-600">
                  Submitting your code...
                </span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5 animate-pulse text-gray-600" />
                <span className="font-medium text-gray-600">
                  Evaluating your submission...
                </span>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
