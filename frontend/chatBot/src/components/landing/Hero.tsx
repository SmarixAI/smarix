'use client';

import React, { useRef, useState, useEffect } from 'react';
import { motion, useScroll, useTransform, useSpring } from 'framer-motion';
import { ArrowUpRight } from 'lucide-react';
import { Victor_Mono, Fira_Code } from 'next/font/google';

const victorMono = Victor_Mono({
  weight: ["400", "500", "700"],
  subsets: ["latin"],
  display: "swap",
});

const firaCode = Fira_Code({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  display: "swap",
});

const TypewriterLoop = () => {
  const words = ["Onboarding.", "Offboarding.", "AI Chatbot.", "Analytics."];
  const [text, setText] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [loopNum, setLoopNum] = useState(0);
  const [typingSpeed, setTypingSpeed] = useState(150);

  useEffect(() => {
    const handleType = () => {
      const i = loopNum % words.length;
      const fullText = words[i];

      setText(isDeleting 
        ? fullText.substring(0, text.length - 1) 
        : fullText.substring(0, text.length + 1)
      );

      setTypingSpeed(isDeleting ? 80 : 150);

      if (!isDeleting && text === fullText) {
        setTimeout(() => setIsDeleting(true), 1500);
      } else if (isDeleting && text === "") {
        setIsDeleting(false);
        setLoopNum(loopNum + 1);
      }
    };

    const timer = setTimeout(handleType, typingSpeed);
    return () => clearTimeout(timer);
  }, [text, isDeleting, loopNum, typingSpeed, words]);

  return (
    <div className="flex items-center justify-center h-full w-full bg-white">
      <h2 className={`${firaCode.className} text-4xl md:text-5xl lg:text-6xl font-bold text-[#0E1B2E] tracking-tight`}>
        {text}
        <span className="animate-pulse text-blue-500 ml-1">|</span>
      </h2>
    </div>
  );
};

export const Hero = () => {
  const containerRef = useRef(null);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end start"],
  });

  const springConfig = { stiffness: 100, damping: 30, restDelta: 0.001 };

  const yTextRaw = useTransform(scrollYProgress, [0, 1], [0, -150]);
  const yVisualRaw = useTransform(scrollYProgress, [0, 1], [0, 100]);
  const scaleVisualRaw = useTransform(scrollYProgress, [0, 1], [1, 0.95]);
  const yGridRaw = useTransform(scrollYProgress, [0, 1], [0, -50]);

  const yText = useSpring(yTextRaw, springConfig);
  const yVisual = useSpring(yVisualRaw, springConfig);
  const scaleVisual = useSpring(scaleVisualRaw, springConfig);
  const yGrid = useSpring(yGridRaw, springConfig);

  return (
    <section
      ref={containerRef}
      className="relative w-full h-screen pt-54 pb-24 px-6 bg-[#FAFAFA] text-[#0E1B2E] overflow-hidden border-b border-gray-200 perspective-1000"
    >
      <motion.div 
        style={{ y: yGrid }}
        className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" 
      />

      <div className="relative max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-16 lg:gap-30 items-center">
        
        <motion.div
          style={{ y: yText }}
          initial={{ opacity: 0, y: 60 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }} 
          className="flex flex-col gap-10 relative z-10"
        >
          <h1
            className={`${firaCode.className} text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.1] text-[#0E1B2E]`}
          >
            Transfer, retain, and operationalize your company’s knowledge.
          </h1>

          <p
            className={`${victorMono.className} text-xl text-[#0E1B2E]/70 leading-relaxed max-w-xl`}
          >
            AI-powered onboarding and offboarding that understands your codebase
            — accelerating ramp-up while preserving tribal knowledge.
          </p>

          <div className="flex items-center gap-6">
            <button className="group relative inline-flex items-center justify-center gap-3 bg-[#0E1B2E] text-white pl-6 pr-4 py-4 rounded-none hover:bg-[#1a2f4d] transition-all duration-300 shadow-xl shadow-blue-900/10">
              <span
                className={`${firaCode.className} font-bold tracking-wide text-sm`}
              >
                TRY OUR PRODUCT
              </span>
              <span className="w-px h-5 bg-white/20" />
              <ArrowUpRight className="w-5 h-5 transition-transform duration-300 group-hover:-translate-y-1 group-hover:translate-x-1" />
            </button>

            <button
              className={`${firaCode.className} text-sm font-bold text-[#0E1B2E] hover:text-blue-600 transition-colors underline decoration-gray-300 underline-offset-4 hover:decoration-blue-600`}
            >
              View Documentation
            </button>
          </div>
        </motion.div>

        <motion.div
          style={{ y: yVisual, scale: scaleVisual }}
          initial={{ opacity: 0, rotateX: 10, y: 100 }}
          animate={{ opacity: 1, rotateX: 0, y: 0 }}
          transition={{ duration: 1.2, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="relative perspective-origin-center"
        >
          <div className="relative aspect-[4/3] w-full overflow-hidden bg-white shadow-2xl shadow-[#0E1B2E]/10 border border-gray-200 flex flex-col will-change-transform">
            
            <div className="h-8 bg-gray-50 border-b border-gray-200 flex items-center px-4 gap-2 z-20 shrink-0">
              <div className="w-3 h-3 rounded-full bg-red-400/80" />
              <div className="w-3 h-3 rounded-full bg-yellow-400/80" />
              <div className="w-3 h-3 rounded-full bg-green-400/80" />
              <div className={`${victorMono.className} ml-4 text-[10px] text-gray-400 font-medium`}>
                smarix — v1.0.0
              </div>
            </div>

            <div className="relative flex-1 w-full bg-[#FAFAFA] flex flex-col items-center justify-center p-8">
              <TypewriterLoop />
            </div>
            
          </div>

          <div className="absolute -bottom-6 -right-6 w-full h-full border-2 border-[#0E1B2E]/5 -z-10" />
        </motion.div>
      </div>
    </section>
  );
};