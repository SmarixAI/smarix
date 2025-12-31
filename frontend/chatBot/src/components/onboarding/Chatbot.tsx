'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Maximize2, Minimize2, X } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatbotProps {
  darkMode: boolean;
  role?: 'onboarding' | 'offboarding' | 'general'; // Role for context-aware responses
}

export default function Chatbot({ darkMode, role = 'onboarding' }: ChatbotProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: role === 'onboarding' 
        ? "Hello! I'm your onboarding assistant. I'm here to help you with any questions about the repository, tech stack, development setup, or onboarding process. Feel free to ask me anything!"
        : role === 'offboarding'
        ? "Hello! I'm your offboarding assistant. I'm here to help you with knowledge transfer, documentation, handover tasks, and ensuring a smooth transition. How can I assist you today?"
        : "Hello! I'm your AI assistant. I'm here to help you with any questions about the codebase, development, or technical matters. Feel free to ask me anything!",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const messageRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const scrollToMessage = (messageId: string) => {
    const messageElement = messageRefs.current[messageId];
    if (messageElement) {
      messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      setSelectedMessageId(messageId);
      // Remove highlight after 2 seconds
      setTimeout(() => setSelectedMessageId(null), 2000);
    }
  };

  const getMessagePreview = (content: string, maxLength: number = 60) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Prevent body scroll when fullscreen
  useEffect(() => {
    if (isFullscreen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isFullscreen]);

  // Handle ESC key to exit fullscreen
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isFullscreen) {
        setIsFullscreen(false);
      }
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [isFullscreen]);

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentInput = inputValue.trim();
    setInputValue('');
    setIsTyping(true);

    try {
      const requestBody: { query: string; session_id?: string; role?: string } = {
        query: currentInput,
        role: role,
      };

      if (sessionId) {
        requestBody.session_id = sessionId;
      }

      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();

      if (data.conversation_id && (!sessionId || sessionId !== data.conversation_id)) {
        setSessionId(data.conversation_id);
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.answer || 'Sorry, I encountered an error processing your request.',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please make sure the backend is running and try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className={`fixed bottom-6 right-6 z-50 p-4 rounded-full shadow-2xl transition-all hover:scale-110 ${
          darkMode
            ? 'bg-gradient-to-br from-blue-600 to-purple-600 text-white hover:from-blue-500 hover:to-purple-500'
            : 'bg-gradient-to-br from-indigo-600 to-cyan-600 text-white hover:from-indigo-500 hover:to-cyan-500'
        }`}
        aria-label="Open chatbot"
      >
        <Bot className="w-6 h-6" />
      </button>
    );
  }

  // Close handler
  const handleClose = () => {
    setIsOpen(false);
    setIsFullscreen(false);
  };

  return (
    <>
      <style jsx global>{`
        .chatbot-messages::-webkit-scrollbar {
          width: 6px;
        }
        .chatbot-messages::-webkit-scrollbar-track {
          background: ${darkMode ? '#1f2937' : '#f1f5f9'};
          border-radius: 10px;
        }
        .chatbot-messages::-webkit-scrollbar-thumb {
          background: ${darkMode ? '#4b5563' : '#cbd5e1'};
          border-radius: 10px;
        }
        .chatbot-messages::-webkit-scrollbar-thumb:hover {
          background: ${darkMode ? '#6b7280' : '#94a3b8'};
        }
        .line-clamp-2 {
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
      `}</style>
      <div
        className={`transition-all duration-300 ${
          isFullscreen
            ? 'fixed inset-0 z-[100] rounded-none'
            : 'fixed bottom-6 right-6 z-50 w-96 h-[600px] rounded-2xl'
        } ${darkMode ? 'glass-card-dark' : 'glass-card-light'} shadow-2xl border ${
          darkMode ? 'border-gray-700' : 'border-slate-200'
        } flex flex-row overflow-hidden`}
      >
        {/* Chat History Sidebar - Only in fullscreen */}
        {isFullscreen && (
          <div
            className={`w-80 border-r flex flex-col flex-shrink-0 ${
              darkMode ? 'border-gray-700 bg-gray-800/80' : 'border-slate-200 bg-slate-100/80'
            }`}
          >
            <div
              className={`px-4 py-3 border-b ${
                darkMode ? 'border-gray-700 bg-gray-800' : 'border-slate-200 bg-slate-200'
              }`}
            >
              <h4 className={`font-semibold text-sm ${darkMode ? 'text-white' : 'text-slate-900'}`}>
                Chat History
              </h4>
              <p className={`text-xs mt-1 ${darkMode ? 'text-gray-400' : 'text-slate-500'}`}>
                {messages.length} {messages.length === 1 ? 'message' : 'messages'}
              </p>
            </div>
            <div
              className={`flex-1 overflow-y-auto ${
                darkMode ? 'bg-gray-900/50' : 'bg-slate-50/50'
              }`}
              style={{
                scrollbarWidth: 'thin',
                scrollbarColor: darkMode ? '#4b5563 #1f2937' : '#cbd5e1 #f1f5f9',
              }}
            >
              {messages.map((message, index) => (
                <button
                  key={message.id}
                  onClick={() => scrollToMessage(message.id)}
                  className={`w-full text-left px-4 py-3 border-b transition-colors ${
                    selectedMessageId === message.id
                      ? darkMode
                        ? 'bg-blue-600/20 border-blue-500'
                        : 'bg-indigo-100 border-indigo-300'
                      : darkMode
                      ? 'border-gray-700 hover:bg-gray-800/50'
                      : 'border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  <div className="flex items-start space-x-2">
                    <div
                      className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                        message.role === 'user'
                          ? darkMode
                            ? 'bg-blue-600'
                            : 'bg-indigo-600'
                          : darkMode
                          ? 'bg-gradient-to-br from-blue-600 to-purple-600'
                          : 'bg-gradient-to-br from-indigo-600 to-cyan-600'
                      }`}
                    >
                      {message.role === 'user' ? (
                        <User className="w-3 h-3 text-white" />
                      ) : (
                        <Bot className="w-3 h-3 text-white" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <span
                          className={`text-xs font-medium ${
                            message.role === 'user'
                              ? darkMode
                                ? 'text-blue-400'
                                : 'text-indigo-600'
                              : darkMode
                              ? 'text-purple-400'
                              : 'text-cyan-600'
                          }`}
                        >
                          {message.role === 'user' ? 'You' : 'Assistant'}
                        </span>
                        <span
                          className={`text-xs ${
                            darkMode ? 'text-gray-500' : 'text-slate-500'
                          }`}
                        >
                          {message.timestamp.toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                      <p
                        className={`text-xs line-clamp-2 ${
                          darkMode ? 'text-gray-300' : 'text-slate-700'
                        }`}
                      >
                        {getMessagePreview(message.content)}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Main Chat Area */}
        <div className="flex flex-col flex-1 min-w-0">
      {/* Header */}
      <div
        className={`px-4 py-3 border-b flex items-center justify-between flex-shrink-0 ${
          darkMode ? 'border-gray-700 bg-gray-800/50' : 'border-slate-200 bg-slate-50/50'
        }`}
      >
        <div className="flex items-center space-x-3">
          <div
            className={`w-8 h-8 rounded-lg flex items-center justify-center ${
              darkMode
                ? 'bg-gradient-to-br from-blue-600 to-purple-600'
                : 'bg-gradient-to-br from-indigo-600 to-cyan-600'
            }`}
          >
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className={`font-semibold ${isFullscreen ? 'text-base' : 'text-sm'} ${darkMode ? 'text-white' : 'text-slate-900'}`}>
              {role === 'onboarding' 
                ? 'Onboarding Assistant'
                : role === 'offboarding'
                ? 'Offboarding Assistant'
                : 'AI Assistant'}
            </h3>
            <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-slate-500'}`}>
              Always here to help
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className={`p-2 rounded-lg transition-colors ${
              darkMode ? 'hover:bg-gray-700' : 'hover:bg-slate-200'
            }`}
            aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
            title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
          >
            {isFullscreen ? (
              <Minimize2 className={`w-5 h-5 ${darkMode ? 'text-gray-300' : 'text-slate-700'}`} />
            ) : (
              <Maximize2 className={`w-5 h-5 ${darkMode ? 'text-gray-300' : 'text-slate-700'}`} />
            )}
          </button>
          <button
            onClick={() => {
              setIsOpen(false);
              setIsFullscreen(false);
            }}
            className={`p-2 rounded-lg transition-colors ${
              darkMode ? 'hover:bg-red-600/20 hover:text-red-400' : 'hover:bg-red-100 hover:text-red-600'
            } ${darkMode ? 'text-gray-300' : 'text-slate-700'}`}
            aria-label="Close chatbot"
            title="Close chatbot"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div
        className={`flex-1 overflow-y-auto ${isFullscreen ? 'px-6 py-6' : 'px-4 py-4'} space-y-4 chatbot-messages ${
          darkMode ? 'bg-gray-900/50' : 'bg-slate-50/50'
        } ${isFullscreen ? 'max-w-4xl mx-auto' : ''}`}
        style={{
          scrollbarWidth: 'thin',
          scrollbarColor: darkMode ? '#4b5563 #1f2937' : '#cbd5e1 #f1f5f9',
        }}
      >
            {messages.map((message) => (
              <div
                key={message.id}
                ref={(el) => {
                  messageRefs.current[message.id] = el;
                }}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} transition-all duration-300 ${
                  isFullscreen ? 'max-w-4xl mx-auto' : ''
                } ${
                  selectedMessageId === message.id
                    ? darkMode
                      ? 'bg-blue-600/10 rounded-lg px-2 py-1 -mx-2 -my-1'
                      : 'bg-indigo-100 rounded-lg px-2 py-1 -mx-2 -my-1'
                    : ''
                }`}
              >
                <div
                  className={`flex items-start space-x-2 ${isFullscreen ? 'max-w-[85%]' : 'max-w-[80%]'} ${
                    message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      message.role === 'user'
                        ? darkMode
                          ? 'bg-blue-600'
                          : 'bg-indigo-600'
                        : darkMode
                        ? 'bg-gradient-to-br from-blue-600 to-purple-600'
                        : 'bg-gradient-to-br from-indigo-600 to-cyan-600'
                    }`}
                  >
                    {message.role === 'user' ? (
                      <User className="w-4 h-4 text-white" />
                    ) : (
                      <Bot className="w-4 h-4 text-white" />
                    )}
                  </div>
                  <div
                    className={`rounded-2xl ${isFullscreen ? 'px-5 py-3' : 'px-4 py-2.5'} ${
                      message.role === 'user'
                        ? darkMode
                          ? 'bg-blue-600 text-white'
                          : 'bg-indigo-600 text-white'
                        : darkMode
                        ? 'bg-gray-800 text-gray-100 border border-gray-700'
                        : 'bg-white text-slate-900 border border-slate-200'
                    }`}
                  >
                    <p className={`${isFullscreen ? 'text-base' : 'text-sm'} whitespace-pre-wrap break-words leading-relaxed`}>{message.content}</p>
                    <p
                      className={`text-xs mt-1.5 ${
                        message.role === 'user'
                          ? 'text-blue-100'
                          : darkMode
                          ? 'text-gray-500'
                          : 'text-slate-500'
                      }`}
                    >
                      {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex justify-start">
                <div className="flex items-start space-x-2 max-w-[80%]">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      darkMode
                        ? 'bg-gradient-to-br from-blue-600 to-purple-600'
                        : 'bg-gradient-to-br from-indigo-600 to-cyan-600'
                    }`}
                  >
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                  <div
                    className={`rounded-2xl px-4 py-2.5 ${
                      darkMode
                        ? 'bg-gray-800 text-gray-100 border border-gray-700'
                        : 'bg-white text-slate-900 border border-slate-200'
                    }`}
                  >
                    <div className="flex space-x-1.5">
                      <div
                        className={`w-2 h-2 rounded-full animate-bounce ${
                          darkMode ? 'bg-gray-400' : 'bg-slate-400'
                        }`}
                        style={{ animationDelay: '0ms' }}
                      />
                      <div
                        className={`w-2 h-2 rounded-full animate-bounce ${
                          darkMode ? 'bg-gray-400' : 'bg-slate-400'
                        }`}
                        style={{ animationDelay: '150ms' }}
                      />
                      <div
                        className={`w-2 h-2 rounded-full animate-bounce ${
                          darkMode ? 'bg-gray-400' : 'bg-slate-400'
                        }`}
                        style={{ animationDelay: '300ms' }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div
        className={`${isFullscreen ? 'px-6 py-4' : 'px-4 py-3'} border-t flex items-center space-x-2 flex-shrink-0 ${
          darkMode ? 'border-gray-700 bg-gray-800/50' : 'border-slate-200 bg-slate-50/50'
        } ${isFullscreen ? 'max-w-4xl mx-auto w-full' : ''}`}
      >
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={isFullscreen ? "Ask me anything about onboarding... (Press Enter to send)" : "Ask me anything about onboarding..."}
          className={`flex-1 ${isFullscreen ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'} rounded-lg outline-none transition-colors ${
            darkMode
              ? 'bg-gray-700 text-gray-100 placeholder-gray-500 border border-gray-600 focus:border-blue-500'
              : 'bg-white text-slate-900 placeholder-slate-500 border border-slate-300 focus:border-indigo-500'
          }`}
          disabled={isTyping}
        />
        <button
          onClick={handleSend}
          disabled={!inputValue.trim() || isTyping}
          className={`${isFullscreen ? 'p-3' : 'p-2'} rounded-lg transition-all ${
            !inputValue.trim() || isTyping
              ? darkMode
                ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                : 'bg-slate-200 text-slate-400 cursor-not-allowed'
              : darkMode
              ? 'bg-blue-600 hover:bg-blue-700 text-white'
              : 'bg-indigo-600 hover:bg-indigo-700 text-white'
          }`}
          aria-label="Send message"
        >
          <Send className={isFullscreen ? 'w-5 h-5' : 'w-4 h-4'} />
        </button>
      </div>
        </div>
      </div>
    </>
  );
}

