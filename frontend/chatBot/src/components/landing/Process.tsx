'use client';

import React, { useRef } from 'react';
import { motion, useScroll, useTransform, useSpring, useInView } from 'framer-motion';
import Image from 'next/image';
import { Victor_Mono, Fira_Code } from 'next/font/google';

const firaCode = Fira_Code({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  display: "swap",
});

const victorMono = Victor_Mono({
  weight: ["400", "500"],
  subsets: ["latin"],
  display: "swap",
});

export const Process = () => {
  const containerRef = useRef(null);
  const isInView = useInView(containerRef, { once: true, amount: 0.2 });
  
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"]
  });

  const springConfig = { stiffness: 100, damping: 30, restDelta: 0.001 };
  
  const yLogoRaw = useTransform(scrollYProgress, [0, 0.5, 1], [-80, 0, 80]);
  const yLogo = useSpring(yLogoRaw, springConfig);
  
  const yTextRaw = useTransform(scrollYProgress, [0, 1], [80, -80]);
  const yText = useSpring(yTextRaw, springConfig);

  const steps = [
    {
      id: "01",
      title: "Onboard faster",
      desc: "Automate access, setup environments, and context-load new hires instantly.",
    },
    {
      id: "02",
      title: "Offboard smarter",
      desc: "Securely revoke access and capture tribal knowledge before it walks out the door.",
    },
    {
      id: "03",
      title: "Keep knowledge forever",
      desc: "Turn ephemeral conversations and code commits into a persistent institutional brain.",
    },
  ];

  return (
    <section 
      ref={containerRef} 
      className="relative w-full h-screen pt-24 px-6 bg-[#F5F8FF] text-[#0E1B2E] overflow-hidden"
    >
      <div className="absolute inset-0 opacity-60">
          <motion.div 
            animate={{ 
              scale: [1, 1.1, 1],
              opacity: [0.4, 0.6, 0.4]
            }}
            transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
            className="absolute -top-[10%] -left-[10%] w-[70vw] h-[70vw] bg-gradient-to-br from-blue-100 to-indigo-100 rounded-full blur-[100px] mix-blend-multiply"
          />
          <motion.div 
            animate={{ 
              scale: [1, 1.2, 1],
              x: [-30, 30, -30],
              opacity: [0.3, 0.5, 0.3]
            }}
            transition={{ duration: 12, repeat: Infinity, ease: "easeInOut", delay: 2 }}
            className="absolute top-[10%] right-[0%] w-[50vw] h-[50vw] bg-gradient-to-bl from-cyan-100 to-blue-200 rounded-full blur-[80px] mix-blend-multiply"
          />
          <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-30 brightness-100 contrast-150 mix-blend-overlay" />
      </div>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-0 items-center relative z-10">
        
        <motion.div 
          style={{ y: yText }}
          className="lg:col-span-4 flex flex-col gap-6"
        >
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
            <h2 className="text-4xl md:text-5xl lg:text-6xl font-tahoma font-bold leading-[1] tracking-tight text-[#0E1B2E]">
              Designed to turn <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-700 via-blue-600 to-cyan-600">complexity</span> into clarity.
            </h2>
            <p className={`${victorMono.className} text-base text-[#0E1B2E]/70 max-w-sm leading-relaxed mt-5 font-medium`}>
              A complete lifecycle engine that synchronizes your engineering team's knowledge graph.
            </p>
          </motion.div>
        </motion.div>

        <div className="lg:col-span-3 relative h-[600px] hidden lg:flex items-center justify-center">
           
           <motion.div 
             style={{ y: yLogo }}
             className="absolute left-0 top-1/2 -translate-y-1/2 z-20 w-20 h-20 bg-white/60 backdrop-blur-xl rounded-xl shadow-[0_20px_40px_-15px_rgba(37,99,235,0.2)] border border-white/80 flex items-center justify-center p-4 overflow-hidden"
           >
              <Image 
                src="/logo.png" 
                alt="SmariX Core" 
                width={48} 
                height={48} 
                className="object-contain rounded-xl"
              />
              <div className="absolute inset-0 rounded-xl ring-1 ring-blue-500/10" />
           </motion.div>

           <svg className="w-full h-full visible overflow-visible">
              <defs>
                <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#0E1B2E" stopOpacity="0" />
                  <stop offset="50%" stopColor="#2563EB" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#3B82F6" stopOpacity="0" />
                </linearGradient>
                <filter id="glow">
                  <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                  <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                  </feMerge>
                </filter>
              </defs>

              {steps.map((_, i) => {
                const yEnd = 100 + (i * 200); 
                const pathD = `M 40 300 C 150 300, 150 ${yEnd}, 280 ${yEnd}`;
                
                return (
                  <g key={i}>
                    <motion.path
                      d={pathD}
                      fill="none"
                      stroke="#E2E8F0"
                      strokeWidth="2"
                    />

                    <motion.path
                      d={pathD}
                      fill="none"
                      stroke="url(#lineGradient)"
                      strokeWidth="3"
                      strokeLinecap="round"
                      initial={{ pathLength: 0, opacity: 0 }}
                      animate={isInView ? { pathLength: 1, opacity: 1 } : {}}
                      transition={{ duration: 1.2, delay: 0.2 + (i * 0.1), ease: "circOut" }}
                    />

                    <motion.circle
                      r="4"
                      fill="#3B82F6"
                      filter="url(#glow)"
                      initial={{ offsetDistance: "0%" }}
                      animate={isInView ? { offsetDistance: "100%" } : {}}
                      style={{ offsetPath: `path("${pathD}")` }}
                      transition={{ 
                        duration: 2.5, 
                        repeat: Infinity, 
                        repeatDelay: 0.5,
                        ease: "easeInOut",
                        delay: i * 0.8
                      }}
                    />
                  </g>
                );
              })}
           </svg>
        </div>

        <div className="lg:col-span-5 flex flex-col justify-center h-full gap-16 py-10">
          {steps.map((step, index) => (
            <motion.div
              key={step.id}
              initial={{ opacity: 0, x: 30 }}
              animate={isInView ? { opacity: 1, x: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.4 + (index * 0.15), ease: "easeOut" }}
              className="group relative pl-8"
            >
              <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-blue-100 group-hover:bg-blue-600 transition-colors duration-500">
                <div className="absolute top-0 left-0 w-full h-full bg-blue-600 scale-y-0 group-hover:scale-y-100 origin-top transition-transform duration-500" />
              </div>
              
              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-3">
                  <span className={`${firaCode.className} text-4xl font-bold text-blue-200 group-hover:text-blue-600 transition-colors duration-300`}>
                    .{step.id}
                  </span>
                  <h3 className="text-2xl md:text-3xl font-tahoma font-bold text-[#0E1B2E]">
                    {step.title}
                  </h3>
                </div>
                
                <p className="text-lg text-[#0E1B2E]/60 font-body leading-relaxed max-w-md mt-1 group-hover:text-[#0E1B2E] transition-colors">
                  {step.desc}
                </p>
              </div>
            </motion.div>
          ))}
          
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 1 }}
            className="pl-8 pt-2"
          >
            <button className="group relative overflow-hidden rounded-none bg-[#0E1B2E] px-8 py-4 text-white transition-all hover:bg-blue-700 hover:shadow-lg hover:shadow-blue-900/20">
              <span className={`${firaCode.className} relative z-10 text-xs font-bold tracking-widest uppercase flex items-center gap-2`}>
                Start Integration 
                <svg className="w-4 h-4 transition-transform group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </span>
            </button>
          </motion.div>
        </div>

      </div>
    </section>
  );
};