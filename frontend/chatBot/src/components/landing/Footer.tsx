'use client';

import React, { useRef } from 'react';
import { motion, useScroll, useTransform, useSpring } from 'framer-motion';
import { ArrowUpRight, Github, Twitter, Linkedin } from 'lucide-react';
import { Space_Grotesk, JetBrains_Mono, Fira_Code } from 'next/font/google';
import Image from 'next/image';
import Link from 'next/link';

const spaceGrotesk = Space_Grotesk({ subsets: ['latin'] });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'] });
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

  const yText = useTransform(smoothProgress, [0.5, 1], [100, 0]);
  const opacityText = useTransform(smoothProgress, [0.6, 1], [0, 1]);

  return (
    <footer 
      ref={containerRef} 
      className="relative w-full bg-[#0E1B2E] text-white overflow-hidden pt-32 pb-6"
    >
      <div className="absolute top-0 left-0 w-full h-40 bg-gradient-to-b from-white/5 to-transparent pointer-events-none z-10" />

      <div className="relative z-20 max-w-[1400px] mx-auto px-8 flex flex-col justify-between min-h-[70vh]">
        
        <div className="flex flex-col lg:flex-row justify-between items-start gap-12 mb-24">
          
          <div className="max-w-4xl relative z-20">
            <motion.h2 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className={`${spaceGrotesk.className} text-5xl md:text-6xl lg:text-7xl font-bold leading-[0.9] tracking-tight mb-12`}
            >
              Ready to integrate <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400">Smarix</span> in your life?
            </motion.h2>

            <Link href="/try-our-product">
              <motion.button 
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="group relative inline-flex items-center gap-5 bg-white text-[#0E1B2E] px-8 py-4 rounded-none transition-all duration-300 hover:bg-blue-50"
              >
                <span className={`${firaCode.className} font-bold tracking-wide text-base relative z-10`}>
                  TRY OUR PRODUCT
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
               className="w-40 h-40 md:w-56 md:h-56 relative bg-white/5 rounded-[2rem] flex items-center justify-center border border-white/10 backdrop-blur-sm overflow-hidden"
             >
                <Image src="/logo.png" alt="Smarix Logo" width={120} height={120} className="object-contain w-28 h-28 md:w-40 md:h-40 rounded-[2rem]" />
             </motion.div>
             <p className={`${jetbrainsMono.className} text-white/40 text-sm max-w-[240px] leading-relaxed text-right`}>
               Empowering engineering teams with AI-driven knowledge continuity.
             </p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-12 gap-y-10 border-t border-white/10 pt-16 mb-20 relative z-20 bg-[#0E1B2E]/50 backdrop-blur-sm rounded-t-3xl">
           <div className="flex flex-col gap-6">
              <h4 className={`${jetbrainsMono.className} text-[11px] font-bold text-blue-400 uppercase tracking-widest`}>Navigation</h4>
              <ul className="flex flex-col gap-4">
                 {['Home', 'Capabilities', 'Integration'].map((item, i) => (
                    <li key={i}>
                       <a href="#" className="text-white/60 hover:text-white hover:translate-x-2 transition-all duration-200 text-base font-medium inline-block">{item}</a>
                    </li>
                 ))}
              </ul>
           </div>

           <div className="flex flex-col gap-6">
              <h4 className={`${jetbrainsMono.className} text-[11px] font-bold text-blue-400 uppercase tracking-widest`}>Company</h4>
              <ul className="flex flex-col gap-4">
                 <li>
                    <a href="/about" className="text-white/60 hover:text-white hover:translate-x-2 transition-all duration-200 text-base font-medium inline-block">About Us</a>
                 </li>
                 <li>
                    <a href="/blog" className="text-white/60 hover:text-white hover:translate-x-2 transition-all duration-200 text-base font-medium inline-block">Blog</a>
                 </li>
                 <li>
                    <a href="/contact" className="text-white/60 hover:text-white hover:translate-x-2 transition-all duration-200 text-base font-medium inline-block">Contact</a>
                 </li>
              </ul>
           </div>

           {/* <div className="flex flex-col gap-6">
              <h4 className={`${jetbrainsMono.className} text-[11px] font-bold text-blue-400 uppercase tracking-widest`}>Legal</h4>
              <ul className="flex flex-col gap-4">
                 {['Privacy Policy', 'Terms of Service', 'Cookie Policy'].map((item, i) => (
                    <li key={i}>
                       <a href="#" className="text-white/60 hover:text-white hover:translate-x-2 transition-all duration-200 text-base font-medium inline-block">{item}</a>
                    </li>
                 ))}
              </ul>
           </div> */}
        </div>

        <div className="relative w-full">
           <motion.div 
             style={{ y: yText, opacity: opacityText }}
             className="w-full flex justify-center items-end pointer-events-none select-none mb-4"
           >
              <svg viewBox="0 0 1320 240" className="w-full h-auto">
                 <text 
                   x="33%" 
                   y="90%" 
                   textAnchor="middle"
                   className={`${spaceGrotesk.className} font-bold text-[240px] fill-transparent stroke-[#FFFFFF]`}
                   style={{ strokeWidth: "1px", strokeOpacity: 0.15 }}
                 >
                   SMARIX
                 </text>
              </svg>
           </motion.div>

           <div className="relative z-30 flex flex-col md:flex-row justify-between items-center gap-4 pt-6 border-t border-white/10">
              <p className={`${jetbrainsMono.className} text-[11px] text-white/30 uppercase tracking-wider`}>
                 © 2026 Smarix AI Inc. All rights reserved.
              </p>
              <p className={`${jetbrainsMono.className} text-[11px] text-white/30 uppercase tracking-wider`}>
                 Built with ❤️ in India.
              </p>
           </div>
        </div>

      </div>
    </footer>
  );
};