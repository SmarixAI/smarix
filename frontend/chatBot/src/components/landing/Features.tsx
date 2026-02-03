"use client";

import React, { useRef, useState, useEffect } from "react";
import {
  motion,
  useScroll,
  useTransform,
  AnimatePresence,
  useSpring,
} from "framer-motion";
import {
  Zap,
  Shield,
  Code2,
  Terminal,
  Cpu,
  Layout,
  GitBranch,
  Share2,
  Search,
  Bug,
} from "lucide-react";
import { Space_Grotesk, JetBrains_Mono } from "next/font/google";
import Image from "next/image";

const spaceGrotesk = Space_Grotesk({ subsets: ["latin"] });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"] });

const features = [
  {
    id: 0,
    tag: "Onboarding",
    title: "AI-Powered Onboarding",
    desc: "Turn complex codebases into guided learning journeys. Help developers understand your product, tech stack, and standards—faster.",
    image: "/onboarding-demo.gif",
    icon: Zap,
    color: "#3B82F6",
    bgGradient:
      "radial-gradient(circle at 0% 0%, rgba(59,130,246,0.15) 0%, transparent 50%)",
    points: [
      {
        icon: Cpu,
        title: "Tech Stack Intel",
        desc: "AI explains architecture & design patterns tailored to you.",
      },
      {
        icon: Terminal,
        title: "Guided Practice",
        desc: "Explore real code and see how changes propagate safely.",
      },
      {
        icon: Bug,
        title: "Real-World Bugs",
        desc: "Simulate historical bugs to learn root cause analysis.",
      },
    ],
  },
  {
    id: 1,
    tag: "Offboarding",
    title: "AI-Powered Offboarding",
    desc: "Turn employee exits into knowledge continuity. Capture critical context and ensure seamless handovers without the chaos.",
    image: "/offboarding-demo.gif",
    icon: Shield,
    color: "#6366F1",
    bgGradient:
      "radial-gradient(circle at 100% 50%, rgba(99,102,241,0.15) 0%, transparent 50%)",
    points: [
      {
        icon: Layout,
        title: "Docs Reflect Code",
        desc: "AI identifies and fixes gaps in documentation automatically.",
      },
      {
        icon: Share2,
        title: "Structured Handover",
        desc: "Capture status, decisions, and risks for new owners.",
      },
      {
        icon: Shield,
        title: "Tribal Knowledge",
        desc: "Extract undocumented insights via AI exit interviews.",
      },
    ],
  },
  {
    id: 2,
    tag: "Smarix Assistance",
    title: "Smarix Assistance",
    desc: "Your 24×7 engineering companion—providing intelligent code analysis, dependency mapping, and impact tracing across complex codebases",
    image: "/assistance-demo.gif",
    icon: Code2,
    color: "#10B981",
    bgGradient:
      "radial-gradient(circle at 50% 100%, rgba(16,185,129,0.15) 0%, transparent 50%)",
    points: [
      {
        icon: Search,
        title: "Contextual Intel",
        desc: "Precise answers sourced from your actual code and docs.",
      },
      {
        icon: Terminal,
        title: "Smart Debugging",
        desc: "Analyze stack traces against system architecture instantly.",
      },
      {
        icon: GitBranch,
        title: "IDE Integration",
        desc: "Get guidance and best practices without breaking flow.",
      },
    ],
  },
];

