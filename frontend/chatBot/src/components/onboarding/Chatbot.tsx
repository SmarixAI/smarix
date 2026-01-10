'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Maximize2, Minimize2, X, Clock, MessageSquarePlus, Trash2, History, MessageSquare, ChevronDown, Loader2 } from 'lucide-react';
import { useAuth } from '@/components/auth/AuthContext';
import { Fira_Code, Space_Grotesk } from 'next/font/google';
import { motion, AnimatePresence } from 'framer-motion';
import Image from 'next/image';

const firaCode = Fira_Code({ subsets: ['latin'] });
const spaceGrotesk = Space_Grotesk({ subsets: ['latin'] });

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
  const [sessions, setSessions] = useState<any[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [sidebarView, setSidebarView] = useState<'sessions' | 'messages'>('sessions');
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

  const loadSessions = async () => {
    try {
      const response = await fetch(`${baseURL}/sessions`);
      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error("Failed to load sessions:", error);
    }
  };

  const loadSession = async (sessionIdToLoad: string) => {
    try {
      const response = await fetch(`${baseURL}/load-session/${sessionIdToLoad}`);
      const data = await response.json();

      const formattedMessages = (data.messages || []).map((msg: any, index: number) => ({
        id: msg.id?.toString() || `msg-${index}-${sessionIdToLoad.slice(-4)}-${Date.now()}`,
        role: (msg.role as 'user' | 'assistant') || 'assistant',
        content: msg.content || 'No content available',
        timestamp: new Date(msg.created_at || Date.now()),
      }));

      setMessages(formattedMessages);
      setSessionId(data.session_id);
      setSelectedSessionId(data.session_id);
      await loadSessions();
    } catch (error) {
      console.error("Failed to load session:", error);
      setMessages([]);
      setSessionId(sessionIdToLoad);
      setSelectedSessionId(sessionIdToLoad);
    }
  };

  const createNewSession = async () => {
    try {
      const response = await fetch(`${baseURL}/new-session`, { method: 'POST' });
      const data = await response.json();

      setSessionId(data.session_id);
      setSelectedSessionId(data.session_id);
      setMessages([
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

      await loadSessions();
    } catch (error) {
      console.error("Failed to create new session:", error);
    }
  };

  const deleteSession = async (sessionIdToDelete: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm("Delete this chat session?")) {
      try {
        await fetch(`${baseURL}/delete-session/${sessionIdToDelete}`, { method: 'DELETE' });
        await loadSessions();
        if (selectedSessionId === sessionIdToDelete) {
          setSessionId(null);
          setSelectedSessionId(null);
          setMessages([
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
        }
      } catch (error) {
        console.error("Failed to delete session:", error);
        alert("Failed to delete session");
      }
    }
  };

  useEffect(() => {
    if (isOpen && isFullscreen) {
      loadSessions();
    }
  }, [isOpen, isFullscreen]);

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
        setSelectedSessionId(data.conversation_id);
        await loadSessions();
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
      <motion.button
        onClick={() => setIsOpen(true)}
        whileHover={{ scale: 1.05, y: -2 }}
        whileTap={{ scale: 0.95 }}
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        className="fixed bottom-6 right-6 z-50 p-4 rounded-2xl bg-[#0E1B2E] text-white shadow-2xl shadow-[#0E1B2E]/30 transition-all hover:bg-[#1a2f4d] border border-white/10 backdrop-blur-sm group"
        aria-label="Open chatbot"
      >
        <div className="flex items-center gap-3">
          <div className="relative">
            <Bot className="w-6 h-6 transition-transform group-hover:scale-110" />
          </div>
          {messages.length > 1 && (
            <span className={`${firaCode.className} text-xs bg-white/20 px-2 py-1 rounded-lg backdrop-blur-sm`}>
              {messages.length - 1}
            </span>
          )}
        </div>
      </motion.button>
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
          background: transparent;
          border-radius: 10px;
        }
        .chatbot-messages::-webkit-scrollbar-thumb {
          background: #0E1B2E15;
          border-radius: 10px;
        }
        .chatbot-messages::-webkit-scrollbar-thumb:hover {
          background: #0E1B2E25;
        }
        .line-clamp-2 {
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
      `}</style>
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        transition={{ duration: 0.2 }}
        className={`transition-all duration-300 ${
          isFullscreen
            ? 'fixed inset-0 z-[100] rounded-none bg-[#FAFAFA]'
            : 'fixed bottom-6 right-6 z-50 w-96 h-[600px] rounded-2xl bg-[#FAFAFA]'
        } shadow-2xl shadow-[#0E1B2E]/10 border border-[#0E1B2E]/10 flex flex-row overflow-hidden backdrop-blur-xl`}
      >
          {/* Sidebar - Only in fullscreen */}
        {isFullscreen && (
          <div className="w-80 border-r border-[#0E1B2E]/10 bg-white/35 backdrop-blur-xl flex flex-col flex-shrink-0 shadow-sm relative z-10">
            <div className="flex flex-col h-full w-80">
              {/* Header */}
              <div className="p-4 border-b border-[#0E1B2E]/10 flex-shrink-0 bg-white/30 backdrop-blur-sm">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-[#0E1B2E] rounded-lg flex items-center justify-center overflow-hidden">
                    <Image
                      src="/logo.png"
                      alt="Smarix Logo"
                      width={24}
                      height={24}
                      className="w-6 h-6 object-contain"
                    />
                  </div>
                  <span className={`${spaceGrotesk.className} font-bold text-lg text-[#0E1B2E]`}>Smarix</span>
                </div>

                {/* New Chat Button */}
                <button
                  onClick={createNewSession}
                  className="w-full p-3 bg-[#0E1B2E] hover:bg-[#1a2f4d] text-white rounded-lg transition-all flex items-center justify-center gap-2 group hover:scale-[1.02] active:scale-[0.98] shadow-md hover:shadow-lg hover:shadow-[#0E1B2E]/20"
                >
                  <MessageSquarePlus className="w-5 h-5 group-hover:rotate-12 transition-transform" />
                  <span className={`text-sm font-medium ${spaceGrotesk.className}`}>New Chat</span>
                </button>
              </div>

              {/* Sidebar View Toggle */}
              <div className="px-3 pt-3 pb-2 border-b border-[#0E1B2E]/10 bg-white/20 flex-shrink-0">
                <div className="relative">
                  <button
                    onClick={() => setSidebarView(sidebarView === 'sessions' ? 'messages' : 'sessions')}
                    className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-white/60 backdrop-blur-sm transition-colors group"
                  >
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-[#0E1B2E]" />
                      <span className={`text-xs font-semibold text-[#0E1B2E] ${spaceGrotesk.className}`}>
                        {sidebarView === 'sessions' ? 'Recent Chats' : 'Chat History'}
                      </span>
                      {sidebarView === 'sessions' && messages.length > 0 && (
                        <span className={`${firaCode.className} text-[10px] bg-[#0E1B2E]/10 text-[#0E1B2E] px-1.5 py-0.5 rounded`}>
                          {messages.length}
                        </span>
                      )}
                    </div>
                    <ChevronDown className={`w-4 h-4 text-[#0E1B2E]/60 transition-transform ${sidebarView === 'messages' ? 'rotate-180' : ''}`} />
                  </button>
                </div>
              </div>

              {/* Sessions List */}
              <div className="flex-1 overflow-y-auto p-3 bg-white/10">
                {sidebarView === 'sessions' && (
                  <>
                    <div className="mb-2 flex items-center justify-between px-2">
                      <span className={`text-xs font-semibold text-[#0E1B2E]/70 uppercase tracking-wider ${spaceGrotesk.className}`}>
                        Recent Chats
                      </span>
                      <Clock className="w-3.5 h-3.5 text-[#0E1B2E]/50" />
                    </div>
                    <AnimatePresence>
                      {sessions.map((session: any) => (
                        <motion.div
                          key={session.session_id}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: 20 }}
                          onClick={() => loadSession(session.session_id)}
                          className={`p-3 cursor-pointer rounded-lg transition-all mb-2 group relative ${
                            selectedSessionId === session.session_id
                              ? 'bg-[#0E1B2E] text-white border border-[#0E1B2E] shadow-lg'
                              : 'hover:bg-white/35 backdrop-blur-sm border border-transparent hover:border-[#0E1B2E]/20 bg-white/25'
                          }`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <div className={`text-sm font-medium truncate mb-1 ${selectedSessionId === session.session_id ? 'text-white' : 'text-[#0E1B2E]'} ${spaceGrotesk.className}`}>
                                {session.title}
                              </div>
                              <div className={`flex items-center gap-2 text-xs ${selectedSessionId === session.session_id ? 'text-white/70' : 'text-[#0E1B2E]/60'}`}>
                                <span className="flex items-center gap-1">
                                  <MessageSquarePlus className="w-3 h-3" />
                                  {session.message_count}
                                </span>
                                <span>•</span>
                                <span className={`${firaCode.className} text-[10px]`}>
                                  {new Date(session.last_message).toLocaleDateString()}
                                </span>
                              </div>
                            </div>
                            <button
                              onClick={(e) => deleteSession(session.session_id, e)}
                              className={`p-1.5 opacity-0 group-hover:opacity-100 hover:bg-red-100 rounded transition-all flex-shrink-0 ${
                                selectedSessionId === session.session_id ? 'text-red-300 hover:text-red-200' : 'text-red-500 hover:text-red-600'
                              }`}
                              title="Delete chat"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </motion.div>
                      ))}
                    </AnimatePresence>

                    {sessions.length === 0 && (
                      <div className={`text-center text-xs text-[#0E1B2E]/60 py-8 ${spaceGrotesk.className}`}>
                        No conversations yet
                        <div className="text-[10px] mt-1 text-[#0E1B2E]/40">
                          Start chatting to see history
                        </div>
                      </div>
                    )}
                  </>
                )}

                {/* Chat History View */}
                {sidebarView === 'messages' && (
                  <>
                    <div className="mb-2 flex items-center justify-between px-2">
                      <span className={`text-xs font-semibold text-[#0E1B2E]/70 uppercase tracking-wider ${spaceGrotesk.className}`}>
                        Current Chat
                      </span>
                      <MessageSquare className="w-3.5 h-3.5 text-[#0E1B2E]/50" />
                    </div>
                    <div className="px-2 mb-2">
                      <p className={`${firaCode.className} text-xs text-[#0E1B2E]/60`}>
                {messages.length} {messages.length === 1 ? 'message' : 'messages'}
              </p>
            </div>
                    <div className="space-y-1">
                      {messages.map((message) => (
                <motion.button
                  key={message.id}
                  onClick={() => scrollToMessage(message.id)}
                  whileHover={{ x: 2 }}
                          className={`w-full text-left px-3 py-2 rounded-lg transition-colors mb-1 ${
                    selectedMessageId === message.id
                              ? 'bg-[#0E1B2E] text-white border border-[#0E1B2E] shadow-lg'
                              : 'hover:bg-white/35 backdrop-blur-sm border border-transparent hover:border-[#0E1B2E]/20 bg-white/25'
                  }`}
                >
                          <div className="flex items-start space-x-2">
                    <div
                              className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                        message.role === 'user'
                                  ? selectedMessageId === message.id
                                    ? 'bg-white/20'
                                    : 'bg-[#0E1B2E]'
                                  : selectedMessageId === message.id
                                  ? 'bg-white/20'
                          : 'bg-[#0E1B2E]/80'
                      }`}
                    >
                      {message.role === 'user' ? (
                                <User className="w-3 h-3 text-white" />
                      ) : (
                                <Bot className="w-3 h-3 text-white" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between mb-0.5">
                        <span
                          className={`${spaceGrotesk.className} text-xs font-medium ${
                                    selectedMessageId === message.id
                                      ? 'text-white'
                                      : message.role === 'user'
                              ? 'text-[#0E1B2E]'
                              : 'text-[#0E1B2E]/80'
                          }`}
                        >
                          {message.role === 'user' ? 'You' : 'Assistant'}
                        </span>
                                <span
                                  className={`${firaCode.className} text-[10px] ${
                                    selectedMessageId === message.id
                                      ? 'text-white/70'
                                      : 'text-[#0E1B2E]/50'
                                  }`}
                                >
                          {message.timestamp.toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                              <p
                                className={`${spaceGrotesk.className} text-xs line-clamp-2 ${
                                  selectedMessageId === message.id
                                    ? 'text-white/90'
                                    : 'text-[#0E1B2E]/70'
                                }`}
                              >
                        {getMessagePreview(message.content)}
                      </p>
                    </div>
                  </div>
                </motion.button>
              ))}
                    </div>
                    {messages.length === 0 && (
                      <div className={`text-center text-xs text-[#0E1B2E]/60 py-8 ${spaceGrotesk.className}`}>
                        No messages yet
                        <div className="text-[10px] mt-1 text-[#0E1B2E]/40">
                          Start chatting to see message history
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Main Chat Area */}
        <div className="flex flex-col flex-1 min-w-0 relative">
          {/* Grid Pattern Background - Matching landing page - only show in fullscreen */}
          {isFullscreen && (
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
          )}
          
          {/* Header */}
          <div className={`${isFullscreen ? 'px-8 py-4' : 'px-5 py-3.5'} border-b ${isFullscreen ? 'border-[#0E1B2E]/10' : 'border-gray-200/50'} flex items-center justify-between flex-shrink-0 ${isFullscreen ? 'bg-white/35 backdrop-blur-xl' : 'bg-white/80 backdrop-blur-xl'} relative z-10 ${isFullscreen ? 'shadow-sm shadow-black/5' : ''}`}>
                {isFullscreen ? (
              <div>
                <h3 className={`${spaceGrotesk.className} font-bold text-xl text-[#0E1B2E]`}>
                  {role === 'onboarding' 
                    ? 'Onboarding Assistant'
                    : role === 'offboarding'
                    ? 'Offboarding Assistant'
                    : 'AI Assistant'}
                </h3>
                <p className={`${firaCode.className} text-sm text-[#0E1B2E]/70 mt-1 ${spaceGrotesk.className}`}>
                  {role === 'onboarding'
                    ? 'Ask anything about onboarding, tech stack, development setup, or repository'
                    : role === 'offboarding'
                    ? 'Ask about knowledge transfer, documentation, handover tasks, and transitions'
                    : 'Ask anything about your code, flows, issues, and PRs'}
                </p>
              </div>
            ) : (
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-[#0E1B2E] shadow-lg shadow-[#0E1B2E]/10">
                  <Image src="/logo.png" alt="Logo" width={20} height={20} className="object-contain" />
                </div>
                <div>
                  <h3 className={`${spaceGrotesk.className} font-semibold text-sm text-[#0E1B2E]`}>
                  {role === 'onboarding' 
                    ? 'Onboarding Assistant'
                    : role === 'offboarding'
                    ? 'Offboarding Assistant'
                    : 'AI Assistant'}
                </h3>
                <p className={`${firaCode.className} text-xs text-[#0E1B2E]/60`}>
                  Always here to help
                </p>
              </div>
            </div>
            )}
            <div className="flex items-center space-x-2">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setIsFullscreen(!isFullscreen)}
                className="p-2 rounded-lg transition-colors hover:bg-[#0E1B2E]/5 text-[#0E1B2E]/70 hover:text-[#0E1B2E]"
                aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
                title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
              >
                {isFullscreen ? (
                  <Minimize2 className="w-5 h-5" />
                ) : (
                  <Maximize2 className="w-5 h-5" />
                )}
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => {
                  setIsOpen(false);
                  setIsFullscreen(false);
                }}
                className="p-2 rounded-lg transition-colors hover:bg-red-50 hover:text-red-600 text-[#0E1B2E]/70"
                aria-label="Close chatbot"
                title="Close chatbot"
              >
                <X className="w-5 h-5" />
              </motion.button>
            </div>
          </div>

          {/* Messages */}
          <div
            className={`flex-1 overflow-y-auto ${isFullscreen ? 'px-12 py-8' : 'px-5 py-5'} ${isFullscreen ? 'space-y-6' : 'space-y-4'} chatbot-messages relative z-10`}
            style={{
              scrollbarWidth: 'thin',
              scrollbarColor: '#0E1B2E15 transparent',
            }}
          >
            {messages.map((message) => (
              <motion.div
                key={message.id}
                ref={(el) => {
                  messageRefs.current[message.id] = el;
                }}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} transition-all duration-300 ${
                  selectedMessageId === message.id
                    ? 'bg-[#0E1B2E]/5 rounded-lg px-2 py-1 -mx-2 -my-1'
                    : ''
                }`}
              >
                <div
                  className={`flex items-start space-x-3 ${isFullscreen ? 'max-w-[70%]' : 'max-w-[80%]'} ${
                    message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                  }`}
                >
                  <div
                    className={`${isFullscreen ? 'w-9 h-9' : 'w-8 h-8'} rounded-full flex items-center justify-center flex-shrink-0 ${
                      message.role === 'user'
                        ? 'bg-[#0E1B2E] shadow-lg shadow-[#0E1B2E]/10'
                        : 'bg-[#0E1B2E]/80 shadow-lg shadow-[#0E1B2E]/5'
                    }`}
                  >
                    {message.role === 'user' ? (
                      <User className="w-4 h-4 text-white" style={isFullscreen ? { width: '18px', height: '18px' } : {}} />
                    ) : (
                      <Bot className="w-4 h-4 text-white" style={isFullscreen ? { width: '18px', height: '18px' } : {}} />
                    )}
                  </div>
                  <div
                    className={`rounded-2xl ${isFullscreen ? 'px-6 py-4' : 'px-4 py-3'} ${
                      message.role === 'user'
                        ? 'bg-[#0E1B2E] text-white shadow-lg shadow-[#0E1B2E]/10'
                        : isFullscreen
                        ? 'bg-white/35 backdrop-blur-xl text-[#0E1B2E] border border-white/25 shadow-md shadow-black/5'
                        : 'bg-white/90 backdrop-blur-sm text-[#0E1B2E] border border-gray-200/50 shadow-sm'
                    }`}
                  >
                    <p className={`${spaceGrotesk.className} ${isFullscreen ? 'text-base' : 'text-sm'} whitespace-pre-wrap break-words leading-relaxed`}>{message.content}</p>
                    <p
                      className={`${firaCode.className} text-xs mt-2 ${
                        message.role === 'user'
                          ? 'text-white/60'
                          : 'text-[#0E1B2E]/50'
                      }`}
                    >
                      {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}

            {isTyping && (
              <div className="flex justify-start">
                <div className={`flex items-start space-x-3 ${isFullscreen ? 'max-w-[70%]' : 'max-w-[80%]'}`}>
                  <div className={`${isFullscreen ? 'w-9 h-9' : 'w-8 h-8'} rounded-full flex items-center justify-center flex-shrink-0 bg-[#0E1B2E]/80 shadow-lg shadow-[#0E1B2E]/5`}>
                    <Bot className="w-4 h-4 text-white" style={isFullscreen ? { width: '18px', height: '18px' } : {}} />
                  </div>
                  <div className={`rounded-2xl ${isFullscreen ? 'px-6 py-4' : 'px-4 py-3'} ${isFullscreen ? 'bg-white/35 backdrop-blur-xl text-[#0E1B2E] border border-white/25 shadow-md shadow-black/5' : 'bg-white/90 backdrop-blur-sm text-[#0E1B2E] border border-gray-200/50 shadow-sm'}`}>
                    <div className="flex space-x-2">
                      <div
                        className="w-2.5 h-2.5 rounded-full animate-bounce bg-[#0E1B2E]/40"
                        style={{ animationDelay: '0ms' }}
                      />
                      <div
                        className="w-2.5 h-2.5 rounded-full animate-bounce bg-[#0E1B2E]/40"
                        style={{ animationDelay: '150ms' }}
                      />
                      <div
                        className="w-2.5 h-2.5 rounded-full animate-bounce bg-[#0E1B2E]/40"
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
          {isFullscreen ? (
            <div
              className="px-12 py-6 border-t border-[#0E1B2E]/10 bg-white/35 backdrop-blur-xl relative z-10 shadow-sm shadow-black/5"
            >
              <div className="max-w-4xl mx-auto">
                <div className="relative">
                  <textarea
                    ref={inputRef as any}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={(e: React.KeyboardEvent<HTMLTextAreaElement>) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSend();
                      }
                    }}
                    placeholder={role === 'onboarding' 
                      ? "Ask anything about onboarding, tech stack, development setup, or repository"
                      : role === 'offboarding'
                      ? "Ask about knowledge transfer, documentation, handover tasks, and transitions"
                      : "Ask anything about your code, flows, issues, and PRs"}
                    disabled={isTyping}
                    rows={1}
                    className={`w-full px-4 py-3 pr-12 bg-white/35 backdrop-blur-xl border border-white/25 focus:border-[#0E1B2E] focus:ring-2 focus:ring-[#0E1B2E]/10 rounded-xl text-[#0E1B2E] placeholder-[#0E1B2E]/40 resize-none focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed transition-colors antialiased shadow-md shadow-black/5 ${spaceGrotesk.className}`}
                    style={{
                      minHeight: "50px",
                      maxHeight: "200px",
                      WebkitFontSmoothing: "antialiased",
                      MozOsxFontSmoothing: "grayscale",
                    }}
                  />
                  <button
                    onClick={handleSend}
                    disabled={!inputValue.trim() || isTyping}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-[#0E1B2E] hover:bg-[#1a2f4d] disabled:bg-[#0E1B2E]/30 disabled:cursor-not-allowed rounded-lg transition-all duration-300 group shadow-md hover:shadow-lg hover:shadow-[#0E1B2E]/20 flex items-center justify-center"
                  >
                    {isTyping ? (
                      <Loader2 className="w-5 h-5 text-white animate-spin" />
                    ) : (
                      <Send className="w-5 h-5 text-white group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                    )}
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div
              className="px-5 py-4 border-t border-gray-200/50 flex items-center space-x-3 flex-shrink-0 bg-white/80 backdrop-blur-xl relative z-10"
            >
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={role === 'onboarding' 
                  ? "Ask about onboarding..."
                  : role === 'offboarding'
                  ? "Ask about offboarding..."
                  : "Ask anything..."}
                className={`${spaceGrotesk.className} flex-1 px-4 py-3 text-sm rounded-xl outline-none transition-all bg-white/90 backdrop-blur-sm text-[#0E1B2E] placeholder-[#0E1B2E]/40 border border-gray-200/50 focus:border-[#0E1B2E]/30 focus:ring-2 focus:ring-[#0E1B2E]/10 shadow-sm`}
                disabled={isTyping}
              />
              <motion.button
                onClick={handleSend}
                disabled={!inputValue.trim() || isTyping}
                whileHover={!inputValue.trim() || isTyping ? {} : { scale: 1.05 }}
                whileTap={!inputValue.trim() || isTyping ? {} : { scale: 0.95 }}
                className={`p-3.5 rounded-xl transition-all shadow-lg ${
                  !inputValue.trim() || isTyping
                    ? 'bg-[#0E1B2E]/10 text-[#0E1B2E]/30 cursor-not-allowed'
                    : 'bg-[#0E1B2E] hover:bg-[#1a2f4d] text-white shadow-[#0E1B2E]/20'
                }`}
                aria-label="Send message"
              >
                <Send className="w-4.5 h-4.5" style={{ width: '18px', height: '18px' }} />
              </motion.button>
            </div>
          )}
        </div>
      </motion.div>
    </>
  );
}

