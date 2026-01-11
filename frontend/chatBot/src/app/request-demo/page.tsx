'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Navbar } from '@/components/landing/Navbar';
import { Footer } from '@/components/landing/Footer';
import { Fira_Code, Victor_Mono } from 'next/font/google';
import { ArrowRight, CheckCircle2, Building2, Mail, Phone, User, MessageSquare, Calendar, Users, Briefcase, Globe, Send, Loader2 } from 'lucide-react';

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

interface FormData {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  company: string;
  jobTitle: string;
  companySize: string;
  country: string;
  message: string;
  preferredDate: string;
}

export default function RequestDemoPage() {
  const [formData, setFormData] = useState<FormData>({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    company: '',
    jobTitle: '',
    companySize: '',
    country: '',
    message: '',
    preferredDate: '',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name as keyof FormData]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof FormData, string>> = {};

    if (!formData.firstName.trim()) newErrors.firstName = 'First name is required';
    if (!formData.lastName.trim()) newErrors.lastName = 'Last name is required';
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    if (!formData.company.trim()) newErrors.company = 'Company name is required';
    if (!formData.jobTitle.trim()) newErrors.jobTitle = 'Job title is required';
    if (!formData.companySize) newErrors.companySize = 'Company size is required';
    if (!formData.country.trim()) newErrors.country = 'Country is required';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    
    // Simulate API call
    setTimeout(() => {
      setIsSubmitting(false);
      setIsSubmitted(true);
      // Reset form after showing success message
      setTimeout(() => {
        setFormData({
          firstName: '',
          lastName: '',
          email: '',
          phone: '',
          company: '',
          jobTitle: '',
          companySize: '',
          country: '',
          message: '',
          preferredDate: '',
        });
        setIsSubmitted(false);
      }, 3000);
    }, 1500);
  };

  const companySizes = [
    '1-10 employees',
    '11-50 employees',
    '51-200 employees',
    '201-500 employees',
    '501-1000 employees',
    '1000+ employees',
  ];

  return (
    <main className="min-h-screen bg-[#FAFAFA] text-[#0E1B2E] relative selection:bg-[#0E1B2E] selection:text-white">
      <Navbar />
      
      <div className="relative w-full pt-32 pb-24 px-6 overflow-hidden">
        {/* Background Grid */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
        
        <div className="relative max-w-7xl mx-auto">
          {/* Header Section */}
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
                Schedule a Demo
              </span>
            </motion.div>
            
            <h1 className={`${firaCode.className} text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.1] text-[#0E1B2E] mb-6`}>
              Request a Demo
            </h1>
            <p className={`${victorMono.className} text-xl text-[#0E1B2E]/70 max-w-2xl mx-auto leading-relaxed`}>
              See how Smarix can transform your team's knowledge management. Fill out the form below and we'll schedule a personalized demo for you.
            </p>
          </motion.div>

          {/* Success Message */}
          {isSubmitted && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="max-w-2xl mx-auto mb-8 p-6 bg-green-50 border-2 border-green-200 rounded-2xl"
            >
              <div className="flex items-start gap-4">
                <CheckCircle2 className="w-6 h-6 text-green-600 shrink-0 mt-0.5" />
                <div>
                  <h3 className={`${firaCode.className} text-lg font-bold text-green-900 mb-1`}>
                    Request Submitted Successfully!
                  </h3>
                  <p className={`${victorMono.className} text-sm text-green-700`}>
                    Thank you for your interest. Our team will reach out to you within 24 hours to schedule your demo.
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {/* Main Content */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-12 max-w-6xl mx-auto">
            {/* Form Section */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="lg:col-span-2"
            >
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Name Fields */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="firstName" className={`${victorMono.className} block text-sm font-medium text-[#0E1B2E]/70 mb-2`}>
                      First Name <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#0E1B2E]/30" />
                      <input
                        type="text"
                        id="firstName"
                        name="firstName"
                        value={formData.firstName}
                        onChange={handleChange}
                        className={`
                          w-full pl-12 pr-4 py-3.5 bg-white border-2 rounded-xl
                          ${errors.firstName ? 'border-red-300 focus:border-red-500' : 'border-gray-200 focus:border-[#0E1B2E]'}
                          ${victorMono.className} text-[#0E1B2E] placeholder:text-[#0E1B2E]/30
                          focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 transition-all duration-200
                        `}
                        placeholder="John"
                      />
                    </div>
                    {errors.firstName && (
                      <p className={`${victorMono.className} text-xs text-red-500 mt-1`}>{errors.firstName}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="lastName" className={`${victorMono.className} block text-sm font-medium text-[#0E1B2E]/70 mb-2`}>
                      Last Name <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#0E1B2E]/30" />
                      <input
                        type="text"
                        id="lastName"
                        name="lastName"
                        value={formData.lastName}
                        onChange={handleChange}
                        className={`
                          w-full pl-12 pr-4 py-3.5 bg-white border-2 rounded-xl
                          ${errors.lastName ? 'border-red-300 focus:border-red-500' : 'border-gray-200 focus:border-[#0E1B2E]'}
                          ${victorMono.className} text-[#0E1B2E] placeholder:text-[#0E1B2E]/30
                          focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 transition-all duration-200
                        `}
                        placeholder="Doe"
                      />
                    </div>
                    {errors.lastName && (
                      <p className={`${victorMono.className} text-xs text-red-500 mt-1`}>{errors.lastName}</p>
                    )}
                  </div>
                </div>

                {/* Email and Phone */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="email" className={`${victorMono.className} block text-sm font-medium text-[#0E1B2E]/70 mb-2`}>
                      Email Address <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#0E1B2E]/30" />
                      <input
                        type="email"
                        id="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        className={`
                          w-full pl-12 pr-4 py-3.5 bg-white border-2 rounded-xl
                          ${errors.email ? 'border-red-300 focus:border-red-500' : 'border-gray-200 focus:border-[#0E1B2E]'}
                          ${victorMono.className} text-[#0E1B2E] placeholder:text-[#0E1B2E]/30
                          focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 transition-all duration-200
                        `}
                        placeholder="john.doe@company.com"
                      />
                    </div>
                    {errors.email && (
                      <p className={`${victorMono.className} text-xs text-red-500 mt-1`}>{errors.email}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="phone" className={`${victorMono.className} block text-sm font-medium text-[#0E1B2E]/70 mb-2`}>
                      Phone Number
                    </label>
                    <div className="relative">
                      <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#0E1B2E]/30" />
                      <input
                        type="tel"
                        id="phone"
                        name="phone"
                        value={formData.phone}
                        onChange={handleChange}
                        className={`
                          w-full pl-12 pr-4 py-3.5 bg-white border-2 rounded-xl
                          border-gray-200 focus:border-[#0E1B2E]
                          ${victorMono.className} text-[#0E1B2E] placeholder:text-[#0E1B2E]/30
                          focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 transition-all duration-200
                        `}
                        placeholder="+1 (555) 000-0000"
                      />
                    </div>
                  </div>
                </div>

                {/* Company and Job Title */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="company" className={`${victorMono.className} block text-sm font-medium text-[#0E1B2E]/70 mb-2`}>
                      Company Name <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <Building2 className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#0E1B2E]/30" />
                      <input
                        type="text"
                        id="company"
                        name="company"
                        value={formData.company}
                        onChange={handleChange}
                        className={`
                          w-full pl-12 pr-4 py-3.5 bg-white border-2 rounded-xl
                          ${errors.company ? 'border-red-300 focus:border-red-500' : 'border-gray-200 focus:border-[#0E1B2E]'}
                          ${victorMono.className} text-[#0E1B2E] placeholder:text-[#0E1B2E]/30
                          focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 transition-all duration-200
                        `}
                        placeholder="Acme Inc."
                      />
                    </div>
                    {errors.company && (
                      <p className={`${victorMono.className} text-xs text-red-500 mt-1`}>{errors.company}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="jobTitle" className={`${victorMono.className} block text-sm font-medium text-[#0E1B2E]/70 mb-2`}>
                      Job Title <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <Briefcase className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#0E1B2E]/30" />
                      <input
                        type="text"
                        id="jobTitle"
                        name="jobTitle"
                        value={formData.jobTitle}
                        onChange={handleChange}
                        className={`
                          w-full pl-12 pr-4 py-3.5 bg-white border-2 rounded-xl
                          ${errors.jobTitle ? 'border-red-300 focus:border-red-500' : 'border-gray-200 focus:border-[#0E1B2E]'}
                          ${victorMono.className} text-[#0E1B2E] placeholder:text-[#0E1B2E]/30
                          focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 transition-all duration-200
                        `}
                        placeholder="Engineering Manager"
                      />
                    </div>
                    {errors.jobTitle && (
                      <p className={`${victorMono.className} text-xs text-red-500 mt-1`}>{errors.jobTitle}</p>
                    )}
                  </div>
                </div>

                {/* Company Size and Country */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="companySize" className={`${victorMono.className} block text-sm font-medium text-[#0E1B2E]/70 mb-2`}>
                      Company Size <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <Users className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#0E1B2E]/30 z-10" />
                      <select
                        id="companySize"
                        name="companySize"
                        value={formData.companySize}
                        onChange={handleChange}
                        className={`
                          w-full pl-12 pr-4 py-3.5 bg-white border-2 rounded-xl appearance-none
                          ${errors.companySize ? 'border-red-300 focus:border-red-500' : 'border-gray-200 focus:border-[#0E1B2E]'}
                          ${victorMono.className} text-[#0E1B2E]
                          focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 transition-all duration-200 cursor-pointer
                        `}
                      >
                        <option value="">Select company size</option>
                        {companySizes.map(size => (
                          <option key={size} value={size}>{size}</option>
                        ))}
                      </select>
                      <ArrowRight className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#0E1B2E]/30 rotate-90 pointer-events-none" />
                    </div>
                    {errors.companySize && (
                      <p className={`${victorMono.className} text-xs text-red-500 mt-1`}>{errors.companySize}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="country" className={`${victorMono.className} block text-sm font-medium text-[#0E1B2E]/70 mb-2`}>
                      Country <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#0E1B2E]/30" />
                      <input
                        type="text"
                        id="country"
                        name="country"
                        value={formData.country}
                        onChange={handleChange}
                        className={`
                          w-full pl-12 pr-4 py-3.5 bg-white border-2 rounded-xl
                          ${errors.country ? 'border-red-300 focus:border-red-500' : 'border-gray-200 focus:border-[#0E1B2E]'}
                          ${victorMono.className} text-[#0E1B2E] placeholder:text-[#0E1B2E]/30
                          focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 transition-all duration-200
                        `}
                        placeholder="United States"
                      />
                    </div>
                    {errors.country && (
                      <p className={`${victorMono.className} text-xs text-red-500 mt-1`}>{errors.country}</p>
                    )}
                  </div>
                </div>

                {/* Preferred Date */}
                <div>
                  <label htmlFor="preferredDate" className={`${victorMono.className} block text-sm font-medium text-[#0E1B2E]/70 mb-2`}>
                    Preferred Demo Date
                  </label>
                  <div className="relative">
                    <Calendar className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#0E1B2E]/30" />
                    <input
                      type="date"
                      id="preferredDate"
                      name="preferredDate"
                      value={formData.preferredDate}
                      onChange={handleChange}
                      min={new Date().toISOString().split('T')[0]}
                      className={`
                        w-full pl-12 pr-4 py-3.5 bg-white border-2 rounded-xl
                        border-gray-200 focus:border-[#0E1B2E]
                        ${victorMono.className} text-[#0E1B2E] placeholder:text-[#0E1B2E]/30
                        focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 transition-all duration-200
                      `}
                    />
                  </div>
                </div>

                {/* Message */}
                <div>
                  <label htmlFor="message" className={`${victorMono.className} block text-sm font-medium text-[#0E1B2E]/70 mb-2`}>
                    Additional Message
                  </label>
                  <textarea
                    id="message"
                    name="message"
                    value={formData.message}
                    onChange={handleChange}
                    rows={5}
                    className={`
                      w-full px-4 py-3.5 bg-white border-2 rounded-xl resize-none
                      border-gray-200 focus:border-[#0E1B2E]
                      ${victorMono.className} text-[#0E1B2E] placeholder:text-[#0E1B2E]/30
                      focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 transition-all duration-200
                    `}
                    placeholder="Tell us about your use case, specific requirements, or any questions you have..."
                  />
                </div>

                {/* Submit Button */}
                <motion.button
                  type="submit"
                  disabled={isSubmitting}
                  whileHover={!isSubmitting ? { scale: 1.02 } : {}}
                  whileTap={!isSubmitting ? { scale: 0.98 } : {}}
                  className={`
                    w-full group relative inline-flex items-center justify-center gap-3
                    bg-[#0E1B2E] text-white px-8 py-4 rounded-xl
                    ${isSubmitting ? 'opacity-75 cursor-wait' : 'hover:bg-[#1a2f4d]'}
                    transition-all duration-300 shadow-xl shadow-[#0E1B2E]/10
                  `}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span className={`${firaCode.className} font-bold tracking-wide text-sm`}>
                        SUBMITTING...
                      </span>
                    </>
                  ) : (
                    <>
                      <span className={`${firaCode.className} font-bold tracking-wide text-sm`}>
                        SUBMIT REQUEST
                      </span>
                      <span className="w-px h-5 bg-white/20" />
                      <Send className="w-5 h-5 transition-transform duration-300 group-hover:translate-x-1" />
                    </>
                  )}
                </motion.button>
              </form>
            </motion.div>

            {/* Info Sidebar */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="lg:col-span-1"
            >
              <div className="sticky top-32 space-y-6">
                {/* What to Expect Card */}
                <div className="p-6 bg-white border-2 border-gray-200 rounded-2xl shadow-lg shadow-black/5">
                  <h3 className={`${firaCode.className} text-xl font-bold text-[#0E1B2E] mb-4`}>
                    What to Expect
                  </h3>
                  <ul className={`${victorMono.className} space-y-3 text-sm text-[#0E1B2E]/70`}>
                    <li className="flex items-start gap-3">
                      <CheckCircle2 className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
                      <span>30-minute personalized demo</span>
                    </li>
                    <li className="flex items-start gap-3">
                      <CheckCircle2 className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
                      <span>Live product walkthrough</span>
                    </li>
                    <li className="flex items-start gap-3">
                      <CheckCircle2 className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
                      <span>Q&A session with our team</span>
                    </li>
                    <li className="flex items-start gap-3">
                      <CheckCircle2 className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
                      <span>Custom solution discussion</span>
                    </li>
                  </ul>
                </div>

                {/* Contact Info Card */}
                <div className="p-6 bg-[#0E1B2E] text-white rounded-2xl shadow-xl shadow-[#0E1B2E]/20">
                  <h3 className={`${firaCode.className} text-xl font-bold mb-4`}>
                    Need Immediate Help?
                  </h3>
                  <p className={`${victorMono.className} text-sm text-white/70 mb-4`}>
                    Our sales team is here to assist you. Reach out directly for faster response.
                  </p>
                  <div className="space-y-3">
                    <a 
                      href="mailto:sales@smarix.ai" 
                      className={`${victorMono.className} flex items-center gap-3 text-sm text-white/90 hover:text-white transition-colors`}
                    >
                      <Mail className="w-4 h-4" />
                      sales@smarix.ai
                    </a>
                    <a 
                      href="tel:+1234567890" 
                      className={`${victorMono.className} flex items-center gap-3 text-sm text-white/90 hover:text-white transition-colors`}
                    >
                      <Phone className="w-4 h-4" />
                      +1 (555) 123-4567
                    </a>
                  </div>
                </div>

                {/* Trust Indicators */}
                <div className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-100 rounded-2xl">
                  <div className="text-center">
                    <div className={`${firaCode.className} text-3xl font-bold text-[#0E1B2E] mb-1`}>
                      24hrs
                    </div>
                    <p className={`${victorMono.className} text-xs text-[#0E1B2E]/70`}>
                      Average response time
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>

      <Footer />
    </main>
  );
}

