'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, useScroll } from 'framer-motion';
import { Navbar } from '@/components/landing/Navbar';
import { Footer } from '@/components/landing/Footer';
import { Fira_Code, Victor_Mono } from 'next/font/google';
import { 
  Search, 
  BookOpen, 
  Code2, 
  Zap, 
  Settings, 
  Users, 
  Database,
  ArrowRight,
  Copy,
  Check,
  ChevronRight,
  FileCode,
  Terminal,
  Webhook,
  Lock,
  Sparkles,
  Rocket,
  Key,
  Globe
} from 'lucide-react';

const firaCode = Fira_Code({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  display: "swap",
});

const victorMono = Victor_Mono({
  weight: ["400", "500", "700"],
  subsets: ["latin"],
  display: "swap",
});

const docSections = [
  {
    id: 'getting-started',
    title: 'Getting Started',
    icon: Rocket,
    color: '#3B82F6',
    subsections: [
      { id: 'introduction', title: 'Introduction', href: '#introduction' },
      { id: 'quick-start', title: 'Quick Start', href: '#quick-start' },
      { id: 'authentication', title: 'Authentication', href: '#authentication' },
      { id: 'installation', title: 'Installation', href: '#installation' },
    ],
  },
  {
    id: 'api-reference',
    title: 'API Reference',
    icon: Code2,
    color: '#8B5CF6',
    subsections: [
      { id: 'rest-api', title: 'REST API', href: '#rest-api' },
      { id: 'endpoints', title: 'Endpoints', href: '#endpoints' },
      { id: 'webhooks', title: 'Webhooks', href: '#webhooks' },
      { id: 'rate-limits', title: 'Rate Limits', href: '#rate-limits' },
    ],
  },
  {
    id: 'guides',
    title: 'Guides & Tutorials',
    icon: BookOpen,
    color: '#10B981',
    subsections: [
      { id: 'onboarding-setup', title: 'Onboarding Setup', href: '#onboarding-setup' },
      { id: 'offboarding-workflow', title: 'Offboarding Workflow', href: '#offboarding-workflow' },
      { id: 'webhook-integration', title: 'Webhook Integration', href: '#webhook-integration' },
      { id: 'best-practices', title: 'Best Practices', href: '#best-practices' },
    ],
  },
  {
    id: 'sdks',
    title: 'SDKs & Libraries',
    icon: FileCode,
    color: '#F59E0B',
    subsections: [
      { id: 'javascript', title: 'JavaScript/TypeScript', href: '#javascript' },
      { id: 'python', title: 'Python', href: '#python' },
      { id: 'go', title: 'Go', href: '#go' },
      { id: 'other-languages', title: 'Other Languages', href: '#other-languages' },
    ],
  },
  {
    id: 'configuration',
    title: 'Configuration',
    icon: Settings,
    color: '#EF4444',
    subsections: [
      { id: 'environment-variables', title: 'Environment Variables', href: '#environment-variables' },
      { id: 'security', title: 'Security', href: '#security' },
      { id: 'customization', title: 'Customization', href: '#customization' },
    ],
  },
];

const codeExamples = {
  quickStart: `// Install the Smarix SDK
npm install @smarix/sdk

// Initialize the client
import { Smarix } from '@smarix/sdk';

const smarix = new Smarix({
  apiKey: process.env.SMARIX_API_KEY,
  environment: 'production'
});

// Create an onboarding module
const module = await smarix.modules.create({
  title: 'Frontend Onboarding',
  description: 'Introduction to React',
  content: {
    sections: [
      { title: 'Setup', content: '...' },
      { title: 'First Steps', content: '...' }
    ]
  }
});

console.log('Module created:', module.id);`,
  authentication: `// Using API Key
const smarix = new Smarix({
  apiKey: 'sk_live_...'
});

// Using OAuth 2.0
const smarix = new Smarix({
  clientId: 'your_client_id',
  clientSecret: 'your_client_secret',
  redirectUri: 'https://your-app.com/callback'
});

// Generate access token
const token = await smarix.auth.getAccessToken();
const smarixWithToken = new Smarix({
  accessToken: token.access_token
});`,
  webhook: `// Express.js webhook handler
const express = require('express');
const crypto = require('crypto');

const app = express();
app.use(express.json());

const WEBHOOK_SECRET = process.env.SMARIX_WEBHOOK_SECRET;

app.post('/webhooks/smarix', (req, res) => {
  const signature = req.headers['x-smarix-signature'];
  const payload = JSON.stringify(req.body);
  
  const hash = crypto
    .createHmac('sha256', WEBHOOK_SECRET)
    .update(payload)
    .digest('hex');
  
  if (signature === hash) {
    const event = req.body;
    
    switch (event.type) {
      case 'onboarding.completed':
        handleOnboardingComplete(event.data);
        break;
      case 'offboarding.started':
        handleOffboardingStart(event.data);
        break;
    }
    
    res.status(200).send('OK');
  } else {
    res.status(401).send('Invalid signature');
  }
});`,
};

