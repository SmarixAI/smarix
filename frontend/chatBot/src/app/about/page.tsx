'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Navbar } from '@/components/landing/Navbar';
import { Footer } from '@/components/landing/Footer';
import { Target, Users, Zap, TrendingUp, Heart, Shield, Clock, Brain } from 'lucide-react';
import { Space_Grotesk, Victor_Mono, Fira_Code } from 'next/font/google';

const spaceGrotesk = Space_Grotesk({ subsets: ['latin'] });
const victorMono = Victor_Mono({ weight: ["400", "500", "700"], subsets: ['latin'] });
const firaCode = Fira_Code({ weight: ["400", "500", "600", "700"], subsets: ['latin'] });

const values = [
  {
    icon: Zap,
    title: 'Innovation First',
    description: 'We push the boundaries of what AI can do for engineering teams, constantly evolving our platform.',
    color: 'from-blue-500 to-cyan-500',
    bgColor: 'bg-blue-50',
  },
  {
    icon: Users,
    title: 'Developer Focused',
    description: 'Every feature is built with developers in mind, ensuring seamless integration into your workflow.',
    color: 'from-purple-500 to-pink-500',
    bgColor: 'bg-purple-50',
  },
  {
    icon: Target,
    title: 'Knowledge Preservation',
    description: 'We believe tribal knowledge is invaluable and work tirelessly to capture and preserve it.',
    color: 'from-indigo-500 to-purple-500',
    bgColor: 'bg-indigo-50',
  },
  {
    icon: TrendingUp,
    title: 'Continuous Improvement',
    description: 'We iterate based on real-world feedback, making Smarix better with every release.',
    color: 'from-emerald-500 to-teal-500',
    bgColor: 'bg-emerald-50',
  },
];

const benefits = [
  {
    icon: Brain,
    title: 'AI-Powered Intelligence',
    description: 'Our advanced AI understands your codebase context, providing intelligent insights and documentation.',
    color: 'from-blue-500 to-cyan-500',
  },
  {
    icon: Shield,
    title: 'Secure & Private',
    description: 'Your code and knowledge stay within your infrastructure with enterprise-grade security.',
    color: 'from-purple-500 to-pink-500',
  },
  {
    icon: Clock,
    title: 'Time Efficient',
    description: 'Drastically reduce onboarding time and prevent knowledge loss during transitions.',
    color: 'from-indigo-500 to-purple-500',
  },
  {
    icon: Zap,
    title: 'Seamless Integration',
    description: 'Works with your existing tools and workflows without disrupting your team\'s productivity.',
    color: 'from-emerald-500 to-teal-500',
  },
];

