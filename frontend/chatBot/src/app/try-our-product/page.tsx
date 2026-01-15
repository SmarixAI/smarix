'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { Navbar } from '@/components/landing/Navbar';
import { 
  User, 
  Building2, 
  Briefcase, 
  Mail, 
  Phone, 
  MessageSquare, 
  CheckCircle2, 
  Loader2,
  Send,
  Sparkles,
  Home
} from 'lucide-react';
import { Fira_Code, Victor_Mono } from 'next/font/google';

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

export default function ContactPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    name: '',
    company: '',
    role: '',
    email: '',
    phone: '',
    reason: ''
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    // Simulate network request
    setTimeout(() => {
      setIsSubmitting(false);
      setIsSubmitted(true);
    }, 1500);
  };

  return (
    <main className="min-h-screen bg-white text-[#0E1B2E] selection:bg-[#0E1B2E] selection:text-white overflow-hidden relative font-sans">

      <div className="flex flex-col lg:flex-row min-h-screen">
        
        {/* Left Section: Form */}
        <div className="w-full lg:w-1/2 p-6 lg:p-12 xl:p-20 flex flex-col justify-center relative z-10">
          <AnimatePresence mode="wait">
            {!isSubmitted ? (
              <motion.div
                key="form"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.5 }}
                className="max-w-xl mx-auto w-full"
              >
                <div className="mb-10">
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="flex items-center gap-2 mb-4"
                  >
                    <span className="w-8 h-[2px] bg-[#0E1B2E]"></span>
                    <span className={`${firaCode.className} text-[#0E1B2E] font-semibold tracking-wider text-sm`}>GET IN TOUCH</span>
                  </motion.div>
                  <h1 className={`${firaCode.className} text-4xl lg:text-5xl font-bold text-[#0E1B2E] mb-4`}>
                    Let's Build the Future of Work.
                  </h1>
                  <p className={`${victorMono.className} text-[#0E1B2E]/60 text-lg`}>
                    Fill in your details below. We are ready to streamline your enterprise knowledge.
                  </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    <div className="space-y-2">
                      <label className={`${firaCode.className} text-xs font-bold text-[#0E1B2E]/70 uppercase tracking-wide`}>Full Name</label>
                      <div className="relative group">
                        <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#0E1B2E]/40 group-focus-within:text-[#0E1B2E] transition-colors" />
                        <input
                          type="text"
                          name="name"
                          required
                          value={formData.name}
                          onChange={handleInputChange}
                          className={`${victorMono.className} w-full bg-[#FAFAFA] border border-[#0E1B2E]/10 rounded-xl py-3.5 pl-11 pr-4 focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 focus:border-[#0E1B2E] transition-all`}
                          placeholder="John Doe"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <label className={`${firaCode.className} text-xs font-bold text-[#0E1B2E]/70 uppercase tracking-wide`}>Company Name</label>
                      <div className="relative group">
                        <Building2 className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#0E1B2E]/40 group-focus-within:text-[#0E1B2E] transition-colors" />
                        <input
                          type="text"
                          name="company"
                          required
                          value={formData.company}
                          onChange={handleInputChange}
                          className={`${victorMono.className} w-full bg-[#FAFAFA] border border-[#0E1B2E]/10 rounded-xl py-3.5 pl-11 pr-4 focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 focus:border-[#0E1B2E] transition-all`}
                          placeholder="Acme Inc."
                        />
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    <div className="space-y-2">
                      <label className={`${firaCode.className} text-xs font-bold text-[#0E1B2E]/70 uppercase tracking-wide`}>Current Role</label>
                      <div className="relative group">
                        <Briefcase className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#0E1B2E]/40 group-focus-within:text-[#0E1B2E] transition-colors" />
                        <input
                          type="text"
                          name="role"
                          required
                          value={formData.role}
                          onChange={handleInputChange}
                          className={`${victorMono.className} w-full bg-[#FAFAFA] border border-[#0E1B2E]/10 rounded-xl py-3.5 pl-11 pr-4 focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 focus:border-[#0E1B2E] transition-all`}
                          placeholder="HR Manager"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <label className={`${firaCode.className} text-xs font-bold text-[#0E1B2E]/70 uppercase tracking-wide`}>Phone Number</label>
                      <div className="relative group">
                        <Phone className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#0E1B2E]/40 group-focus-within:text-[#0E1B2E] transition-colors" />
                        <input
                          type="tel"
                          name="phone"
                          required
                          value={formData.phone}
                          onChange={handleInputChange}
                          className={`${victorMono.className} w-full bg-[#FAFAFA] border border-[#0E1B2E]/10 rounded-xl py-3.5 pl-11 pr-4 focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 focus:border-[#0E1B2E] transition-all`}
                          placeholder="+1 (555) 000-0000"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className={`${firaCode.className} text-xs font-bold text-[#0E1B2E]/70 uppercase tracking-wide`}>Work Email</label>
                    <div className="relative group">
                      <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#0E1B2E]/40 group-focus-within:text-[#0E1B2E] transition-colors" />
                      <input
                        type="email"
                        name="email"
                        required
                        value={formData.email}
                        onChange={handleInputChange}
                        className={`${victorMono.className} w-full bg-[#FAFAFA] border border-[#0E1B2E]/10 rounded-xl py-3.5 pl-11 pr-4 focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 focus:border-[#0E1B2E] transition-all`}
                        placeholder="john@company.com"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className={`${firaCode.className} text-xs font-bold text-[#0E1B2E]/70 uppercase tracking-wide`}>Reason for Contact</label>
                    <div className="relative group">
                      <MessageSquare className="absolute left-4 top-5 w-4 h-4 text-[#0E1B2E]/40 group-focus-within:text-[#0E1B2E] transition-colors" />
                      <textarea
                        name="reason"
                        required
                        rows={3}
                        value={formData.reason}
                        onChange={handleInputChange}
                        className={`${victorMono.className} w-full bg-[#FAFAFA] border border-[#0E1B2E]/10 rounded-xl py-3.5 pl-11 pr-4 focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 focus:border-[#0E1B2E] transition-all resize-none`}
                        placeholder="I'm interested in automating our offboarding process..."
                      />
                    </div>
                  </div>

                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    disabled={isSubmitting}
                    className={`
                      ${firaCode.className} w-full py-4 bg-[#0E1B2E] text-white rounded-xl
                      font-semibold text-lg flex items-center justify-center gap-3
                      shadow-xl shadow-[#0E1B2E]/20 hover:shadow-2xl hover:shadow-[#0E1B2E]/30
                      transition-all duration-300 disabled:opacity-70 disabled:cursor-not-allowed
                    `}
                  >
                    {isSubmitting ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <>
                        Submit Request <Send className="w-4 h-4" />
                      </>
                    )}
                  </motion.button>
                </form>
              </motion.div>
            ) : (
              <motion.div
                key="success"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, type: "spring" }}
                className="max-w-xl mx-auto w-full bg-[#FAFAFA] border border-[#0E1B2E]/5 p-12 rounded-3xl text-center shadow-2xl shadow-[#0E1B2E]/5"
              >
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
                  className="w-24 h-24 bg-[#0E1B2E] rounded-full flex items-center justify-center mx-auto mb-8 shadow-xl shadow-[#0E1B2E]/20"
                >
                  <CheckCircle2 className="w-10 h-10 text-white" />
                </motion.div>
                
                <h2 className={`${firaCode.className} text-3xl font-bold text-[#0E1B2E] mb-4`}>
                  Request Received!
                </h2>
                
                <p className={`${victorMono.className} text-[#0E1B2E]/70 text-lg mb-8 leading-relaxed`}>
                  Thank you for your interest in Smarix. Your inquiry has been securely registered in our system. A senior executive will review your requirements and reach out to you shortly to discuss the next steps.
                </p>
                
                <div className="p-4 bg-white border border-[#0E1B2E]/10 rounded-xl inline-block mb-10">
                  <p className={`${firaCode.className} text-xs text-[#0E1B2E]/50 font-bold uppercase tracking-wider`}>Reference ID</p>
                  <p className={`${victorMono.className} text-[#0E1B2E] font-bold mt-1`}>SMX-{Math.floor(Math.random() * 100000)}</p>
                </div>

                <motion.button
                  onClick={() => router.push('/landing')}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className={`
                    ${firaCode.className} w-full py-4 bg-[#0E1B2E] text-white rounded-xl
                    font-semibold text-base flex items-center justify-center gap-2
                    shadow-lg shadow-[#0E1B2E]/10 hover:shadow-xl hover:shadow-[#0E1B2E]/20
                    transition-all duration-300
                  `}
                >
                  <Home className="w-5 h-5" />
                  Back to Home
                </motion.button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Right Section: Tech Visual / Lottie Simulation */}
        <div className="hidden lg:flex w-1/2 bg-[#0E1B2E] relative overflow-hidden items-center justify-center">
          {/* Animated Background Mesh */}
          <div className="absolute inset-0 opacity-20">
             <div className="absolute top-0 left-0 w-full h-full bg-[linear-gradient(rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:50px_50px]" />
          </div>

          <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-blue-500/20 rounded-full blur-[120px]" />
          <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-purple-500/20 rounded-full blur-[120px]" />

          {/* Central Tech Animation */}
          <div className="relative w-[600px] h-[600px] flex items-center justify-center">
            
            {/* Orbital Rings */}
            {[1, 2, 3].map((ring, i) => (
              <motion.div
                key={i}
                animate={{ rotate: 360 }}
                transition={{ 
                  duration: 20 + (i * 10), 
                  repeat: Infinity, 
                  ease: "linear",
                  delay: i * 2 
                }}
                className={`absolute rounded-full border border-white/${10 - (i * 2)}`}
                style={{
                  width: `${300 + (i * 100)}px`,
                  height: `${300 + (i * 100)}px`,
                }}
              >
                <motion.div 
                  className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-[0_0_15px_rgba(255,255,255,0.5)]" 
                />
              </motion.div>
            ))}

            {/* Central Core */}
            <motion.div
              animate={{ 
                scale: [1, 1.1, 1],
                boxShadow: [
                  "0 0 20px rgba(255,255,255,0.1)", 
                  "0 0 50px rgba(255,255,255,0.3)", 
                  "0 0 20px rgba(255,255,255,0.1)"
                ]
              }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              className="w-32 h-32 bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-md rounded-full border border-white/20 flex items-center justify-center relative z-20"
            >
              <Sparkles className="w-12 h-12 text-white/80" />
            </motion.div>

            {/* Floating Data Cards */}
            <motion.div
              animate={{ y: [-15, 15, -15] }}
              transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
              className="absolute top-20 right-20 bg-white/10 backdrop-blur-xl border border-white/10 p-4 rounded-xl z-30 w-48"
            >
              <div className="flex items-center gap-3 mb-2">
                <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center">
                  <CheckCircle2 className="w-4 h-4 text-green-400" />
                </div>
                <div className="h-2 w-20 bg-white/20 rounded-full" />
              </div>
              <div className="h-2 w-full bg-white/10 rounded-full mb-2" />
              <div className="h-2 w-2/3 bg-white/10 rounded-full" />
            </motion.div>

            <motion.div
              animate={{ y: [20, -20, 20] }}
              transition={{ duration: 7, repeat: Infinity, ease: "easeInOut", delay: 1 }}
              className="absolute bottom-32 left-10 bg-white/10 backdrop-blur-xl border border-white/10 p-4 rounded-xl z-30 w-40"
            >
              <div className="flex justify-between items-end h-12 gap-1">
                {[40, 70, 50, 90, 60].map((h, i) => (
                  <motion.div
                    key={i}
                    animate={{ height: [`${h}%`, `${h - 20}%`, `${h}%`] }}
                    transition={{ duration: 2, repeat: Infinity, delay: i * 0.2 }}
                    className="w-full bg-blue-400/50 rounded-t-sm"
                  />
                ))}
              </div>
            </motion.div>

            {/* Connecting Lines (Simulated SVG) */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-30">
               <motion.line 
                  x1="50%" y1="50%" x2="80%" y2="20%" 
                  stroke="white" strokeWidth="1" strokeDasharray="5,5"
                  animate={{ strokeDashoffset: [0, 20] }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
               />
               <motion.line 
                  x1="50%" y1="50%" x2="20%" y2="70%" 
                  stroke="white" strokeWidth="1" strokeDasharray="5,5"
                  animate={{ strokeDashoffset: [0, -20] }}
                  transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
               />
            </svg>
          </div>
        </div>
      </div>
    </main>
  );
}