export default function DocumentationPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeSection, setActiveSection] = useState('getting-started');
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const { scrollYProgress } = useScroll();

  const copyToClipboard = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const filteredSections = docSections.filter(section =>
    section.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    section.subsections.some(sub => sub.title.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <main className="min-h-screen bg-[#FAFAFA] text-[#0E1B2E] relative selection:bg-[#0E1B2E] selection:text-white">
      <Navbar />
      
      {/* Hero Section */}
      <section className="relative w-full pt-32 pb-16 px-6 overflow-hidden border-b border-gray-200">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
        
        <div className="relative max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-12"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#0E1B2E]/5 border border-[#0E1B2E]/10 mb-6"
            >
              <BookOpen className="w-4 h-4 text-[#0E1B2E]/60" />
              <span className={`${victorMono.className} text-xs text-[#0E1B2E]/70`}>
                Developer Documentation
              </span>
            </motion.div>
            
            <h1 className={`${firaCode.className} text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.1] text-[#0E1B2E] mb-6`}>
              Documentation
            </h1>
            <p className={`${victorMono.className} text-xl text-[#0E1B2E]/70 max-w-2xl mx-auto leading-relaxed mb-8`}>
              Everything you need to integrate and use Smarix in your applications
            </p>

            {/* Search Bar */}
            <div className="max-w-2xl mx-auto">
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#0E1B2E]/40" />
                <input
                  type="text"
                  placeholder="Search documentation..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className={`
                    w-full pl-12 pr-4 py-4 bg-white border-2 border-gray-200 rounded-xl
                    ${victorMono.className} text-[#0E1B2E] placeholder:text-[#0E1B2E]/30
                    focus:outline-none focus:border-[#0E1B2E] focus:ring-2 focus:ring-[#0E1B2E]/10
                    transition-all duration-200
                  `}
                />
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Main Content */}
      <div className="flex relative">
        {/* Sidebar */}
        <motion.aside
          initial={{ x: -300, opacity: 0 }}
          animate={{ x: isSidebarOpen ? 0 : -300, opacity: isSidebarOpen ? 1 : 0 }}
          transition={{ duration: 0.3 }}
          className={`
            fixed lg:sticky top-0 h-screen w-80 bg-white border-r border-gray-200 overflow-y-auto z-30
            ${isSidebarOpen ? 'block' : 'hidden lg:block'}
          `}
        >
          <div className="p-6 sticky top-0 bg-white border-b border-gray-200 z-10">
            <h2 className={`${firaCode.className} text-lg font-bold text-[#0E1B2E] mb-4`}>
              Table of Contents
            </h2>
          </div>
          
          <nav className="p-6 space-y-1">
            {filteredSections.map((section) => {
              const Icon = section.icon;
              return (
                <div key={section.id} className="mb-6">
                  <button
                    onClick={() => setActiveSection(activeSection === section.id ? '' : section.id)}
                    className={`
                      w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200
                      ${activeSection === section.id 
                        ? 'bg-[#0E1B2E] text-white' 
                        : 'text-[#0E1B2E] hover:bg-gray-50'
                      }
                    `}
                  >
                    <Icon className="w-5 h-5 shrink-0" />
                    <span className={`${victorMono.className} text-sm font-medium flex-1 text-left`}>
                      {section.title}
                    </span>
                    <ChevronRight 
                      className={`w-4 h-4 transition-transform duration-200 shrink-0 ${
                        activeSection === section.id ? 'rotate-90' : ''
                      }`}
                    />
                  </button>
                  
                  {activeSection === section.id && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-2 space-y-1 pl-12"
                    >
                      {section.subsections.map((subsection) => (
                        <a
                          key={subsection.id}
                          href={subsection.href}
                          className={`
                            block px-4 py-2 rounded-lg transition-colors duration-200
                            ${victorMono.className} text-sm
                            text-[#0E1B2E]/70 hover:text-[#0E1B2E] hover:bg-gray-50
                          `}
                        >
                          {subsection.title}
                        </a>
                      ))}
                    </motion.div>
                  )}
                </div>
              );
            })}
          </nav>
        </motion.aside>

        {/* Content Area */}
        <div className="flex-1 lg:ml-80">
          <div className="max-w-4xl mx-auto px-6 py-12">
            {/* Introduction */}
            <section id="introduction" className="mb-16 scroll-mt-24">
              <div className="flex items-center gap-3 mb-6">
                <Rocket className="w-6 h-6 text-blue-600" />
                <h2 className={`${firaCode.className} text-3xl font-bold text-[#0E1B2E]`}>
                  Introduction
                </h2>
              </div>
              <div className={`${victorMono.className} space-y-4 text-[#0E1B2E]/80 leading-relaxed`}>
                <p>
                  Welcome to the Smarix documentation! Smarix is an AI-powered platform that helps organizations 
                  streamline onboarding and offboarding processes, capture tribal knowledge, and maintain 
                  institutional memory.
                </p>
                <p>
                  This documentation will guide you through integrating Smarix into your applications, 
                  understanding our API, and implementing best practices for knowledge management.
                </p>
              </div>
            </section>

            {/* Quick Start */}
            <section id="quick-start" className="mb-16 scroll-mt-24">
              <div className="flex items-center gap-3 mb-6">
                <Zap className="w-6 h-6 text-blue-600" />
                <h2 className={`${firaCode.className} text-3xl font-bold text-[#0E1B2E]`}>
                  Quick Start
                </h2>
              </div>
              
              <div className="space-y-6">
                <div className={`${victorMono.className} space-y-4 text-[#0E1B2E]/80 leading-relaxed`}>
                  <p>
                    Get up and running with Smarix in minutes. Follow these simple steps to start 
                    integrating our platform.
                  </p>
                </div>

                <div className="relative bg-[#0E1B2E] rounded-xl p-6 shadow-xl overflow-hidden">
                  <div className="absolute inset-0 bg-[linear-gradient(to_right,#FFFFFF05_1px,transparent_1px),linear-gradient(to_bottom,#FFFFFF05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none opacity-20" />
                  
                  <div className="relative z-10">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <Terminal className="w-5 h-5 text-blue-400" />
                        <span className={`${firaCode.className} text-sm font-bold text-white/90 uppercase tracking-wider`}>
                          Quick Start Example
                        </span>
                      </div>
                      <button
                        onClick={() => copyToClipboard(codeExamples.quickStart, 'quickStart')}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors text-white/80 hover:text-white"
                      >
                        {copiedCode === 'quickStart' ? (
                          <>
                            <Check className="w-4 h-4" />
                            <span className={`${victorMono.className} text-xs`}>Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-4 h-4" />
                            <span className={`${victorMono.className} text-xs`}>Copy</span>
                          </>
                        )}
                      </button>
                    </div>
                    
                    <pre className="overflow-x-auto">
                      <code className={`${firaCode.className} text-sm text-white/90 leading-relaxed`}>
                        {codeExamples.quickStart}
                      </code>
                    </pre>
                  </div>
                </div>
              </div>
            </section>

            {/* Authentication */}
            <section id="authentication" className="mb-16 scroll-mt-24">
              <div className="flex items-center gap-3 mb-6">
                <Lock className="w-6 h-6 text-blue-600" />
                <h2 className={`${firaCode.className} text-3xl font-bold text-[#0E1B2E]`}>
                  Authentication
                </h2>
              </div>
              
              <div className="space-y-6">
                <div className={`${victorMono.className} space-y-4 text-[#0E1B2E]/80 leading-relaxed`}>
                  <p>
                    Smarix supports multiple authentication methods to secure your API requests. 
                    Choose the method that best fits your use case.
                  </p>
                </div>

                <div className="relative bg-[#0E1B2E] rounded-xl p-6 shadow-xl overflow-hidden">
                  <div className="absolute inset-0 bg-[linear-gradient(to_right,#FFFFFF05_1px,transparent_1px),linear-gradient(to_bottom,#FFFFFF05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none opacity-20" />
                  
                  <div className="relative z-10">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <Key className="w-5 h-5 text-blue-400" />
                        <span className={`${firaCode.className} text-sm font-bold text-white/90 uppercase tracking-wider`}>
                          Authentication Example
                        </span>
                      </div>
                      <button
                        onClick={() => copyToClipboard(codeExamples.authentication, 'authentication')}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors text-white/80 hover:text-white"
                      >
                        {copiedCode === 'authentication' ? (
                          <>
                            <Check className="w-4 h-4" />
                            <span className={`${victorMono.className} text-xs`}>Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-4 h-4" />
                            <span className={`${victorMono.className} text-xs`}>Copy</span>
                          </>
                        )}
                      </button>
                    </div>
                    
                    <pre className="overflow-x-auto">
                      <code className={`${firaCode.className} text-sm text-white/90 leading-relaxed`}>
                        {codeExamples.authentication}
                      </code>
                    </pre>
                  </div>
                </div>
              </div>
            </section>

            {/* REST API */}
            <section id="rest-api" className="mb-16 scroll-mt-24">
              <div className="flex items-center gap-3 mb-6">
                <Code2 className="w-6 h-6 text-purple-600" />
                <h2 className={`${firaCode.className} text-3xl font-bold text-[#0E1B2E]`}>
                  REST API
                </h2>
              </div>
              
              <div className={`${victorMono.className} space-y-6 text-[#0E1B2E]/80 leading-relaxed`}>
                <p>
                  Smarix provides a comprehensive REST API for all operations. All API requests should 
                  be made to the base URL: <code className="bg-gray-100 px-2 py-1 rounded text-sm">https://api.smarix.ai/v1</code>
                </p>
                
                <div className="bg-white border-2 border-gray-200 rounded-xl p-6">
                  <h3 className={`${firaCode.className} text-lg font-bold text-[#0E1B2E] mb-4`}>
                    Base URL
                  </h3>
                  <code className={`${victorMono.className} text-sm text-blue-600`}>
                    https://api.smarix.ai/v1
                  </code>
                </div>

                <div className="bg-white border-2 border-gray-200 rounded-xl p-6">
                  <h3 className={`${firaCode.className} text-lg font-bold text-[#0E1B2E] mb-4`}>
                    Common Endpoints
                  </h3>
                  <ul className="space-y-3">
                    <li className="flex items-start gap-3">
                      <span className="text-blue-600 mt-1">•</span>
                      <div>
                        <code className="bg-gray-100 px-2 py-1 rounded text-sm">POST /modules</code>
                        <p className="text-sm text-[#0E1B2E]/60 mt-1">Create a new onboarding module</p>
                      </div>
                    </li>
                    <li className="flex items-start gap-3">
                      <span className="text-blue-600 mt-1">•</span>
                      <div>
                        <code className="bg-gray-100 px-2 py-1 rounded text-sm">GET /employees/:id/progress</code>
                        <p className="text-sm text-[#0E1B2E]/60 mt-1">Get employee onboarding progress</p>
                      </div>
                    </li>
                    <li className="flex items-start gap-3">
                      <span className="text-blue-600 mt-1">•</span>
                      <div>
                        <code className="bg-gray-100 px-2 py-1 rounded text-sm">POST /offboarding/start</code>
                        <p className="text-sm text-[#0E1B2E]/60 mt-1">Start an offboarding workflow</p>
                      </div>
                    </li>
                  </ul>
                </div>
              </div>
            </section>

            {/* Webhooks */}
            <section id="webhooks" className="mb-16 scroll-mt-24">
              <div className="flex items-center gap-3 mb-6">
                <Webhook className="w-6 h-6 text-green-600" />
                <h2 className={`${firaCode.className} text-3xl font-bold text-[#0E1B2E]`}>
                  Webhooks
                </h2>
              </div>
              
              <div className="space-y-6">
                <div className={`${victorMono.className} space-y-4 text-[#0E1B2E]/80 leading-relaxed`}>
                  <p>
                    Webhooks allow you to receive real-time notifications about events in your Smarix workspace. 
                    Configure your webhook endpoint to receive updates automatically.
                  </p>
                </div>

                <div className="relative bg-[#0E1B2E] rounded-xl p-6 shadow-xl overflow-hidden">
                  <div className="absolute inset-0 bg-[linear-gradient(to_right,#FFFFFF05_1px,transparent_1px),linear-gradient(to_bottom,#FFFFFF05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none opacity-20" />
                  
                  <div className="relative z-10">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <Webhook className="w-5 h-5 text-green-400" />
                        <span className={`${firaCode.className} text-sm font-bold text-white/90 uppercase tracking-wider`}>
                          Webhook Handler Example
                        </span>
                      </div>
                      <button
                        onClick={() => copyToClipboard(codeExamples.webhook, 'webhook')}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors text-white/80 hover:text-white"
                      >
                        {copiedCode === 'webhook' ? (
                          <>
                            <Check className="w-4 h-4" />
                            <span className={`${victorMono.className} text-xs`}>Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-4 h-4" />
                            <span className={`${victorMono.className} text-xs`}>Copy</span>
                          </>
                        )}
                      </button>
                    </div>
                    
                    <pre className="overflow-x-auto">
                      <code className={`${firaCode.className} text-sm text-white/90 leading-relaxed`}>
                        {codeExamples.webhook}
                      </code>
                    </pre>
                  </div>
                </div>
              </div>
            </section>

            {/* CTA Section */}
            <section className="mt-16 p-12 bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-100 rounded-2xl">
              <div className="text-center">
                <Sparkles className="w-12 h-12 text-blue-600 mx-auto mb-6" />
                <h2 className={`${firaCode.className} text-2xl font-bold text-[#0E1B2E] mb-4`}>
                  Need More Help?
                </h2>
                <p className={`${victorMono.className} text-[#0E1B2E]/70 mb-8 max-w-2xl mx-auto`}>
                  Can't find what you're looking for? Our support team is here to help.
                </p>
                <div className="flex flex-wrap items-center justify-center gap-4">
                  <motion.a
                    href="/contact"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="group inline-flex items-center gap-3 bg-[#0E1B2E] text-white px-8 py-4 rounded-xl hover:bg-[#1a2f4d] transition-all duration-300 shadow-xl shadow-[#0E1B2E]/10"
                  >
                    <span className={`${firaCode.className} font-bold tracking-wide text-sm`}>
                      CONTACT SUPPORT
                    </span>
                    <ArrowRight className="w-5 h-5 transition-transform duration-300 group-hover:translate-x-1" />
                  </motion.a>
                  <motion.a
                    href="/integration"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className={`${firaCode.className} text-sm font-bold text-[#0E1B2E] hover:text-blue-600 transition-colors underline decoration-gray-300 underline-offset-4 hover:decoration-blue-600 px-4 py-2`}
                  >
                    View Integration Guide
                  </motion.a>
                </div>
              </div>
            </section>
          </div>
        </div>

        {/* Sidebar Toggle Button (Mobile) */}
        <button
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className="fixed bottom-6 right-6 lg:hidden z-40 w-14 h-14 bg-[#0E1B2E] text-white rounded-full shadow-xl flex items-center justify-center"
        >
          <BookOpen className="w-6 h-6" />
        </button>
      </div>

      <Footer />
    </main>
  );
}

