"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Zap, FileText, MessageSquare, Sparkles, ArrowUpRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { Space_Grotesk, Fira_Code, Lora } from "next/font/google";
import Image from "next/image";
import Link from "next/link";

const spaceGrotesk = Space_Grotesk({
    subsets: ["latin"],
    display: "swap",
});

const firaCode = Fira_Code({
    weight: ["400", "500"],
    subsets: ["latin"],
    display: "swap",
});

const lora = Lora({
    weight: ["400", "500", "700"],
    subsets: ["latin"],
    display: "swap",
    style: ["normal", "italic"],
});

const TOOLS = [
    {
        id: "impact-analyzer",
        href: "/impact-analyzer",
        icon: Zap,
        number: "01",
        label: "Impact Analyzer",
        tagline: "Understand change before it ships",
        description: "Blast radius, risk score, and dependency graphs mapped out before you ever merge.",
        accent: "#F59E0B",
        accentLight: "#FFFBEB",
        accentMid: "#FEF3C7",
        stats: ["Instant blast radius", "0–100 risk score", "Live dep graph"],
    },
    {
        id: "prompt-builder",
        href: "/prompt-builder",
        icon: Sparkles,
        number: "02",
        label: "Prompt Builder",
        tagline: "Craft prompts that actually work",
        description: "Repo-aware prompts grounded in real context, tested and refined for precision.",
        accent: "#8B5CF6",
        accentLight: "#F5F3FF",
        accentMid: "#EDE9FE",
        stats: ["50+ templates", "Multi-model", "Repo-grounded"],
    },
    {
        id: "auto-documentation",
        href: "/auto-documentation",
        icon: FileText,
        number: "03",
        label: "Auto Documentation",
        tagline: "Docs that write themselves",
        description: "Achieve 100% coverage, auto-synced on every single commit with zero manual effort.",
        accent: "#10B981",
        accentLight: "#F0FDF4",
        accentMid: "#D1FAE5",
        stats: ["100% coverage", "MD / JSDoc", "Auto-sync"],
    },
    {
        id: "code-guide",
        href: "/chat",
        icon: MessageSquare,
        number: "04",
        label: "Code Guide",
        tagline: "Your codebase, always explained",
        description: "Chat directly with your repo. Understand architecture, PRs, and bugs in plain English.",
        accent: "#06B6D4",
        accentLight: "#ECFEFF",
        accentMid: "#CFFAFE",
        stats: ["Session memory", "Cited sources", "Flow diagrams"],
    },
];

