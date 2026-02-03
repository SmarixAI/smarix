"use client";

import React, { useState, useEffect } from "react";
import { Space_Grotesk } from "next/font/google";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, ArrowRight } from "lucide-react";
import { TypewriterLink } from "./TypeWriterLink";
import Image from "next/image";
import Link from "next/link";

const spaceGrotesk = Space_Grotesk({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  display: "swap",
});

export const Navbar = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navLinks = [
    { name: "Onboarding", href: "#onboarding" },
    { name: "Offboarding", href: "#offboarding" },
    { name: "Smarix Assistant", href: "#assistance" },
  ];

  return (
    <>
      <motion.nav
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className={`fixed top-4 left-0 right-0 mx-auto z-50 transition-all duration-500 ease-out
          flex items-center justify-between px-6 py-3 rounded-full
          ${
            isScrolled
              ? "w-[75%] md:w-[60%] lg:w-[750px] bg-white/20 backdrop-blur-2xl shadow-lg shadow-black/5 border border-white/25 ring-1 ring-black/5"
              : "w-[88%] md:w-[78%] lg:w-[850px] bg-white/35 backdrop-blur-xl shadow-md shadow-black/5 border border-white/30"
          }`}
      >
        {/* Logo */}
        <Link href="/  " className="flex items-center gap-2 shrink-0 hover:opacity-80 transition-opacity cursor-pointer">
          <div className="w-8 h-8 bg-[#0E1B2E] rounded-lg flex items-center justify-center overflow-hidden">
            <Image
              src="/logo.png"
              alt="Logo"
              width={22}
              height={22}
              className="w-5.5 h-5.5 object-contain"
            />
          </div>
          <span className="text-[#0E1B2E] font-bold text-xl tracking-tight whitespace-nowrap">
            Smarix
          </span>
        </Link>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-8 ml-auto mr-8 whitespace-nowrap">
          {navLinks.map((link) => (
            <div key={link.name} className="whitespace-nowrap">
              <TypewriterLink text={link.name} href={link.href} />
            </div>
          ))}
        </div>

        {/* CTA */}
        <div className="hidden md:flex items-center shrink-0">
          <Link href="/contact" className="group relative overflow-hidden rounded-full bg-[#0E1B2E] px-6 py-2.5 text-white transition-all hover:bg-[#1a2f4d] hover:shadow-lg hover:shadow-[#0E1B2E]/20">
            <div className="flex items-center gap-2 whitespace-nowrap">
              <span className="text-sm font-medium tracking-wide">
                Contact Us
              </span>
              <ArrowRight className="w-4 h-4 transition-transform duration-300 group-hover:translate-x-1" />
            </div>
          </Link>
        </div>

        {/* Mobile Menu Toggle */}
        <button
          className="md:hidden text-[#0E1B2E]"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          aria-label="Toggle menu"
        >
          {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </motion.nav>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="fixed inset-x-4 top-20 z-40 rounded-3xl bg-white/90 backdrop-blur-2xl p-6 shadow-2xl shadow-black/10 border border-white/30 md:hidden"
          >
            <div className="flex flex-col gap-2">
              {navLinks.map((link, index) => (
                <motion.a
                  key={link.name}
                  href={link.href}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="text-[#0E1B2E] text-base font-medium py-3 px-2 rounded-lg hover:bg-gray-100/50 transition-colors"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  {link.name}
                </motion.a>
              ))}

              <Link 
                href="/request-demo"
                className="w-full mt-4 rounded-full bg-[#0E1B2E] py-3.5 text-white font-medium shadow-xl shadow-[#0E1B2E]/20 hover:bg-[#1a2f4d] transition-colors text-center"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Contact Us
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};
