'use client';

import React, { useRef } from 'react';
import { motion, useScroll, useTransform, useSpring } from 'framer-motion';
import { Victor_Mono, Fira_Code, Google_Sans_Code } from 'next/font/google';

const firaCode = Google_Sans_Code({
  weight: ["400", "500", "700"],
  subsets: ["latin"],
  display: "swap",
});

const victorMono = Victor_Mono({
  weight: ["400", "500"],
  subsets: ["latin"],
  display: "swap",
});

export const Transition = () => {
  const containerRef = useRef(null);
  
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start 90%", "center center"] 
  });

  const springConfig = { stiffness: 100, damping: 20, restDelta: 0.001 };
  const smoothProgress = useSpring(scrollYProgress, springConfig);

  const opacity1 = useTransform(smoothProgress, [0, 0.3], [0, 1]);
  const y1 = useTransform(smoothProgress, [0, 0.3], [30, 0]);
  const blur1 = useTransform(smoothProgress, [0, 0.3], [10, 0]);

  const opacity2 = useTransform(smoothProgress, [0.2, 0.5], [0, 1]);
  const y2 = useTransform(smoothProgress, [0.2, 0.5], [30, 0]);
  const blur2 = useTransform(smoothProgress, [0.2, 0.5], [10, 0]);

  const opacity3 = useTransform(smoothProgress, [0.4, 0.7], [0, 1]);
  const y3 = useTransform(smoothProgress, [0.4, 0.7], [30, 0]);
  const blur3 = useTransform(smoothProgress, [0.4, 0.7], [10, 0]);
  const scale3 = useTransform(smoothProgress, [0.4, 0.8], [0.9, 1]);

  const opacitySub = useTransform(smoothProgress, [0.6, 0.9], [0, 1]);
  const ySub = useTransform(smoothProgress, [0.6, 0.9], [20, 0]);

  return (
    <section 
      ref={containerRef} 
      className="relative h-[50vh] flex flex-col items-center justify-center bg-[#F2F4F7] overflow-hidden border-t border-white/50"
    >
      <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 mix-blend-soft-light pointer-events-none" />
      
      <div className="relative z-10 w-full max-w-7xl px-6 flex flex-col items-center justify-center">
        
        <div className="flex flex-col md:flex-row items-center gap-4 md:gap-6 lg:gap-6">
            
            <motion.h2
              style={{ opacity: opacity1, filter: `blur(${blur1}px)`, y: y1 }}
              className={`${firaCode.className} text-5xl md:text-6xl lg:text-7xl font-tahoma font-bold tracking-tighter text-[#0E1B2E]`}
            >
              Simple
              <span className={`${firaCode.className} text-blue-600`}>.</span>
            </motion.h2>

            <motion.h2
              style={{ opacity: opacity2, filter: `blur(${blur2}px)`, y: y2 }}
              className={`${firaCode.className} text-5xl md:text-6xl lg:text-7xl font-tahoma font-bold tracking-tighter text-[#0E1B2E]`}
            >
              Faster
              <span className={`${firaCode.className} text-blue-600`}>.</span>
            </motion.h2>

            <motion.h2
               style={{ opacity: opacity3, filter: `blur(${blur3}px)`, y: y3, scale: scale3 }}
               className={`${firaCode.className} text-5xl md:text-6xl lg:text-7xl font-tahoma font-bold tracking-tighter text-[#0E1B2E]`}
            >
                Done
                <span className={`${firaCode.className} text-green-500`}>.</span>
            </motion.h2>
        </div>

        <motion.div 
          style={{ opacity: opacitySub, y: ySub }}
          className="mt-10 flex flex-col items-center gap-6"
        >
          <p className={`${victorMono.className} text-lg md:text-xl text-gray-500 font-medium text-center max-w-xl leading-relaxed`}>
             Turn employee transitions into <span className="text-[#0E1B2E] font-bold border-b-2 border-gray-200">knowledge continuity</span>.
          </p>
        </motion.div>

      </div>
    </section>
  );
};