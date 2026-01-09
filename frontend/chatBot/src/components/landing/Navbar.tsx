"use client";

import React, { useState, useEffect } from "react";
import { Space_Grotesk } from "next/font/google";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, ArrowRight } from "lucide-react";
import { TypewriterLink } from "./TypeWriterLink";
import Image from "next/image";

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
    { name: "Analytics", href: "#" },
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
              ? "w-[88%] md:w-[75%] lg:w-[900px] bg-white/20 backdrop-blur-2xl shadow-lg shadow-black/5 border border-white/25 ring-1 ring-black/5"
              : "w-[92%] md:w-[85%] lg:w-[1000px] bg-white/35 backdrop-blur-xl shadow-md shadow-black/5 border border-white/30"
          }`}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="w-8 h-8 bg-[#0E1B2E] rounded-lg flex items-center justify-center overflow-hidden">
            <Image
              src="/logo.png"
              alt="Logo"
              width={24}
              height={24}
              className="w-6 h-6 object-contain"
            />
          </div>
          <span className="text-[#0E1B2E] font-bold text-xl tracking-tight whitespace-nowrap">
            Smarix
          </span>
        </div>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-5 ml-14 mr-10 whitespace-nowrap">
          {navLinks.map((link) => (
            <div key={link.name} className="whitespace-nowrap">
              <TypewriterLink text={link.name} href={link.href} />
            </div>
          ))}
        </div>

        {/* CTA */}
        <div className="hidden md:flex items-center shrink-0">
          <button className="group relative overflow-hidden rounded-full bg-[#0E1B2E] px-6 py-2.5 text-white transition-all hover:bg-[#1a2f4d] hover:shadow-lg hover:shadow-[#0E1B2E]/20">
            <div className="flex items-center gap-2 whitespace-nowrap">
              <span className="text-sm font-tahoma font-semibold tracking-wide">
                Request demo
              </span>
              <ArrowRight className="w-4 h-4 transition-transform duration-300 group-hover:translate-x-1" />
            </div>
          </button>
        </div>

        {/* Mobile Menu Toggle */}
        <button
          className="md:hidden text-[#0E1B2E]"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        >
          {isMobileMenuOpen ? <X /> : <Menu />}
        </button>
      </motion.nav>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            className="fixed inset-x-4 top-24 z-40 rounded-3xl bg-white/75 backdrop-blur-2xl p-6 shadow-2xl shadow-black/10 border border-white/25 md:hidden"
          >
            <div className="flex flex-col gap-4">
              {navLinks.map((link) => (
                <a
                  key={link.name}
                  href={link.href}
                  className="text-[#0E1B2E] text-lg font-medium py-3 border-b border-gray-100 last:border-0"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  {link.name}
                </a>
              ))}

              <button className="w-full mt-4 rounded-full bg-[#0E1B2E] py-4 text-white font-medium shadow-xl shadow-[#0E1B2E]/10">
                Request for demo
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};
