"use client";

import React, { useRef } from "react";
import { motion, useScroll, useTransform, useSpring } from "framer-motion";
import { ArrowUpRight, Sparkles } from "lucide-react";
import { Space_Grotesk, JetBrains_Mono, Fira_Code } from "next/font/google";
import Image from "next/image";
import Link from "next/link";

const spaceGrotesk = Space_Grotesk({ subsets: ["latin"] });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], weight: ["800"] });
const firaCode = Fira_Code({ subsets: ["latin"] });

export const Footer = () => {
  const containerRef = useRef(null);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end end"],
  });

  const smoothProgress = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001,
  });

  const yText = useTransform(smoothProgress, [0.5, 1], [150, 0]);
  const opacityText = useTransform(smoothProgress, [0.6, 1], [0, 1]);

  return (
    <footer
      ref={containerRef}
      className="relative w-full bg-[#0E1B2E] text-white overflow-hidden pt-16 sm:pt-24 md:pt-32 pb-0"
    >
      <div className="absolute top-10 sm:top-20 left-1/4 w-64 h-64 sm:w-96 sm:h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse" />

      <div className="absolute top-0 left-0 w-full h-20 sm:h-40 bg-gradient-to-b from-white/5 to-transparent pointer-events-none z-10" />

      <div className="relative z-20 max-w-[1400px] mx-auto px-4 sm:px-6 md:px-8 flex flex-col justify-between">
        <div className="flex flex-col lg:flex-row justify-between items-center lg:items-start gap-8 sm:gap-10 md:gap-12 mb-12 sm:mb-16 md:mb-24">
          <div className="max-w-4xl relative z-20 w-full flex flex-col items-center lg:items-start">
            <div className="mb-4 sm:mb-6 flex items-center justify-center lg:justify-start gap-2 sm:gap-3 w-full">
              <motion.div
                animate={{
                  rotate: [0, 360],
                  scale: [1, 1.2, 1],
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
              >
                <Sparkles className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400" />
              </motion.div>
              <span
                className={`${jetbrainsMono.className} text-[10px] sm:text-xs text-blue-400 uppercase tracking-widest`}
              >
                Transform Your Workflow
              </span>
            </div>

            <h2
              className={`${spaceGrotesk.className} text-3xl sm:text-4xl md:text-5xl lg:text-7xl font-bold leading-[1.1] sm:leading-[0.95] lg:leading-[0.9] tracking-tight mb-8 sm:mb-10 md:mb-12 text-center lg:text-left w-full`}
            >
              Ready to integrate <br />
              <span className="relative inline-block">
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400">
                  Smarix
                </span>
                <span className="absolute -bottom-1 sm:-bottom-2 left-0 w-full h-0.5 sm:h-1 bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 rounded-full" />
              </span>{" "}
              in your life?
            </h2>

            <div className="w-full flex justify-center lg:justify-start">
              <Link href="/request-demo" className="w-full sm:w-auto">
                <motion.button
                  whileHover={{ scale: 1.02, x: 5 }}
                  whileTap={{ scale: 0.98 }}
                  className="group relative inline-flex items-center gap-3 sm:gap-4 md:gap-5 bg-white text-[#0E1B2E] px-6 py-3 sm:px-8 sm:py-4 md:px-10 md:py-5 rounded-none transition-all duration-300 hover:bg-blue-50 overflow-hidden w-full sm:w-auto justify-center"
                >
                  <motion.div
                    className="absolute inset-0 bg-gradient-to-r from-blue-400/20 to-purple-400/20"
                    initial={{ x: "-100%" }}
                    whileHover={{ x: "100%" }}
                    transition={{ duration: 0.6 }}
                  />
                  <span
                    className={`${firaCode.className} font-bold tracking-wide text-sm sm:text-base relative z-10`}
                  >
                    REQUEST DEMO
                  </span>
                  <span className="w-px h-5 sm:h-6 bg-[#0E1B2E]/20 relative z-10" />
                  <ArrowUpRight className="w-5 h-5 sm:w-6 sm:h-6 transition-transform duration-300 group-hover:-translate-y-1 group-hover:translate-x-1 relative z-10" />
                </motion.button>
              </Link>
            </div>
          </div>

          <div className="flex flex-col gap-4 sm:gap-6 text-center lg:text-right items-center lg:items-end relative z-20 w-full lg:w-auto">
            <motion.div
              animate={{
                y: [0, -15, 0],
                rotate: [0, 5, -5, 0],
              }}
              transition={{
                duration: 6,
                repeat: Infinity,
                ease: "easeInOut",
              }}
              className="relative w-32 h-32 sm:w-40 sm:h-40 md:w-56 md:h-56"
            >
              <motion.div
                className="absolute inset-0 rounded-2xl sm:rounded-[2rem] bg-gradient-to-br from-blue-400/20 to-purple-400/20"
                animate={{
                  scale: [1, 1.1, 1],
                  opacity: [0.5, 0.8, 0.5],
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
              />
              <div className="relative w-full h-full bg-white/5 rounded-2xl sm:rounded-[2rem] flex items-center justify-center border border-white/10 backdrop-blur-sm overflow-hidden">
                <Image
                  src="/logo.png"
                  alt="Smarix Logo"
                  width={120}
                  height={120}
                  className="object-contain w-20 h-20 sm:w-28 sm:h-28 md:w-40 md:h-40 rounded-2xl sm:rounded-[2rem]"
                />
              </div>
            </motion.div>
            <p
              className={`${jetbrainsMono.className} text-white/40 text-xs sm:text-sm max-w-[200px] sm:max-w-[240px] leading-relaxed text-center lg:text-right`}
            >
              Empowering engineering teams with AI-driven knowledge continuity.
            </p>
          </div>
        </div>

        <div className="relative z-30 mb-8 sm:mb-12 md:mb-20">
          <div className="w-full h-px bg-gradient-to-r from-transparent via-white/20 to-transparent mb-6 sm:mb-8 md:mb-12" />

          <div className="flex flex-col md:flex-row justify-between items-center gap-4 sm:gap-6 px-0 sm:px-4">
            <div className="flex flex-col md:flex-row items-center gap-3 sm:gap-6">
              <p
                className={`${jetbrainsMono.className} text-[10px] sm:text-[11px] text-white/30 uppercase tracking-wider text-center`}
              >
                © 2026 Smarix AI Inc. All rights reserved.
              </p>
            </div>

            <div className="flex items-center gap-4">
              <p
                className={`${jetbrainsMono.className} text-[10px] sm:text-[11px] text-white/30 uppercase tracking-wider text-center`}
              >
                Built with <span className="text-red-400">❤️</span> in India
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="relative w-full h-[75px] sm:h-[100px] md:h-[130px] lg:h-[300px] overflow-hidden">
        <motion.div
          style={{ y: yText, opacity: opacityText }}
          className="absolute top-0 left-0 w-full pointer-events-none select-none will-change-transform"
        >
          <svg
            viewBox="0 0 1600 400"
            className="w-full h-auto"
            preserveAspectRatio="xMidYMin slice"
          >
            <defs>
              <linearGradient
                id="fadeGradient"
                x1="0%"
                y1="100%"
                x2="0%"
                y2="0%"
              >
                <stop
                  offset="0%"
                  style={{ stopColor: "#E879F9", stopOpacity: 1 }}
                />
                <stop
                  offset="30%"
                  style={{ stopColor: "#C084FC", stopOpacity: 0.9 }}
                />
                <stop
                  offset="60%"
                  style={{ stopColor: "#A78BFA", stopOpacity: 0.6 }}
                />
                <stop
                  offset="85%"
                  style={{ stopColor: "#818CF8", stopOpacity: 0.3 }}
                />
                <stop
                  offset="100%"
                  style={{ stopColor: "#60A5FA", stopOpacity: 0 }}
                />
              </linearGradient>

              <linearGradient
                id="strokeGradient"
                x1="0%"
                y1="100%"
                x2="0%"
                y2="0%"
              >
                <stop
                  offset="0%"
                  style={{ stopColor: "#FFFFFF", stopOpacity: 0.3 }}
                />
                <stop
                  offset="50%"
                  style={{ stopColor: "#FFFFFF", stopOpacity: 0.15 }}
                />
                <stop
                  offset="100%"
                  style={{ stopColor: "#FFFFFF", stopOpacity: 0 }}
                />
              </linearGradient>

              <filter id="subtleGlow">
                <feGaussianBlur stdDeviation="4" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
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
                fontSize: "400px",
                fill: "url(#fadeGradient)",
                filter: "url(#subtleGlow)",
                letterSpacing: "-0.02em",
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
                fontSize: "400px",
                fill: "transparent",
                stroke: "url(#strokeGradient)",
                strokeWidth: "2px",
                letterSpacing: "-0.02em",
              }}
            >
              SMARIX
            </text>
          </svg>
        </motion.div>

        <div
          className="absolute inset-0 bg-gradient-to-b from-[#0E1B2E] via-[#0E1B2E]/50 to-transparent pointer-events-none"
          style={{ height: "40%" }}
        />
      </div>
    </footer>
  );
};
