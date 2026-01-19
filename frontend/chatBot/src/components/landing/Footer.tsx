'use client';

import React, { useRef } from 'react';
import { motion, useScroll, useTransform, useSpring } from 'framer-motion';
import { ArrowUpRight, Github, Twitter, Linkedin, Sparkles } from 'lucide-react';
import { Space_Grotesk, JetBrains_Mono, Fira_Code } from 'next/font/google';
import Image from 'next/image';
import Link from 'next/link';

const spaceGrotesk = Space_Grotesk({ subsets: ['latin'] });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], weight: ['800'] });
const firaCode = Fira_Code({ subsets: ['latin'] });

export const Footer = () => {
  const containerRef = useRef(null);
  
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end end"]
  });

  const smoothProgress = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001
  });

  const yText = useTransform(smoothProgress, [0.5, 1], [150, 0]);
  const opacityText = useTransform(smoothProgress, [0.6, 1], [0, 1]);

  return (
    <footer 
      ref={containerRef} 
      className="relative w-full bg-[#0E1B2E] text-white overflow-hidden pt-32 pb-0"
    >
      <div className="absolute top-20 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse" />
      
      <div className="absolute top-0 left-0 w-full h-40 bg-gradient-to-b from-white/5 to-transparent pointer-events-none z-10" />

      <div className="relative z-20 max-w-[1400px] mx-auto px-8 flex flex-col justify-between">
        
        <div className="flex flex-col lg:flex-row justify-between items-start gap-12 mb-24">
          
          <div className="max-w-4xl relative z-20">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="mb-6 flex items-center gap-3"
            >
              <motion.div
                animate={{ 
                  rotate: [0, 360],
                  scale: [1, 1.2, 1]
                }}
                transition={{ 
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              >
                <Sparkles className="w-6 h-6 text-blue-400" />
              </motion.div>
              <span className={`${jetbrainsMono.className} text-xs text-blue-400 uppercase tracking-widest`}>
                Transform Your Workflow
              </span>
            </motion.div>

            <motion.h2 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className={`${spaceGrotesk.className} text-5xl md:text-6xl lg:text-7xl font-bold leading-[0.9] tracking-tight mb-12`}
            >
              Ready to integrate <br/>
              <span className="relative inline-block">
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400">
                  Smarix
                </span>
                <motion.span
                  className="absolute -bottom-2 left-0 w-full h-1 bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 rounded-full"
                  initial={{ scaleX: 0 }}
                  whileInView={{ scaleX: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.8, delay: 0.4 }}
                />
              </span> in your life?
            </motion.h2>

            <Link href="/request-demo">
              <motion.button 
                whileHover={{ scale: 1.02, x: 5 }}
                whileTap={{ scale: 0.98 }}
                className="group relative inline-flex items-center gap-5 bg-white text-[#0E1B2E] px-10 py-5 rounded-none transition-all duration-300 hover:bg-blue-50 overflow-hidden"
              >
                <motion.div
                  className="absolute inset-0 bg-gradient-to-r from-blue-400/20 to-purple-400/20"
                  initial={{ x: '-100%' }}
                  whileHover={{ x: '100%' }}
                  transition={{ duration: 0.6 }}
                />
                <span className={`${firaCode.className} font-bold tracking-wide text-base relative z-10`}>
                  REQUEST DEMO
                </span>
                <span className="w-px h-6 bg-[#0E1B2E]/20 relative z-10" />
                <ArrowUpRight className="w-6 h-6 transition-transform duration-300 group-hover:-translate-y-1 group-hover:translate-x-1 relative z-10" />
              </motion.button>
            </Link>
          </div>

          <div className="flex flex-col gap-6 text-right items-end relative z-20">
             <motion.div 
               animate={{ 
                 y: [0, -15, 0],
                 rotate: [0, 5, -5, 0]
               }}
               transition={{ 
                 duration: 6,
                 repeat: Infinity,
                 ease: "easeInOut"
               }}
               className="relative w-40 h-40 md:w-56 md:h-56"
             >
                <motion.div
                  className="absolute inset-0 rounded-[2rem] bg-gradient-to-br from-blue-400/20 to-purple-400/20"
                  animate={{ 
                    scale: [1, 1.1, 1],
                    opacity: [0.5, 0.8, 0.5]
                  }}
                  transition={{ 
                    duration: 3,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                />
                <div className="relative w-full h-full bg-white/5 rounded-[2rem] flex items-center justify-center border border-white/10 backdrop-blur-sm overflow-hidden">
                  <Image src="/logo.png" alt="Smarix Logo" width={120} height={120} className="object-contain w-28 h-28 md:w-40 md:h-40 rounded-[2rem]" />
                </div>
             </motion.div>
             <p className={`${jetbrainsMono.className} text-white/40 text-sm max-w-[240px] leading-relaxed text-right`}>
               Empowering engineering teams with AI-driven knowledge continuity.
             </p>
          </div>
        </div>

        <div className="relative z-30 mb-20">
           <motion.div 
             initial={{ scaleX: 0 }}
             whileInView={{ scaleX: 1 }}
             viewport={{ once: true }}
             transition={{ duration: 1.2, delay: 0.3 }}
             className="w-full h-px bg-gradient-to-r from-transparent via-white/20 to-transparent mb-12"
           />

           <div className="flex flex-col md:flex-row justify-between items-center gap-6 px-4">
              <div className="flex flex-col md:flex-row items-center gap-6">
                <p className={`${jetbrainsMono.className} text-[11px] text-white/30 uppercase tracking-wider`}>
                  © 2026 Smarix AI Inc. All rights reserved.
                </p>
              </div>
              
              <div className="flex items-center gap-4">
                <p className={`${jetbrainsMono.className} text-[11px] text-white/30 uppercase tracking-wider`}>
                  Built with <span className="text-red-400">❤️</span> in India
                </p>
              </div>
           </div>
        </div>

      </div>

      <div className="relative w-full h-[300px] overflow-hidden">
        <motion.div 
          style={{ y: yText, opacity: opacityText }}
          className="absolute top-0 left-0 w-full pointer-events-none select-none"
        >
          <svg viewBox="0 0 1600 400" className="w-full h-auto" preserveAspectRatio="xMidYMin slice">
            <defs>
              <linearGradient id="fadeGradient" x1="0%" y1="100%" x2="0%" y2="0%">
                <stop offset="0%" style={{ stopColor: '#E879F9', stopOpacity: 1 }} />
                <stop offset="30%" style={{ stopColor: '#C084FC', stopOpacity: 0.9 }} />
                <stop offset="60%" style={{ stopColor: '#A78BFA', stopOpacity: 0.6 }} />
                <stop offset="85%" style={{ stopColor: '#818CF8', stopOpacity: 0.3 }} />
                <stop offset="100%" style={{ stopColor: '#60A5FA', stopOpacity: 0 }} />
              </linearGradient>
              
              <linearGradient id="strokeGradient" x1="0%" y1="100%" x2="0%" y2="0%">
                <stop offset="0%" style={{ stopColor: '#FFFFFF', stopOpacity: 0.3 }} />
                <stop offset="50%" style={{ stopColor: '#FFFFFF', stopOpacity: 0.15 }} />
                <stop offset="100%" style={{ stopColor: '#FFFFFF', stopOpacity: 0 }} />
              </linearGradient>

              <filter id="subtleGlow">
                <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>
            
            <text 
              x="50%" 
              y="55%" 
              textAnchor="middle"
              dominantBaseline="middle"
              fontFamily="JetBrains Mono, monospace"
              fontWeight="800"
              style={{ 
                fontSize: '400px',
                fill: 'url(#fadeGradient)',
                filter: 'url(#subtleGlow)',
                letterSpacing: '-0.02em'
              }}
            >
              SMARIX
            </text>
            
            <text 
              x="50%" 
              y="55%" 
              textAnchor="middle"
              dominantBaseline="middle"
              fontFamily="JetBrains Mono, monospace"
              fontWeight="800"
              style={{ 
                fontSize: '400px',
                fill: 'transparent',
                stroke: 'url(#strokeGradient)',
                strokeWidth: '2px',
                letterSpacing: '-0.02em'
              }}
            >
              SMARIX
            </text>
          </svg>
        </motion.div>
        
        <div className="absolute inset-0 bg-gradient-to-b from-[#0E1B2E] via-[#0E1B2E]/50 to-transparent pointer-events-none" style={{ height: '40%' }} />
      </div>

    </footer>
  );
};