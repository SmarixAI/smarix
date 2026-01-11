'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Navbar } from '@/components/landing/Navbar';
import { Footer } from '@/components/landing/Footer';
import { Fira_Code, Victor_Mono } from 'next/font/google';
import { 
  GitBranch, 
  UserPlus, 
  UserMinus, 
  MessageSquare, 
  Settings, 
  Users,
  ArrowRight,
  CheckCircle2,
  Sparkles,
  Database,
  Workflow,
  Shield,
  BarChart3,
  BookOpen,
  Zap,
  Network,
  GitMerge,
  FileText,
  Eye,
  PlayCircle,
  TrendingUp,
  History
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

const integrationComponents = [
  {
    id: 'onboarding',
    title: 'Onboarding Integration',
    description: 'Seamlessly integrate Smarix onboarding with your repository to create structured learning paths for new employees.',
    icon: UserPlus,
    color: '#3B82F6',
    bgGradient: 'from-blue-50 to-cyan-50',
    borderColor: 'border-blue-200',
    iconBg: 'bg-blue-100',
    features: [
      'Automatic module generation from codebase structure',
      'AI-powered learning path recommendations',
      'Progress tracking and analytics',
      'Interactive tutorials and practice tasks',
      'Integration with existing documentation'
    ],
    workflow: [
      'Connect your repository',
      'AI analyzes codebase structure',
      'Generate customized onboarding modules',
      'Employees progress through learning paths',
      'Managers track completion and performance'
    ]
  },
  {
    id: 'offboarding',
    title: 'Offboarding Integration',
    description: 'Capture institutional knowledge and ensure smooth transitions when employees leave your organization.',
    icon: UserMinus,
    color: '#8B5CF6',
    bgGradient: 'from-purple-50 to-pink-50',
    borderColor: 'border-purple-200',
    iconBg: 'bg-purple-100',
    features: [
      'Automated knowledge capture workflows',
      'Documentation gap identification',
      'Structured handover templates',
      'Access revocation automation',
      'Knowledge repository updates'
    ],
    workflow: [
      'Initiate offboarding process',
      'AI identifies knowledge gaps',
      'Capture tribal knowledge',
      'Generate handover documentation',
      'Update knowledge base automatically'
    ]
  },
  {
    id: 'assistant',
    title: 'Smarix Assistant Integration',
    description: 'AI-powered assistant that understands your codebase and provides contextual help to your entire team.',
    icon: MessageSquare,
    color: '#10B981',
    bgGradient: 'from-emerald-50 to-teal-50',
    borderColor: 'border-emerald-200',
    iconBg: 'bg-emerald-100',
    features: [
      'Codebase-aware question answering',
      'Real-time code analysis and suggestions',
      'Documentation generation',
      'Contextual debugging assistance',
      'Team-wide knowledge sharing'
    ],
    workflow: [
      'Connect repository to Smarix Assistant',
      'AI indexes codebase and documentation',
      'Team members ask questions',
      'Assistant provides contextual answers',
      'Knowledge continuously updated'
    ]
  },
];

const adminFeatures = [
  {
    icon: Settings,
    title: 'Pipeline Setup',
    description: 'Configure and manage onboarding/offboarding pipelines for your organization.',
    color: '#3B82F6'
  },
  {
    icon: Database,
    title: 'Repository Management',
    description: 'Connect and manage multiple repositories across your organization.',
    color: '#8B5CF6'
  },
  {
    icon: Users,
    title: 'User Management',
    description: 'Manage user access, roles, and permissions across your Smarix workspace.',
    color: '#10B981'
  },
  {
    icon: BarChart3,
    title: 'Analytics & Insights',
    description: 'Track onboarding success rates, knowledge retention, and team productivity metrics.',
    color: '#F59E0B'
  },
  {
    icon: Shield,
    title: 'Security & Compliance',
    description: 'Configure security settings, access controls, and compliance policies.',
    color: '#EF4444'
  },
  {
    icon: History,
    title: 'Activity History',
    description: 'Monitor all system activities, pipeline executions, and user actions.',
    color: '#6366F1'
  },
];

const managerFeatures = [
  {
    icon: Eye,
    title: 'Progress Tracking',
    description: 'Monitor employee onboarding progress in real-time with detailed analytics.',
    color: '#3B82F6'
  },
  {
    icon: PlayCircle,
    title: 'Task Management',
    description: 'Assign and manage onboarding/offboarding tasks for your team members.',
    color: '#8B5CF6'
  },
  {
    icon: TrendingUp,
    title: 'Performance Metrics',
    description: 'View productivity trends and identify areas for improvement.',
    color: '#10B981'
  },
  {
    icon: FileText,
    title: 'Documentation Review',
    description: 'Review and approve documentation generated during offboarding processes.',
    color: '#F59E0B'
  },
];

export default function IntegrationPage() {
  const [activeComponent, setActiveComponent] = useState('onboarding');

  return (
    <main className="min-h-screen bg-[#FAFAFA] text-[#0E1B2E] relative selection:bg-[#0E1B2E] selection:text-white">
      <Navbar />
      
      {/* Hero Section */}
      <section className="relative w-full pt-32 pb-24 px-6 overflow-hidden">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
        
        <div className="relative max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#0E1B2E]/5 border border-[#0E1B2E]/10 mb-6"
            >
              <Network className="w-4 h-4 text-[#0E1B2E]/60" />
              <span className={`${victorMono.className} text-xs text-[#0E1B2E]/70`}>
                Company Integration
              </span>
            </motion.div>
            
            <h1 className={`${firaCode.className} text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.1] text-[#0E1B2E] mb-6`}>
              Integrate Smarix with Your Organization
            </h1>
            <p className={`${victorMono.className} text-xl text-[#0E1B2E]/70 max-w-2xl mx-auto leading-relaxed mb-8`}>
              Connect Smarix with your repositories and workflows to streamline onboarding, offboarding, and knowledge management across your entire organization.
            </p>

            <div className="flex flex-wrap items-center justify-center gap-4">
              <motion.a
                href="#components"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="group inline-flex items-center gap-3 bg-[#0E1B2E] text-white px-8 py-4 rounded-xl hover:bg-[#1a2f4d] transition-all duration-300 shadow-xl shadow-[#0E1B2E]/10"
              >
                <span className={`${firaCode.className} font-bold tracking-wide text-sm`}>
                  EXPLORE INTEGRATION
                </span>
                <ArrowRight className="w-5 h-5 transition-transform duration-300 group-hover:translate-x-1" />
              </motion.a>
              <motion.a
                href="/documentation"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={`${firaCode.className} text-sm font-bold text-[#0E1B2E] hover:text-blue-600 transition-colors underline decoration-gray-300 underline-offset-4 hover:decoration-blue-600`}
              >
                Developer Docs
              </motion.a>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Repository Integration Overview */}
      <section className="relative w-full py-24 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className={`${firaCode.className} text-3xl md:text-4xl font-bold tracking-tight text-[#0E1B2E] mb-4`}>
              Repository Integration
            </h2>
            <p className={`${victorMono.className} text-lg text-[#0E1B2E]/70 max-w-2xl mx-auto`}>
              Connect your codebase with Smarix to unlock intelligent onboarding, offboarding, and assistance capabilities
            </p>
          </motion.div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-16">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="p-8 bg-gradient-to-br from-blue-50 to-cyan-50 border-2 border-blue-200 rounded-2xl"
            >
              <GitBranch className="w-12 h-12 text-blue-600 mb-4" />
              <h3 className={`${firaCode.className} text-xl font-bold text-[#0E1B2E] mb-3`}>
                Connect Repository
              </h3>
              <p className={`${victorMono.className} text-sm text-[#0E1B2E]/70 leading-relaxed`}>
                Link your GitHub, GitLab, or Bitbucket repository to Smarix. Our AI analyzes your codebase structure automatically.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="p-8 bg-gradient-to-br from-purple-50 to-pink-50 border-2 border-purple-200 rounded-2xl"
            >
              <Workflow className="w-12 h-12 text-purple-600 mb-4" />
              <h3 className={`${firaCode.className} text-xl font-bold text-[#0E1B2E] mb-3`}>
                Configure Workflows
              </h3>
              <p className={`${victorMono.className} text-sm text-[#0E1B2E]/70 leading-relaxed`}>
                Set up onboarding and offboarding pipelines tailored to your organization's processes and requirements.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="p-8 bg-gradient-to-br from-emerald-50 to-teal-50 border-2 border-emerald-200 rounded-2xl"
            >
              <Zap className="w-12 h-12 text-emerald-600 mb-4" />
              <h3 className={`${firaCode.className} text-xl font-bold text-[#0E1B2E] mb-3`}>
                Automate Processes
              </h3>
              <p className={`${victorMono.className} text-sm text-[#0E1B2E]/70 leading-relaxed`}>
                Enable automated knowledge capture, documentation updates, and seamless team workflows.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Integration Components */}
      <section id="components" className="relative w-full py-24 px-6 bg-[#FAFAFA]">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
        
        <div className="relative max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className={`${firaCode.className} text-3xl md:text-4xl font-bold tracking-tight text-[#0E1B2E] mb-4`}>
              Core Integration Components
            </h2>
            <p className={`${victorMono.className} text-lg text-[#0E1B2E]/70 max-w-2xl mx-auto`}>
              Three powerful systems working together to transform your knowledge management
            </p>
          </motion.div>

          {/* Component Selector */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            {integrationComponents.map((component, index) => {
              const Icon = component.icon;
              const isActive = activeComponent === component.id;
              return (
                <motion.button
                  key={component.id}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  onClick={() => setActiveComponent(component.id)}
                  whileHover={{ scale: 1.02, y: -4 }}
                  whileTap={{ scale: 0.98 }}
                  className={`
                    relative p-6 rounded-2xl border-2 text-left transition-all duration-300
                    ${isActive 
                      ? `${component.borderColor} bg-gradient-to-br ${component.bgGradient} shadow-xl shadow-black/10` 
                      : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-lg'
                    }
                  `}
                >
                  <div className={`
                    w-12 h-12 rounded-xl ${component.iconBg} flex items-center justify-center mb-4
                    transition-transform duration-300 ${isActive ? 'scale-110' : ''}
                  `}>
                    <Icon className="w-6 h-6" style={{ color: component.color }} />
                  </div>
                  <h3 className={`${firaCode.className} text-xl font-bold text-[#0E1B2E] mb-2`}>
                    {component.title}
                  </h3>
                  <p className={`${victorMono.className} text-sm text-[#0E1B2E]/70 leading-relaxed`}>
                    {component.description}
                  </p>
                  {isActive && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="absolute top-4 right-4 w-6 h-6 rounded-full bg-[#0E1B2E] flex items-center justify-center"
                    >
                      <CheckCircle2 className="w-4 h-4 text-white" />
                    </motion.div>
                  )}
                </motion.button>
              );
            })}
          </div>

          {/* Active Component Details */}
          {integrationComponents.map((component) => {
            if (component.id !== activeComponent) return null;
            const Icon = component.icon;
            
            return (
              <motion.div
                key={component.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="grid grid-cols-1 lg:grid-cols-2 gap-8"
              >
                {/* Features */}
                <div className="p-8 bg-white border-2 border-gray-200 rounded-2xl">
                  <div className="flex items-center gap-3 mb-6">
                    <div className={`w-12 h-12 rounded-xl ${component.iconBg} flex items-center justify-center`}>
                      <Icon className="w-6 h-6" style={{ color: component.color }} />
                    </div>
                    <h3 className={`${firaCode.className} text-2xl font-bold text-[#0E1B2E]`}>
                      Key Features
                    </h3>
                  </div>
                  <ul className="space-y-4">
                    {component.features.map((feature, idx) => (
                      <li key={idx} className="flex items-start gap-3">
                        <CheckCircle2 className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
                        <span className={`${victorMono.className} text-sm text-[#0E1B2E]/80`}>
                          {feature}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Workflow */}
                <div className="p-8 bg-white border-2 border-gray-200 rounded-2xl">
                  <div className="flex items-center gap-3 mb-6">
                    <Workflow className="w-12 h-12 text-blue-600" />
                    <h3 className={`${firaCode.className} text-2xl font-bold text-[#0E1B2E]`}>
                      Integration Workflow
                    </h3>
                  </div>
                  <ol className="space-y-4">
                    {component.workflow.map((step, idx) => (
                      <li key={idx} className="flex items-start gap-4">
                        <div className="w-8 h-8 rounded-full bg-[#0E1B2E] text-white flex items-center justify-center shrink-0">
                          <span className={`${firaCode.className} text-sm font-bold`}>
                            {idx + 1}
                          </span>
                        </div>
                        <span className={`${victorMono.className} text-sm text-[#0E1B2E]/80 pt-1.5`}>
                          {step}
                        </span>
                      </li>
                    ))}
                  </ol>
                </div>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* Admin Panel Section */}
      <section className="relative w-full py-24 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-50 border border-blue-200 mb-6">
              <Settings className="w-4 h-4 text-blue-600" />
              <span className={`${victorMono.className} text-xs text-blue-700`}>
                Administrative Control
              </span>
            </div>
            <h2 className={`${firaCode.className} text-3xl md:text-4xl font-bold tracking-tight text-[#0E1B2E] mb-4`}>
              Admin Panel
            </h2>
            <p className={`${victorMono.className} text-lg text-[#0E1B2E]/70 max-w-2xl mx-auto`}>
              Comprehensive administrative tools to configure, manage, and monitor your Smarix integration
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {adminFeatures.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className="p-6 bg-gradient-to-br from-gray-50 to-white border-2 border-gray-200 rounded-xl hover:border-blue-300 hover:shadow-lg transition-all duration-300"
                >
                  <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center mb-4">
                    <Icon className="w-6 h-6" style={{ color: feature.color }} />
                  </div>
                  <h3 className={`${firaCode.className} text-lg font-bold text-[#0E1B2E] mb-2`}>
                    {feature.title}
                  </h3>
                  <p className={`${victorMono.className} text-sm text-[#0E1B2E]/70 leading-relaxed`}>
                    {feature.description}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Manager Dashboard Section */}
      <section className="relative w-full py-24 px-6 bg-[#0E1B2E] text-white overflow-hidden">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#FFFFFF05_1px,transparent_1px),linear-gradient(to_bottom,#FFFFFF05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none opacity-20" />
        
        <div className="relative max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 border border-white/20 mb-6">
              <Users className="w-4 h-4 text-white" />
              <span className={`${victorMono.className} text-xs text-white/90`}>
                Management Interface
              </span>
            </div>
            <h2 className={`${firaCode.className} text-3xl md:text-4xl font-bold tracking-tight mb-4`}>
              Manager Dashboard
            </h2>
            <p className={`${victorMono.className} text-lg text-white/70 max-w-2xl mx-auto`}>
              Powerful dashboard for managers to oversee team onboarding, offboarding, and knowledge management
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {managerFeatures.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl hover:bg-white/10 transition-all duration-300"
                >
                  <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center mb-4">
                    <Icon className="w-6 h-6 text-blue-400" />
                  </div>
                  <h3 className={`${firaCode.className} text-lg font-bold mb-2`}>
                    {feature.title}
                  </h3>
                  <p className={`${victorMono.className} text-sm text-white/70 leading-relaxed`}>
                    {feature.description}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* How It Works Together */}
      <section className="relative w-full py-24 px-6 bg-[#FAFAFA]">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
        
        <div className="relative max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className={`${firaCode.className} text-3xl md:text-4xl font-bold tracking-tight text-[#0E1B2E] mb-4`}>
              How It All Works Together
            </h2>
            <p className={`${victorMono.className} text-lg text-[#0E1B2E]/70 max-w-2xl mx-auto`}>
              A unified system that connects your repository, employees, and knowledge management
            </p>
          </motion.div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="space-y-6"
            >
              <div className="p-6 bg-white border-2 border-gray-200 rounded-xl">
                <div className="flex items-center gap-3 mb-4">
                  <GitMerge className="w-8 h-8 text-blue-600" />
                  <h3 className={`${firaCode.className} text-xl font-bold text-[#0E1B2E]`}>
                    Repository Connection
                  </h3>
                </div>
                <p className={`${victorMono.className} text-sm text-[#0E1B2E]/70 leading-relaxed`}>
                  Your codebase becomes the foundation. Smarix analyzes structure, dependencies, and patterns to understand your organization's technical ecosystem.
                </p>
              </div>

              <div className="p-6 bg-white border-2 border-gray-200 rounded-xl">
                <div className="flex items-center gap-3 mb-4">
                  <Network className="w-8 h-8 text-purple-600" />
                  <h3 className={`${firaCode.className} text-xl font-bold text-[#0E1B2E]`}>
                    Integrated Workflows
                  </h3>
                </div>
                <p className={`${victorMono.className} text-sm text-[#0E1B2E]/70 leading-relaxed`}>
                  Onboarding, offboarding, and assistant all share the same knowledge base, ensuring consistency and continuity across all processes.
                </p>
              </div>

              <div className="p-6 bg-white border-2 border-gray-200 rounded-xl">
                <div className="flex items-center gap-3 mb-4">
                  <Database className="w-8 h-8 text-emerald-600" />
                  <h3 className={`${firaCode.className} text-xl font-bold text-[#0E1B2E]`}>
                    Continuous Learning
                  </h3>
                </div>
                <p className={`${victorMono.className} text-sm text-[#0E1B2E]/70 leading-relaxed`}>
                  Knowledge captured during onboarding and offboarding enriches the assistant, making it smarter over time.
                </p>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="p-12 bg-gradient-to-br from-blue-50 via-purple-50 to-emerald-50 border-2 border-gray-200 rounded-2xl"
            >
              <h3 className={`${firaCode.className} text-2xl font-bold text-[#0E1B2E] mb-6 text-center`}>
                Integration Flow
              </h3>
              <div className="space-y-6">
                {[
                  { step: '1', text: 'Connect Repository', bgColor: 'bg-blue-100', textColor: 'text-blue-600' },
                  { step: '2', text: 'Admin Configures Pipelines', bgColor: 'bg-purple-100', textColor: 'text-purple-600' },
                  { step: '3', text: 'Onboarding Automatically Starts', bgColor: 'bg-emerald-100', textColor: 'text-emerald-600' },
                  { step: '4', text: 'Knowledge Base Updates', bgColor: 'bg-blue-100', textColor: 'text-blue-600' },
                  { step: '5', text: 'Assistant Uses Knowledge', bgColor: 'bg-purple-100', textColor: 'text-purple-600' },
                  { step: '6', text: 'Offboarding Captures New Knowledge', bgColor: 'bg-emerald-100', textColor: 'text-emerald-600' },
                ].map((item, idx) => (
                  <div key={idx} className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-xl ${item.bgColor} flex items-center justify-center shrink-0`}>
                      <span className={`${firaCode.className} text-lg font-bold ${item.textColor}`}>
                        {item.step}
                      </span>
                    </div>
                    <span className={`${victorMono.className} text-sm font-medium text-[#0E1B2E]`}>
                      {item.text}
                    </span>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative w-full py-24 px-6 bg-[#FAFAFA]">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="p-12 bg-white border-2 border-gray-200 rounded-2xl shadow-xl"
          >
            <Sparkles className="w-12 h-12 text-blue-600 mx-auto mb-6" />
            <h2 className={`${firaCode.className} text-3xl md:text-4xl font-bold text-[#0E1B2E] mb-4`}>
              Ready to Integrate Smarix?
            </h2>
            <p className={`${victorMono.className} text-lg text-[#0E1B2E]/70 mb-8 max-w-2xl mx-auto`}>
              Transform your organization's knowledge management with seamless integration. Schedule a demo to see how it works.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-4">
              <motion.a
                href="/request-demo"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="group inline-flex items-center gap-3 bg-[#0E1B2E] text-white px-8 py-4 rounded-xl hover:bg-[#1a2f4d] transition-all duration-300 shadow-xl shadow-[#0E1B2E]/10"
              >
                <span className={`${firaCode.className} font-bold tracking-wide text-sm`}>
                  REQUEST DEMO
                </span>
                <ArrowRight className="w-5 h-5 transition-transform duration-300 group-hover:translate-x-1" />
              </motion.a>
              <motion.a
                href="/try-our-product"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={`${firaCode.className} text-sm font-bold text-[#0E1B2E] hover:text-blue-600 transition-colors underline decoration-gray-300 underline-offset-4 hover:decoration-blue-600 px-4 py-2`}
              >
                Try It Free
              </motion.a>
            </div>
          </motion.div>
        </div>
      </section>

      <Footer />
    </main>
  );
}
