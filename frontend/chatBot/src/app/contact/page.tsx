'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Navbar } from '@/components/landing/Navbar';
import { Footer } from '@/components/landing/Footer';
import { Mail, MessageSquare, Phone, Send, CheckCircle, AlertCircle } from 'lucide-react';
import { Space_Grotesk, Victor_Mono, Fira_Code } from 'next/font/google';

const spaceGrotesk = Space_Grotesk({ subsets: ['latin'] });
const victorMono = Victor_Mono({ weight: ["400", "500", "700"], subsets: ['latin'] });
const firaCode = Fira_Code({ weight: ["400", "500", "600", "700"], subsets: ['latin'] });

const contactMethods = [
  {
    icon: Mail,
    title: 'Email Us',
    description: 'Send us an email anytime',
    value: 'hello@smarix.ai',
    action: 'mailto:hello@smarix.ai',
    color: 'from-blue-500 to-cyan-500',
  },
  {
    icon: Phone,
    title: 'Call Us',
    description: 'Mon-Fri 9AM-6PM EST',
    value: '+1 (555) 123-4567',
    action: 'tel:+15551234567',
    color: 'from-indigo-500 to-purple-500',
  },
];

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    subject: '',
    message: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitStatus('idle');

    // Simulate form submission
    setTimeout(() => {
      setIsSubmitting(false);
      setSubmitStatus('success');
      setFormData({
        name: '',
        email: '',
        company: '',
        subject: '',
        message: '',
      });
      
      // Reset success message after 5 seconds
      setTimeout(() => {
        setSubmitStatus('idle');
      }, 5000);
    }, 1500);
  };

  return (
    <main className="min-h-screen bg-[#FAFAFA] text-[#0E1B2E] relative selection:bg-[#0E1B2E] selection:text-white">
      <Navbar />
      
      {/* Hero Section */}
      <section className="relative w-full pt-32 pb-16 px-6 overflow-hidden">
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
              <MessageSquare className="w-4 h-4 text-[#0E1B2E]/60" />
              <span className={`${victorMono.className} text-xs text-[#0E1B2E]/70`}>
                Get in Touch
              </span>
            </motion.div>
            
            <h1 className={`${firaCode.className} text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.1] text-[#0E1B2E] mb-6`}>
              Let's Talk
            </h1>
            
            <p className={`${victorMono.className} text-xl text-[#0E1B2E]/70 max-w-2xl mx-auto leading-relaxed`}>
              Have questions about Smarix? Want to see a demo? We're here to help.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Contact Methods */}
      <section className="relative py-12 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-2 gap-8 mb-20">
            {contactMethods.map((method, index) => {
              const Icon = method.icon;
              return (
                <motion.a
                  key={method.title}
                  href={method.action}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: 0.1 * index }}
                  className="group relative cursor-pointer"
                >
                  <div className={`
                    relative h-full rounded-2xl border-2 border-[#0E1B2E]/10 bg-white
                    p-8 transition-all duration-300
                    hover:shadow-2xl hover:shadow-black/10 hover:-translate-y-2
                    overflow-hidden
                  `}>
                    <div className={`
                      absolute inset-0 bg-gradient-to-br ${method.color} opacity-0
                      group-hover:opacity-10 transition-opacity duration-300
                    `} />
                    
                    <div className="relative z-10">
                      <div className={`
                        w-16 h-16 rounded-2xl bg-gradient-to-br ${method.color}
                        flex items-center justify-center mb-6
                        group-hover:scale-110 group-hover:rotate-3 transition-all duration-300
                        shadow-lg
                      `}>
                        <Icon className="w-8 h-8 text-white" />
                      </div>
                      
                      <h3 className={`${firaCode.className} text-2xl font-bold text-[#0E1B2E] mb-2`}>
                        {method.title}
                      </h3>
                      
                      <p className={`${victorMono.className} text-sm text-[#0E1B2E]/60 mb-4`}>
                        {method.description}
                      </p>
                      
                      <p className={`${victorMono.className} text-lg font-semibold text-[#0E1B2E] group-hover:text-blue-600 transition-colors`}>
                        {method.value}
                      </p>
                    </div>
                  </div>
                </motion.a>
              );
            })}
          </div>
        </div>
      </section>

      {/* Contact Form Section */}
      <section className="relative py-20 px-6 bg-white">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
        
        <div className="relative max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="bg-white rounded-2xl border-2 border-[#0E1B2E]/10 p-8 md:p-12 lg:p-16 shadow-2xl shadow-black/10"
          >
            <div className="mb-10 text-center">
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                whileInView={{ scale: 1, opacity: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5 }}
                className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 mb-6 shadow-lg"
              >
                <MessageSquare className="w-8 h-8 text-white" />
              </motion.div>
              <h2 className={`${firaCode.className} text-3xl md:text-4xl font-bold text-[#0E1B2E] mb-4`}>
                Send us a Message
              </h2>
              <p className={`${victorMono.className} text-lg text-[#0E1B2E]/70 max-w-2xl mx-auto`}>
                Fill out the form below and we'll get back to you as soon as possible.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="name" className={`block ${victorMono.className} text-sm font-medium text-[#0E1B2E] mb-2`}>
                    Name *
                  </label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    required
                    value={formData.name}
                    onChange={handleInputChange}
                    className={`
                      w-full px-4 py-3 rounded-lg border-2 border-[#0E1B2E]/10
                      bg-[#FAFAFA] focus:border-[#0E1B2E]/30 focus:outline-none
                      transition-all duration-200
                      ${firaCode.className} text-sm
                    `}
                    placeholder="John Doe"
                  />
                </div>

                <div>
                  <label htmlFor="email" className={`block ${victorMono.className} text-sm font-medium text-[#0E1B2E] mb-2`}>
                    Email *
                  </label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    required
                    value={formData.email}
                    onChange={handleInputChange}
                    className={`
                      w-full px-4 py-3 rounded-lg border-2 border-[#0E1B2E]/10
                      bg-[#FAFAFA] focus:border-[#0E1B2E]/30 focus:outline-none
                      transition-all duration-200
                      ${firaCode.className} text-sm
                    `}
                    placeholder="john@example.com"
                  />
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="company" className={`block ${victorMono.className} text-sm font-medium text-[#0E1B2E] mb-2`}>
                    Company
                  </label>
                  <input
                    type="text"
                    id="company"
                    name="company"
                    value={formData.company}
                    onChange={handleInputChange}
                    className={`
                      w-full px-4 py-3 rounded-lg border-2 border-[#0E1B2E]/10
                      bg-[#FAFAFA] focus:border-[#0E1B2E]/30 focus:outline-none
                      transition-all duration-200
                      ${firaCode.className} text-sm
                    `}
                    placeholder="Acme Inc."
                  />
                </div>

                <div>
                  <label htmlFor="subject" className={`block ${victorMono.className} text-sm font-medium text-[#0E1B2E] mb-2`}>
                    Subject *
                  </label>
                  <select
                    id="subject"
                    name="subject"
                    required
                    value={formData.subject}
                    onChange={handleInputChange}
                    className={`
                      w-full px-4 py-3 rounded-lg border-2 border-[#0E1B2E]/10
                      bg-[#FAFAFA] focus:border-[#0E1B2E]/30 focus:outline-none
                      transition-all duration-200
                      ${firaCode.className} text-sm
                    `}
                  >
                    <option value="">Select a subject</option>
                    <option value="demo">Request Demo</option>
                    <option value="pricing">Pricing Inquiry</option>
                    <option value="support">Technical Support</option>
                    <option value="partnership">Partnership</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>

              <div>
                <label htmlFor="message" className={`block ${victorMono.className} text-sm font-medium text-[#0E1B2E] mb-2`}>
                  Message *
                </label>
                <textarea
                  id="message"
                  name="message"
                  required
                  rows={6}
                  value={formData.message}
                  onChange={handleInputChange}
                  className={`
                    w-full px-4 py-3 rounded-lg border-2 border-[#0E1B2E]/10
                    bg-[#FAFAFA] focus:border-[#0E1B2E]/30 focus:outline-none
                    transition-all duration-200 resize-none
                    ${firaCode.className} text-sm
                  `}
                  placeholder="Tell us how we can help..."
                />
              </div>

              {submitStatus === 'success' && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-3 p-4 rounded-lg bg-emerald-50 border border-emerald-200"
                >
                  <CheckCircle className="w-5 h-5 text-emerald-600" />
                  <p className={`${victorMono.className} text-sm text-emerald-700`}>
                    Thank you! We've received your message and will get back to you soon.
                  </p>
                </motion.div>
              )}

              {submitStatus === 'error' && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-3 p-4 rounded-lg bg-red-50 border border-red-200"
                >
                  <AlertCircle className="w-5 h-5 text-red-600" />
                  <p className={`${victorMono.className} text-sm text-red-700`}>
                    Something went wrong. Please try again.
                  </p>
                </motion.div>
              )}

              <div className="flex justify-center pt-4">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className={`
                    px-10 py-4 rounded-xl
                    bg-[#0E1B2E] text-white
                    hover:bg-[#1a2f4d] disabled:opacity-50 disabled:cursor-not-allowed
                    transition-all duration-200 shadow-lg hover:shadow-xl
                    flex items-center justify-center gap-2
                    ${firaCode.className} font-semibold text-base
                    transform hover:scale-105 active:scale-95
                  `}
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Send className="w-5 h-5" />
                      Send Message
                    </>
                  )}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="relative py-20 px-6 bg-[#FAFAFA]">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-12"
          >
            <h2 className={`${firaCode.className} text-3xl md:text-4xl font-bold text-[#0E1B2E] mb-4`}>
              Frequently Asked Questions
            </h2>
            <p className={`${victorMono.className} text-lg text-[#0E1B2E]/70`}>
              Quick answers to common questions
            </p>
          </motion.div>

          <div className="space-y-4">
            {[
              {
                question: 'How quickly can I get started with Smarix?',
                answer: 'You can get started in minutes. Simply sign up, connect your codebase, and our AI will begin analyzing and documenting your code.',
              },
              {
                question: 'What programming languages does Smarix support?',
                answer: 'Smarix supports all major programming languages including Python, JavaScript, TypeScript, Java, Go, Rust, and more.',
              },
              {
                question: 'Is my code data secure?',
                answer: 'Absolutely. We use enterprise-grade security measures including encryption at rest and in transit. Your code never leaves your infrastructure.',
              },
              {
                question: 'Can I integrate Smarix with my existing tools?',
                answer: 'Yes! Smarix integrates with popular tools like Slack, GitHub, Jira, and most CI/CD pipelines.',
              },
            ].map((faq, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: 0.1 * index }}
                className="bg-white rounded-xl border-2 border-[#0E1B2E]/10 p-6 md:p-8 hover:shadow-xl hover:border-[#0E1B2E]/20 transition-all duration-300"
              >
                <h3 className={`${firaCode.className} text-lg md:text-xl font-bold text-[#0E1B2E] mb-3`}>
                  {faq.question}
                </h3>
                <p className={`${victorMono.className} text-base text-[#0E1B2E]/70 leading-relaxed`}>
                  {faq.answer}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}