export default function AboutPage() {
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
              <Heart className="w-4 h-4 text-[#0E1B2E]/60" />
              <span className={`${victorMono.className} text-xs text-[#0E1B2E]/70`}>
                Our Story
              </span>
            </motion.div>
            
            <h1 className={`${firaCode.className} text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.1] text-[#0E1B2E] mb-6`}>
              Building the Future of
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600">
                Engineering Knowledge
              </span>
            </h1>
            
            <p className={`${victorMono.className} text-xl text-[#0E1B2E]/70 max-w-3xl mx-auto leading-relaxed`}>
              Smarix was born from a simple observation: engineering teams lose critical knowledge every time someone leaves. 
              We're on a mission to change that.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="relative py-20 px-6 bg-white border-y border-[#0E1B2E]/10">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-12"
          >
            <h2 className={`${firaCode.className} text-3xl md:text-4xl font-bold text-[#0E1B2E] mb-4`}>
              Why Choose Smarix
            </h2>
            <p className={`${victorMono.className} text-lg text-[#0E1B2E]/70 max-w-2xl mx-auto`}>
              Powerful features designed to transform how your engineering team manages knowledge
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {benefits.map((benefit, index) => {
              const Icon = benefit.icon;
              return (
                <motion.div
                  key={benefit.title}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: 0.1 * index }}
                  className="group relative"
                >
                  <div className={`
                    relative h-full rounded-2xl border-2 border-[#0E1B2E]/10 bg-[#FAFAFA]
                    p-6 transition-all duration-300
                    hover:shadow-xl hover:shadow-black/5 hover:-translate-y-1
                    overflow-hidden
                  `}>
                    <div className={`
                      absolute inset-0 bg-gradient-to-br ${benefit.color} opacity-0
                      group-hover:opacity-5 transition-opacity duration-300
                    `} />
                    
                    <div className="relative z-10">
                      <div className={`
                        w-14 h-14 rounded-xl bg-gradient-to-br ${benefit.color}
                        flex items-center justify-center mb-4
                        group-hover:scale-110 transition-transform duration-300
                        shadow-lg
                      `}>
                        <Icon className="w-7 h-7 text-white" />
                      </div>
                      
                      <h3 className={`${firaCode.className} text-xl font-bold text-[#0E1B2E] mb-3`}>
                        {benefit.title}
                      </h3>
                      
                      <p className={`${victorMono.className} text-sm text-[#0E1B2E]/70 leading-relaxed`}>
                        {benefit.description}
                      </p>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Mission Section */}
      <section className="relative py-24 px-6">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
        
        <div className="relative max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
            >
              <h2 className={`${firaCode.className} text-3xl md:text-4xl font-bold text-[#0E1B2E] mb-6`}>
                Our Mission
              </h2>
              <div className="space-y-4">
                <p className={`${victorMono.className} text-lg text-[#0E1B2E]/70 leading-relaxed`}>
                  At Smarix, we believe that knowledge shouldn't walk out the door with departing employees. 
                  Our mission is to transform how engineering teams capture, preserve, and transfer institutional knowledge.
                </p>
                <p className={`${victorMono.className} text-lg text-[#0E1B2E]/70 leading-relaxed`}>
                  We're building AI-powered solutions that understand your codebase, document your processes, 
                  and ensure that every piece of tribal knowledge becomes a permanent part of your organization's DNA.
                </p>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="relative"
            >
              <div className="rounded-2xl bg-gradient-to-br from-blue-500/10 via-indigo-500/10 to-purple-500/10 p-8 border border-[#0E1B2E]/10">
                <h3 className={`${firaCode.className} text-2xl font-bold text-[#0E1B2E] mb-4`}>
                  The Problem We Solve
                </h3>
                <ul className="space-y-3">
                  {[
                    'Knowledge loss during employee transitions',
                    'Fragmented documentation across tools',
                    'Onboarding delays for new team members',
                    'Repeated mistakes due to missing context',
                  ].map((item, idx) => (
                    <li key={idx} className="flex items-start gap-3">
                      <div className="w-1.5 h-1.5 rounded-full bg-[#0E1B2E] mt-2 shrink-0" />
                      <span className={`${victorMono.className} text-base text-[#0E1B2E]/70`}>
                        {item}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Values Section */}
      <section className="relative py-24 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className={`${firaCode.className} text-3xl md:text-4xl font-bold text-[#0E1B2E] mb-4`}>
              Our Values
            </h2>
            <p className={`${victorMono.className} text-lg text-[#0E1B2E]/70 max-w-2xl mx-auto`}>
              The principles that guide everything we do
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {values.map((value, index) => {
              const Icon = value.icon;
              return (
                <motion.div
                  key={value.title}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: 0.1 * index }}
                  className="group relative"
                >
                  <div className={`
                    relative h-full rounded-2xl border-2 border-[#0E1B2E]/10 ${value.bgColor}
                    p-6 transition-all duration-300
                    hover:shadow-xl hover:shadow-black/5
                    overflow-hidden
                  `}>
                    <div className={`
                      absolute inset-0 bg-gradient-to-br ${value.color} opacity-0
                      group-hover:opacity-5 transition-opacity duration-300
                    `} />
                    
                    <div className="relative z-10">
                      <div className={`
                        w-12 h-12 rounded-xl ${value.bgColor} border border-[#0E1B2E]/10
                        flex items-center justify-center mb-4
                        group-hover:scale-110 transition-transform duration-300
                      `}>
                        <Icon className="w-6 h-6 text-[#0E1B2E]" />
                      </div>
                      
                      <h3 className={`${firaCode.className} text-xl font-bold text-[#0E1B2E] mb-2`}>
                        {value.title}
                      </h3>
                      
                      <p className={`${victorMono.className} text-sm text-[#0E1B2E]/70 leading-relaxed`}>
                        {value.description}
                      </p>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section className="relative py-24 px-6">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
        
        <div className="relative max-w-7xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className={`${firaCode.className} text-3xl md:text-4xl font-bold text-[#0E1B2E] mb-6`}>
              Built by Engineers, for Engineers
            </h2>
            <p className={`${victorMono.className} text-lg text-[#0E1B2E]/70 max-w-3xl mx-auto leading-relaxed mb-8`}>
              Our team is a diverse group of engineers, designers, and AI researchers who've experienced 
              the pain of knowledge loss firsthand. We're solving problems we've lived through.
            </p>
            <div className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-[#0E1B2E] text-white hover:bg-[#1a2f4d] transition-colors cursor-pointer">
              <span className={`${firaCode.className} text-sm font-semibold`}>
                Join Our Team
              </span>
            </div>
          </motion.div>
        </div>
      </section>

      <Footer />
    </main>
  );
}