export default function ProductivityPage() {
    const router = useRouter();
    const [hovered, setHovered] = useState<string | null>(null);
    const [clicked, setClicked] = useState<string | null>(null);

    const handleNavigate = (href: string, id: string) => {
        setClicked(id);
        setTimeout(() => router.push(href), 300);
    };

    const activeTool = hovered ? TOOLS.find((t) => t.id === hovered) : null;

    return (
        <div
            className={`h-screen w-screen overflow-hidden flex flex-col ${spaceGrotesk.className}`}
            style={{ userSelect: "none", backgroundColor: "#0E1B2E" }} // Base color fallback
        >
            {/* ── TOP NAV (Unified across both panels) ── */}
            <nav className="relative z-30 flex items-center justify-between px-10 py-4 bg-white/95 backdrop-blur-xl border-b border-[#0E1B2E]/10 flex-shrink-0 shadow-sm">
                <Link href="/admin" className="flex items-center gap-4 group">
                    <div className="w-9 h-9 bg-[#0E1B2E] rounded-xl flex items-center justify-center overflow-hidden shadow-md transition-transform group-hover:scale-105">
                        <Image src="/logo.png" alt="Smarix" width={22} height={22} className="object-contain" />
                    </div>
                    <span className="font-extrabold text-xl text-[#0E1B2E] tracking-tight">Smarix</span>
                </Link>

                <div className="flex items-center gap-6">
                    <div className="flex items-center gap-5">
                        {TOOLS.map((t) => (
                            <div key={t.id} className="flex items-center gap-2">
                                <motion.div
                                    className="w-2 h-2 rounded-full"
                                    style={{ background: t.accent }}
                                    animate={{
                                        scale: hovered === t.id ? 1.8 : 1,
                                        opacity: hovered === t.id ? 1 : 0.4
                                    }}
                                    transition={{ duration: 0.3 }}
                                />
                                <span className={`text-[11px] font-semibold text-[#0E1B2E]/60 ${firaCode.className}`}>
                                    {t.label.split(" ")[0]}
                                </span>
                            </div>
                        ))}
                    </div>
                    <div className="h-4 w-px bg-[#0E1B2E]/15" />
                    <span className={`text-[11px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-100 px-3 py-1 rounded-full ${firaCode.className}`}>
                        ● 4 active
                    </span>
                </div>
            </nav>

            {/* ── BODY ── */}
            <div className="relative flex-1 flex overflow-hidden min-h-0">

                {/* ── LEFT SIDEBAR (Stark White + Soft Gradient Wash) ── */}
                <div className="relative z-20 flex flex-col justify-between px-10 py-8 xl:px-12 w-[420px] xl:w-[480px] flex-shrink-0 bg-white border-r border-[#0E1B2E]/10 shadow-[20px_0_60px_-15px_rgba(14,27,46,0.05)] overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">

                    {/* Subtle internal top-down gradient */}
                    <div className="absolute top-0 left-0 right-0 h-96 bg-gradient-to-b from-[#0E1B2E]/[0.03] to-transparent pointer-events-none" />

                    {/* Headline */}
                    <div className="relative z-10 flex-shrink-0">
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5 }}
                            className={`inline-flex items-center gap-2 mb-6 px-3 py-1.5 rounded-full border border-[#0E1B2E]/10 bg-white/80 backdrop-blur-md shadow-sm ${firaCode.className}`}
                        >
                            <Sparkles className="w-3.5 h-3.5 text-violet-500" />
                            <span className="text-[11px] font-bold text-[#0E1B2E]/70 uppercase tracking-widest">
                                Productivity Suite
                            </span>
                        </motion.div>

                        <motion.h1
                            initial={{ opacity: 0, y: 14 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.6, delay: 0.08 }}
                            className="text-5xl font-black text-[#0E1B2E] leading-[1.05] tracking-tight mb-4"
                        >
                            Your<br />
                            <span
                                className={`italic font-bold pr-2 ${lora.className}`}
                                style={{
                                    background: "linear-gradient(135deg, #8B5CF6 0%, #06B6D4 50%, #10B981 100%)",
                                    WebkitBackgroundClip: "text",
                                    WebkitTextFillColor: "transparent",
                                    backgroundClip: "text",
                                }}
                            >
                                Codebase,
                            </span>
                            <br />
                            Supercharged.
                        </motion.h1>

                        <motion.p
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ duration: 0.5, delay: 0.2 }}
                            className="text-base font-medium text-[#0E1B2E]/60 leading-relaxed max-w-sm"
                        >
                            Four AI-powered tools. One mission — ship faster, break less, understand more.
                        </motion.p>
                    </div>

                    {/* Dynamic preview on hover */}
                    <div className="relative z-10 flex-1 flex flex-col justify-center py-6 min-h-[280px]">
                        <AnimatePresence mode="wait">
                            {activeTool ? (
                                <motion.div
                                    key={activeTool.id}
                                    initial={{ opacity: 0, x: -15, filter: "blur(4px)" }}
                                    animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
                                    exit={{ opacity: 0, x: 15, filter: "blur(4px)" }}
                                    transition={{ duration: 0.25, ease: "easeOut" }}
                                    className="w-full"
                                >
                                    <motion.div
                                        className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4 shadow-lg border border-white"
                                        style={{ background: activeTool.accentMid }}
                                        layoutId="preview-icon"
                                    >
                                        <activeTool.icon className="w-8 h-8" style={{ color: activeTool.accent }} />
                                    </motion.div>

                                    <h2 className="text-2xl font-bold text-[#0E1B2E] mb-1.5 leading-snug">
                                        {activeTool.label}
                                    </h2>
                                    <p
                                        className={`text-[11px] mb-4 font-bold uppercase tracking-wider ${firaCode.className}`}
                                        style={{ color: activeTool.accent }}
                                    >
                                        {activeTool.tagline}
                                    </p>
                                    <p className="text-base text-[#0E1B2E]/70 leading-relaxed mb-5 max-w-sm">
                                        {activeTool.description}
                                    </p>

                                    <div className="flex flex-col gap-3">
                                        {activeTool.stats.map((s, i) => (
                                            <motion.div
                                                key={s}
                                                initial={{ opacity: 0, x: -10 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                transition={{ delay: i * 0.08 }}
                                                className="flex items-center gap-3"
                                            >
                                                <div
                                                    className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0"
                                                    style={{ background: activeTool.accentMid }}
                                                >
                                                    <div className="w-1.5 h-1.5 rounded-full" style={{ background: activeTool.accent }} />
                                                </div>
                                                <span className={`text-xs font-semibold text-[#0E1B2E]/70 ${firaCode.className}`}>{s}</span>
                                            </motion.div>
                                        ))}
                                    </div>
                                </motion.div>
                            ) : (
                                <motion.div
                                    key="idle"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    transition={{ duration: 0.3 }}
                                    className="w-full"
                                >
                                    <div className="flex gap-3 mb-5">
                                        {TOOLS.map((t) => (
                                            <div
                                                key={t.id}
                                                className="w-10 h-10 rounded-xl flex items-center justify-center opacity-40 grayscale transition-all duration-500 hover:grayscale-0 hover:opacity-100 cursor-default bg-[#0E1B2E]/5"
                                            >
                                                <t.icon className="w-5 h-5" style={{ color: t.accent }} />
                                            </div>
                                        ))}
                                    </div>
                                    <p className={`text-sm text-[#0E1B2E]/40 font-semibold ${firaCode.className}`}>
                                        Hover a card to preview capabilities →
                                    </p>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>

                    {/* Bottom stats */}
                    <div className="relative z-10 flex gap-8 pt-6 border-t border-[#0E1B2E]/10 flex-shrink-0">
                        {[
                            { v: "99%", l: "Accuracy" },
                            { v: "2.4k+", l: "Teams" },
                            { v: "180k", l: "PRs Analyzed" },
                        ].map((s) => (
                            <div key={s.l}>
                                <div className={`text-xl font-black text-[#0E1B2E] ${firaCode.className}`}>{s.v}</div>
                                <div className="text-[10px] font-bold text-[#0E1B2E]/40 mt-1 uppercase tracking-wider">{s.l}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* ── RIGHT: CARDS GRID (Off-white + Dot Texture) ── */}
                <div className="relative z-10 flex-1 flex flex-col justify-center items-center p-8 overflow-y-auto bg-[#FAFAFA]">

                    {/* Dot grid mapped exclusively to the right area */}
                    <div
                        className="absolute inset-0 pointer-events-none z-0 opacity-[0.6]"
                        style={{
                            backgroundImage: `radial-gradient(circle at 1px 1px, #0E1B2E1A 1px, transparent 0)`,
                            backgroundSize: "32px 32px",
                        }}
                    />

                    {/* Ambient Hover Glow */}
                    <motion.div
                        className="absolute inset-0 pointer-events-none z-0"
                        animate={{
                            background: activeTool
                                ? `radial-gradient(circle 800px at 50% 50%, ${activeTool.accent}10 0%, transparent 100%)`
                                : "none",
                        }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                    />

                    {/* Cards Container */}
                    <div className="relative z-10 w-full max-w-[900px] flex flex-col gap-6">

                        {/* 2×2 GRID */}
                        <div className="grid grid-cols-2 gap-6">
                            {TOOLS.map((tool, index) => {
                                const Icon = tool.icon;
                                const isHov = hovered === tool.id;
                                const isClk = clicked === tool.id;
                                const isFaded = hovered !== null && hovered !== tool.id;

                                return (
                                    <motion.div
                                        key={tool.id}
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{
                                            opacity: isFaded ? 0.4 : 1,
                                            scale: isClk ? 0.95 : isHov ? 1.02 : 1,
                                            y: 0
                                        }}
                                        transition={{
                                            duration: 0.35,
                                            delay: hovered ? 0 : 0.08 + index * 0.08,
                                            ease: [0.23, 1, 0.32, 1],
                                        }}
                                        onHoverStart={() => setHovered(tool.id)}
                                        onHoverEnd={() => setHovered(null)}
                                        onClick={() => handleNavigate(tool.href, tool.id)}
                                        className="relative cursor-pointer rounded-3xl bg-white flex flex-col overflow-hidden border"
                                        style={{
                                            borderColor: isHov ? tool.accent : "#0E1B2E15",
                                            boxShadow: isHov
                                                ? `0 24px 48px -12px ${tool.accent}25, 0 8px 24px -4px ${tool.accent}15`
                                                : "0 4px 16px -4px rgba(14,27,46,0.04)", // Softer resting shadow against off-white bg
                                        }}
                                    >
                                        {/* Top accent line */}
                                        <motion.div
                                            className="absolute top-0 left-0 right-0 h-[3px] origin-left z-20"
                                            animate={{ scaleX: isHov ? 1 : 0 }}
                                            initial={{ scaleX: 0 }}
                                            transition={{ duration: 0.3, ease: "easeInOut" }}
                                            style={{ background: tool.accent }}
                                        />

                                        <div className="relative flex flex-col h-[280px] p-6 z-10">
                                            {/* Row 1: number + icon + arrow */}
                                            <div className="flex items-start justify-between mb-5">
                                                <div className="flex items-center gap-3">
                                                    <span
                                                        className={`text-xs font-bold tracking-widest ${firaCode.className}`}
                                                        style={{ color: `${tool.accent}90` }}
                                                    >
                                                        {tool.number}
                                                    </span>
                                                    <motion.div
                                                        className="w-12 h-12 rounded-2xl flex items-center justify-center border border-white"
                                                        style={{ background: tool.accentLight }}
                                                        animate={{
                                                            rotate: isHov ? 10 : 0,
                                                            scale: isHov ? 1.1 : 1,
                                                        }}
                                                        transition={{ type: "spring", stiffness: 300 }}
                                                    >
                                                        <Icon className="w-6 h-6" style={{ color: tool.accent }} />
                                                    </motion.div>
                                                </div>

                                                <motion.div
                                                    className="w-10 h-10 rounded-full flex items-center justify-center border-2 bg-white"
                                                    animate={{
                                                        rotate: isHov ? 45 : 0,
                                                        backgroundColor: isHov ? tool.accent : "#fff",
                                                        borderColor: isHov ? tool.accent : "#0E1B2E15",
                                                    }}
                                                    transition={{ duration: 0.25 }}
                                                >
                                                    <ArrowUpRight
                                                        className="w-5 h-5 transition-colors duration-300"
                                                        style={{ color: isHov ? "#fff" : "#0E1B2E40" }}
                                                    />
                                                </motion.div>
                                            </div>

                                            {/* Row 2: title + tagline */}
                                            <div className="mb-3">
                                                <h2 className="text-xl font-extrabold text-[#0E1B2E] leading-tight mb-1">{tool.label}</h2>
                                                <p
                                                    className={`text-[11px] font-bold uppercase tracking-wider ${firaCode.className}`}
                                                    style={{ color: tool.accent }}
                                                >
                                                    {tool.tagline}
                                                </p>
                                            </div>

                                            {/* Row 3: description */}
                                            <p className="text-sm font-medium text-[#0E1B2E]/60 leading-relaxed flex-1">
                                                {tool.description}
                                            </p>

                                            {/* Row 4: stat pills */}
                                            <div className="flex gap-2 flex-wrap pt-4 border-t border-[#0E1B2E]/10">
                                                {tool.stats.slice(0, 2).map((s) => (
                                                    <span
                                                        key={s}
                                                        className={`text-[11px] px-2.5 py-1 rounded-full font-bold ${firaCode.className}`}
                                                        style={{ background: tool.accentLight, color: tool.accent }}
                                                    >
                                                        {s}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    </motion.div>
                                );
                            })}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}