export const Features = () => {
  const containerRef = useRef(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [targetIndex, setTargetIndex] = useState(0);
  const [queue, setQueue] = useState<number[]>([]);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  const smoothProgress = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001,
  });

  const titleScale = useTransform(smoothProgress, [0, 0.2], [1, 0.5]);
  const titleY = useTransform(smoothProgress, [0, 0.2], [0, -400]);
  const titleOpacity = useTransform(smoothProgress, [0, 0.15], [1, 0]);

  const contentOpacity = useTransform(smoothProgress, [0.15, 0.25], [0, 1]);
  const contentY = useTransform(smoothProgress, [0.15, 0.25], [100, 0]);

  useEffect(() => {
    const unsubscribe = smoothProgress.onChange((latest) => {
      if (latest < 0.2) return;

      const adjustedProgress = (latest - 0.2) / 0.8;
      const rawIndex = adjustedProgress * (features.length - 1);
      const nextTarget = Math.min(
        Math.max(Math.round(rawIndex), 0),
        features.length - 1,
      );

      setTargetIndex((prevTarget) => {
        if (nextTarget === prevTarget) return prevTarget;

        const path: number[] = [];
        const step = nextTarget > prevTarget ? 1 : -1;
        for (let i = prevTarget + step; i !== nextTarget + step; i += step) {
          path.push(i);
        }

        setQueue((old) => [...old, ...path]);

        return nextTarget;
      });
    });

    return () => {
      unsubscribe();
    };
  }, [smoothProgress]);

  useEffect(() => {
    if (queue.length === 0) return;

    let cancelled = false;

    const advance = () => {
      if (cancelled) return;

      setQueue((currentQueue) => {
        if (currentQueue.length === 0) return currentQueue;

        const [next, ...rest] = currentQueue;
        setActiveIndex(next);
        return rest;
      });
    };

    const timer = setTimeout(advance, 220);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [queue]);

  return (
    <section ref={containerRef} className="relative h-[300vh] bg-white">
      <div
        id="onboarding"
        className="absolute top-[17%] left-0 w-full h-px pointer-events-none opacity-0"
      />
      <div
        id="offboarding"
        className="absolute top-[37%] left-0 w-full h-px pointer-events-none opacity-0"
      />
      <div
        id="assistance"
        className="absolute top-[57%] left-0 w-full h-px pointer-events-none opacity-0"
      />

      <div className="sticky top-0 h-screen overflow-hidden flex flex-col items-center justify-center">
        <motion.div
          className="absolute inset-0 transition-all duration-1000 ease-in-out z-0"
          style={{ background: features[activeIndex].bgGradient }}
        />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(14,27,46,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(14,27,46,0.03)_1px,transparent_1px)] bg-[size:64px_64px] pointer-events-none z-0" />

        <motion.div
          style={{ scale: titleScale, y: titleY, opacity: titleOpacity }}
          className="absolute z-10 flex flex-col items-center justify-center text-center px-4 pointer-events-none"
        >
          <h1
            className={`${spaceGrotesk.className} text-6xl md:text-8xl lg:text-9xl font-bold text-[#0E1B2E] tracking-tighter`}
          >
            Smarix
            <br />
            Capabilities
          </h1>
        </motion.div>

        <motion.div
          style={{ opacity: contentOpacity, y: contentY }}
          className="relative z-20 w-full max-w-[1400px] px-6 h-full max-h-[900px] flex flex-col"
        >
          <div className="w-full flex justify-between items-center py-8 border-b border-slate-100/50">
            <div className="flex items-center gap-2">
              <span
                className={`${spaceGrotesk.className} text-xl font-bold text-[#0E1B2E]`}
              >
                Smarix
              </span>
              <span className="text-slate-300">/</span>
              <span
                className={`${jetbrainsMono.className} text-sm font-medium text-slate-500`}
              >
                Capabilities
              </span>
            </div>

            <div className="flex gap-2">
              {features.map((_, i) => (
                <motion.div
                  key={i}
                  animate={{
                    width: activeIndex === i ? 32 : 8,
                    backgroundColor:
                      activeIndex === i
                        ? features[activeIndex].color
                        : "#E2E8F0",
                  }}
                  className="h-2 rounded-full transition-all duration-500"
                />
              ))}
            </div>
          </div>

          <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-20 items-center">
            <div className="lg:col-span-5 flex flex-col justify-center">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeIndex}
                  initial={{ opacity: 0, x: -40 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 40 }}
                  transition={{ duration: 0.5, ease: "circOut" }}
                  className="flex flex-col"
                >
                  <div className="mb-8">
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{
                        type: "spring",
                        stiffness: 200,
                        damping: 15,
                      }}
                      className="w-16 h-16 rounded-2xl bg-white border border-slate-100 flex items-center justify-center mb-6 shadow-xl shadow-slate-200/50"
                    >
                      {React.createElement(features[activeIndex].icon, {
                        color: features[activeIndex].color,
                        size: 32,
                      })}
                    </motion.div>

                    <h2
                      className={`${spaceGrotesk.className} text-5xl lg:text-6xl font-bold leading-[1.05] tracking-tight mb-6 text-[#0E1B2E]`}
                    >
                      {features[activeIndex].title}
                    </h2>

                    <p
                      className={`${spaceGrotesk.className} text-xl leading-relaxed text-slate-500`}
                    >
                      {features[activeIndex].desc}
                    </p>
                  </div>

                  <div className="flex flex-col gap-4">
                    {features[activeIndex].points.map((point, idx) => (
                      <motion.div
                        key={idx}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 + idx * 0.1 }}
                        className="flex items-start gap-4 p-4 rounded-xl hover:bg-white/80 hover:shadow-sm transition-all duration-300 border border-transparent hover:border-slate-100"
                      >
                        <div className="mt-1 w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center shrink-0">
                          <point.icon
                            size={16}
                            style={{ color: features[activeIndex].color }}
                          />
                        </div>
                        <div>
                          <h4
                            className={`${spaceGrotesk.className} text-base font-bold text-[#0E1B2E] mb-1`}
                          >
                            {point.title}
                          </h4>
                          <p className="text-sm text-slate-500 leading-relaxed">
                            {point.desc}
                          </p>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              </AnimatePresence>
            </div>

            <div className="lg:col-span-7 h-full max-h-[600px] flex items-center">
              <div className="relative w-full aspect-[16/10] rounded-[2rem] bg-white p-2 shadow-2xl shadow-slate-200/50 border border-slate-100 ring-4 ring-slate-50">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={activeIndex}
                    className="relative w-full h-full rounded-[1.5rem] overflow-hidden bg-slate-50"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 1.05 }}
                    transition={{ duration: 0.6 }}
                  >
                    <div className="absolute top-0 left-0 right-0 h-10 bg-white/90 backdrop-blur z-20 border-b border-slate-100 flex items-center px-4 justify-between">
                      <div className="flex gap-1.5">
                        <div className="w-2.5 h-2.5 rounded-full bg-slate-200" />
                        <div className="w-2.5 h-2.5 rounded-full bg-slate-200" />
                        <div className="w-2.5 h-2.5 rounded-full bg-slate-200" />
                      </div>
                      <div
                        className={`${jetbrainsMono.className} text-[10px] text-slate-400`}
                      >
                        smarix-engine://
                        {features[activeIndex].tag.toLowerCase()}
                      </div>
                    </div>

                    <Image
                      src={features[activeIndex].image}
                      alt={features[activeIndex].title}
                      fill
                      className="object-cover mt-10"
                      unoptimized
                    />

                    <div className="absolute inset-0 ring-1 ring-inset ring-black/5 rounded-[1.5rem] z-30 pointer-events-none" />
                  </motion.div>
                </AnimatePresence>

                <motion.div
                  key={`badge-${activeIndex}`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                  className="absolute -bottom-6 -right-6 px-6 py-3 bg-white rounded-2xl shadow-xl border border-slate-100 flex items-center gap-3 z-40"
                >
                  <div
                    className="w-2 h-2 rounded-full animate-pulse"
                    style={{ backgroundColor: features[activeIndex].color }}
                  />
                  <span
                    className={`${jetbrainsMono.className} text-xs font-bold text-[#0E1B2E]`}
                  >
                    LIVE PREVIEW
                  </span>
                </motion.div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};
