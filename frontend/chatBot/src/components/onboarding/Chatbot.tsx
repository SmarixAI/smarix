'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Maximize2, Minimize2, X } from 'lucide-react';
import { useAuth } from '@/components/auth/AuthContext';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatbotProps {
  role?: 'onboarding' | 'offboarding' | 'general'; // Role for context-aware responses
}

export default function Chatbot({ role = 'onboarding' }: ChatbotProps) {
  const { user } = useAuth();
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

  const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
      const requestBody: { query: string; session_id?: string; role?: string; username?: string } = {
        query: currentInput,
        role: role,
      };

      if (sessionId) {
        requestBody.session_id = sessionId;
      }

      if (user?.username) {
        requestBody.username = user.username;
      }

      const response = await fetch(`${baseURL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        let errorMessage = 'Failed to get response';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch (e) {
          // If response is not JSON, use status text
          errorMessage = response.statusText || errorMessage;
        }
        throw new Error(errorMessage);
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
      let errorContent = 'Sorry, I encountered an error. Please make sure the backend is running and try again.';
      
      // Show the actual error message from the backend if available
      if (error instanceof Error) {
        const errorMsg = error.message;
        if (errorMsg.includes('Chatbot not initialized')) {
          errorContent = `Chatbot Error: ${errorMsg}. Please check the backend logs or contact an administrator.`;
        } else if (errorMsg && errorMsg !== 'Failed to get response') {
          errorContent = `Error: ${errorMsg}`;
        }
      }
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: errorContent,
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
        className="fixed bottom-6 right-6 z-50 p-4 rounded-full bg-gray-800 text-white shadow-2xl transition-all hover:scale-110 hover:bg-gray-700"
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
          background: #f1f5f9;
          border-radius: 10px;
        }
        .chatbot-messages::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 10px;
        }
        .chatbot-messages::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
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
            ? 'fixed inset-0 z-[100] rounded-none bg-white'
            : 'fixed bottom-6 right-6 z-50 w-96 h-[600px] rounded-2xl bg-white'
        } shadow-2xl border border-gray-200 flex flex-row overflow-hidden`}
      >
        {/* Chat History Sidebar - Only in fullscreen */}
        {isFullscreen && (
          <div className="w-80 border-r border-gray-100 flex flex-col flex-shrink-0 bg-white">
            <div className="px-4 py-3 border-b border-gray-100 bg-white">
              <h4 className="font-semibold text-sm text-gray-900">
                Chat History
              </h4>
              <p className="text-xs mt-1 text-gray-500">
                {messages.length} {messages.length === 1 ? 'message' : 'messages'}
              </p>
            </div>
            <div
              className="flex-1 overflow-y-auto bg-white"
              style={{
                scrollbarWidth: 'thin',
                scrollbarColor: '#cbd5e1 #f1f5f9',
              }}
            >
              {messages.map((message, index) => (
                <button
                  key={message.id}
                  onClick={() => scrollToMessage(message.id)}
                  className={`w-full text-left px-4 py-3 border-b border-gray-200 transition-colors ${
                    selectedMessageId === message.id
                      ? 'bg-blue-50 border-blue-300'
                      : 'hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-start space-x-2">
                    <div
                      className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                        message.role === 'user'
                          ? 'bg-gray-700'
                          : 'bg-gray-600'
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
                              ? 'text-gray-700'
                              : 'text-gray-600'
                          }`}
                        >
                          {message.role === 'user' ? 'You' : 'Assistant'}
                        </span>
                        <span className="text-xs text-gray-500">
                          {message.timestamp.toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                      <p className="text-xs line-clamp-2 text-gray-700">
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
      <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between flex-shrink-0 bg-white">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-gray-800">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className={`font-semibold ${isFullscreen ? 'text-base' : 'text-sm'} text-gray-900`}>
              {role === 'onboarding' 
                ? 'Onboarding Assistant'
                : role === 'offboarding'
                ? 'Offboarding Assistant'
                : 'AI Assistant'}
            </h3>
            <p className="text-xs text-gray-500">
              Always here to help
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-2 rounded-lg transition-colors hover:bg-gray-100 text-gray-700"
            aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
            title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
          >
            {isFullscreen ? (
              <Minimize2 className="w-5 h-5" />
            ) : (
              <Maximize2 className="w-5 h-5" />
            )}
          </button>
          <button
            onClick={() => {
              setIsOpen(false);
              setIsFullscreen(false);
            }}
            className="p-2 rounded-lg transition-colors hover:bg-red-100 hover:text-red-600 text-gray-700"
            aria-label="Close chatbot"
            title="Close chatbot"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div
        className={`flex-1 overflow-y-auto ${isFullscreen ? 'px-8 py-6' : 'px-4 py-4'} space-y-4 chatbot-messages bg-white`}
        style={{
          scrollbarWidth: 'thin',
          scrollbarColor: '#cbd5e1 #f1f5f9',
        }}
      >
            {messages.map((message) => (
              <div
                key={message.id}
                ref={(el) => {
                  messageRefs.current[message.id] = el;
                }}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} transition-all duration-300 ${
                  selectedMessageId === message.id
                    ? 'bg-blue-50 rounded-lg px-2 py-1 -mx-2 -my-1'
                    : ''
                }`}
              >
                <div
                  className={`flex items-start space-x-2 ${isFullscreen ? 'max-w-[75%]' : 'max-w-[80%]'} ${
                    message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      message.role === 'user'
                        ? 'bg-gray-700'
                        : 'bg-gray-600'
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
                        ? 'bg-gray-700 text-white'
                        : 'bg-gray-50 text-gray-900 border border-gray-200'
                    }`}
                  >
                    <p className={`${isFullscreen ? 'text-base' : 'text-sm'} whitespace-pre-wrap break-words leading-relaxed`}>{message.content}</p>
                    <p
                      className={`text-xs mt-1.5 ${
                        message.role === 'user'
                          ? 'text-gray-300'
                          : 'text-gray-500'
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
                <div className={`flex items-start space-x-2 ${isFullscreen ? 'max-w-[75%]' : 'max-w-[80%]'}`}>
                  <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-gray-600">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                  <div className="rounded-2xl px-4 py-2.5 bg-gray-50 text-gray-900 border border-gray-200">
                    <div className="flex space-x-1.5">
                      <div
                        className="w-2 h-2 rounded-full animate-bounce bg-gray-400"
                        style={{ animationDelay: '0ms' }}
                      />
                      <div
                        className="w-2 h-2 rounded-full animate-bounce bg-gray-400"
                        style={{ animationDelay: '150ms' }}
                      />
                      <div
                        className="w-2 h-2 rounded-full animate-bounce bg-gray-400"
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
        className={`${isFullscreen ? 'px-8 py-4' : 'px-4 py-3'} border-t border-gray-100 flex items-center space-x-2 flex-shrink-0 bg-white`}
      >
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={isFullscreen ? "Ask me anything about onboarding... (Press Enter to send)" : "Ask me anything about onboarding..."}
          className={`flex-1 ${isFullscreen ? 'px-4 py-3 text-base' : 'px-3 py-2 text-sm'} rounded-lg outline-none transition-colors bg-white text-gray-900 placeholder-gray-500 border border-gray-300 focus:border-gray-500 focus:ring-1 focus:ring-gray-500`}
          disabled={isTyping}
        />
        <button
          onClick={handleSend}
          disabled={!inputValue.trim() || isTyping}
          className={`${isFullscreen ? 'p-3' : 'p-2'} rounded-lg transition-all ${
            !inputValue.trim() || isTyping
              ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
              : 'bg-gray-800 hover:bg-gray-700 text-white'
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

