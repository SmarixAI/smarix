"use client";

import React, { useRef, useState, useEffect } from "react";
import { motion, useScroll, useTransform, useSpring } from "framer-motion";
import { ArrowUpRight } from "lucide-react";
import { Victor_Mono, Fira_Code } from "next/font/google";
import Link from "next/link";

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
  const words = ["Onboarding.", "Offboarding.", "AI Assistant."];
  const [text, setText] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [loopNum, setLoopNum] = useState(0);
  const [typingSpeed, setTypingSpeed] = useState(150);

  useEffect(() => {
    const handleType = () => {
      const i = loopNum % words.length;
      const fullText = words[i];

      setText(
        isDeleting
          ? fullText.substring(0, text.length - 1)
          : fullText.substring(0, text.length + 1),
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
    <div className="flex items-center justify-center h-full w-full bg-white px-2 text-center">
      <h2
        className={`${firaCode.className} text-2xl sm:text-3xl md:text-5xl lg:text-6xl font-bold text-[#0E1B2E] tracking-tight`}
      >
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
      className="relative w-full min-h-screen h-auto pt-32 pb-48 md:pt-40 md:pb-20 lg:pt-54 lg:pb-24 px-6 bg-[#FAFAFA] text-[#0E1B2E] overflow-hidden border-b border-gray-200 perspective-1000 flex flex-col justify-center"
    >
      <motion.div
        style={{ y: yGrid }}
        className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none"
      />

      <div className="relative max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-30 items-center">
        <motion.div
          style={{ y: yText }}
          initial={{ opacity: 0, y: 60 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
          className="flex flex-col gap-6 md:gap-10 relative z-10 text-center lg:text-left items-center lg:items-start"
        >
          <h1
            className={`${firaCode.className} text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.1] text-[#0E1B2E]`}
          >
            Transfer, retain, and operationalize your company’s knowledge.
          </h1>

          <p
            className={`${victorMono.className} text-base md:text-xl text-[#0E1B2E]/70 leading-relaxed max-w-xl`}
          >
            AI-powered onboarding and offboarding that understands your codebase
            accelerating developer productivity while preserving critical
            institutional knowledge.
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-6 w-full sm:w-auto">
            <Link
              href="/request-demo"
              className="group relative w-full sm:w-auto inline-flex items-center justify-center gap-3 bg-[#0E1B2E] text-white pl-6 pr-4 py-4 rounded-none hover:bg-[#1a2f4d] transition-all duration-300 shadow-xl shadow-blue-900/10"
            >
              <span
                className={`${firaCode.className} font-bold tracking-wide text-sm`}
              >
                REQUEST A DEMO
              </span>
              <span className="w-px h-5 bg-white/20" />
              <ArrowUpRight className="w-5 h-5 transition-transform duration-300 group-hover:-translate-y-1 group-hover:translate-x-1" />
            </Link>
          </div>
        </motion.div>

        <motion.div
          style={{ y: yVisual, scale: scaleVisual }}
          initial={{ opacity: 0, rotateX: 10, y: 100 }}
          animate={{ opacity: 1, rotateX: 0, y: 0 }}
          transition={{ duration: 1.2, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="relative perspective-origin-center w-full max-w-lg lg:max-w-none mx-auto"
        >
          <div className="relative aspect-[4/3] w-full overflow-hidden bg-white shadow-2xl shadow-[#0E1B2E]/10 border border-gray-200 flex flex-col will-change-transform">
            <div className="h-8 bg-gray-50 border-b border-gray-200 flex items-center px-4 gap-2 z-20 shrink-0">
              <div className="w-3 h-3 rounded-full bg-red-400/80" />
              <div className="w-3 h-3 rounded-full bg-yellow-400/80" />
              <div className="w-3 h-3 rounded-full bg-green-400/80" />
              <div
                className={`${victorMono.className} ml-4 text-[10px] text-gray-400 font-medium`}
              >
                smarix — v1.0.0
              </div>
            </div>

            <div className="relative flex-1 w-full bg-[#FAFAFA] flex flex-col items-center justify-center p-4 md:p-8">
              <TypewriterLoop />
            </div>
          </div>

          <div className="absolute -bottom-4 -right-4 md:-bottom-6 md:-right-6 w-full h-full border-2 border-[#0E1B2E]/5 -z-10" />
        </motion.div>
      </div>
    </section>
  );
};
