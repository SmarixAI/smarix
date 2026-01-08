'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Space_Grotesk  } from "next/font/google";

interface TypewriterLinkProps {
  text: string;
  href: string;
}

const spaceGrotesk = Space_Grotesk({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  display: "swap",
});

export const TypewriterLink = ({ text, href }: TypewriterLinkProps) => {
  const [displayText, setDisplayText] = useState(text);
  const [isHovering, setIsHovering] = useState(false);
  
  const chars = "HIJKLMNOPQRSTUYZ"; 

  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (isHovering) {
      let iteration = 0;
      
      interval = setInterval(() => {
        setDisplayText((prev) =>
          text
            .split("")
            .map((letter, index) => {
              if (index < iteration) {
                return text[index];
              }
              return chars[Math.floor(Math.random() * chars.length)];
            })
            .join("")
        );

        if (iteration >= text.length) {
          clearInterval(interval);
        }

        iteration += 1.5; 
      }, 40);
    } else {
      setDisplayText(text);
    }

    return () => clearInterval(interval);
  }, [isHovering, text]);

  return (
    <Link
      href={href}
      className="relative text-[#0E1B2E] font-display font-medium text-sm tracking-wide px-2 py-1 group"
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      <span className={`${spaceGrotesk.className} relative z-10 block min-w-[10px] text-center`}>
        {displayText}
      </span>
      <span className="absolute bottom-0 left-0 w-0 h-[1.5px] bg-[#0E1B2E] transition-all duration-500 ease-out group-hover:w-full" />
    </Link>
  );
};