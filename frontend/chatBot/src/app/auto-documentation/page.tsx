"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import mermaid from "mermaid";
import {
    FileCode,
    ChevronRight,
    ChevronDown,
    Copy,
    Check,
    Download,
    Loader2,
    ArrowLeft,
    Sparkles,
    BookOpen,
    GitCommit,
    Database,
    Settings,
    FileText,
    Code2,
    Layout,
    Terminal,
    Users,
    RefreshCw,
    ZoomIn,
    ZoomOut,
    RotateCcw,
    Folder,
    FolderOpen,
    Cpu,
    Zap,
    Search,
    FileCheck2,
    Layers
} from "lucide-react";
import { useRouter } from "next/navigation";
import { Fira_Code, Space_Grotesk } from "next/font/google";
import { useAuth } from "@/components/auth/AuthContext";

const firaCode = Fira_Code({
    weight: ["400", "500", "600", "700"],
    subsets: ["latin"],
    display: "swap",
});

const spaceGrotesk = Space_Grotesk({
    weight: ["400", "500", "600", "700"],
    subsets: ["latin"],
    display: "swap",
});

if (typeof window !== "undefined") {
    mermaid.initialize({
        startOnLoad: false,
        theme: "default",
        logLevel: "error",
        securityLevel: "loose",
        themeVariables: {
            primaryColor: "#0E1B2E",
            primaryTextColor: "#FAFAFA",
            primaryBorderColor: "#0E1B2E",
            lineColor: "#0E1B2E",
            secondaryColor: "#1a2f4d",
            tertiaryColor: "#FAFAFA",
            background: "#FAFAFA",
            mainBkg: "#FFFFFF",
            nodeBorder: "#0E1B2E",
            clusterBkg: "#F5F5F5",
            clusterBorder: "#0E1B2E",
            titleColor: "#0E1B2E",
            edgeLabelBackground: "#FFFFFF",
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
        },
        flowchart: { htmlLabels: true, curve: "basis", useMaxWidth: true },
    });
}

const IGNORED_PATTERNS: RegExp[] = [
    // ── Package / dependency dirs ──────────────────────────────────────────
    /node_modules\//,
    /\.pub-cache\//,
    /\.pub\//,
    /vendor\//,               // PHP / Go / Ruby
    /Pods\//,                 // iOS CocoaPods
    /\.bundle\//,             // Ruby bundler
    /bower_components\//,     // legacy JS

    // ── Build & output dirs ────────────────────────────────────────────────
    /^build\//,
    /^dist\//,
    /^out\//,
    /^output\//,
    /^target\//,              // Rust / Maven
    /^bin\//,
    /^obj\//,                 // .NET
    /^\.next\//,
    /^\.nuxt\//,
    /^\.svelte-kit\//,
    /^\.output\//,            // Nuxt 3
    /^\.dart_tool\//,
    /^\.gradle\//,
    /android\/app\/build\//,
    /android\/build\//,
    /ios\/build\//,
    /ios\/Pods\//,
    /ios\/\.symlinks\//,
    /macos\/Pods\//,
    /\.flutter-plugins/,
    /\.flutter-plugins-dependencies/,

    // ── VCS / IDE / OS ─────────────────────────────────────────────────────
    /^\.git\//,
    /^\.github\/workflows\/.*\.yml$/,  // keep, don't ignore CI files
    /^\.idea\//,
    /^\.vscode\//,
    /^\.vs\//,                // Visual Studio
    /\.DS_Store/,
    /Thumbs\.db/,
    /desktop\.ini/,

    // ── Python ────────────────────────────────────────────────────────────
    /venv\//,
    /\.venv\//,
    /env\//,
    /__pycache__\//,
    /\.pyc$/,
    /\.pyo$/,
    /\.pyd$/,
    /\.egg-info\//,
    /\.eggs\//,
    /\.tox\//,
    /\.mypy_cache\//,
    /\.pytest_cache\//,
    /\.ruff_cache\//,
    /site-packages\//,

    // ── JavaScript / TypeScript ────────────────────────────────────────────
    /package-lock\.json$/,
    /yarn\.lock$/,
    /pnpm-lock\.yaml$/,
    /bun\.lockb$/,
    /\.turbo\//,
    /\.parcel-cache\//,
    /\.cache\//,
    /storybook-static\//,
    /coverage\//,
    /\.nyc_output\//,

    // ── Dart / Flutter generated ───────────────────────────────────────────
    /pubspec\.lock$/,
    /\.freezed\.dart$/,
    /\.g\.dart$/,
    /\.gr\.dart$/,
    /\.gen\.dart$/,
    /\.mocks\.dart$/,
    /GeneratedPluginRegistrant\.dart$/,
    /generated_plugin_registrant\.dart$/,
    /\.dart_tool\//,
    /flutter_gen\//,

    // ── Java / Kotlin / Android ────────────────────────────────────────────
    /\.class$/,
    /\.jar$/,
    /\.aar$/,
    /\.ap_$/,
    /R\.java$/,
    /BuildConfig\.java$/,
    /R\.kt$/,

    // ── Swift / iOS ────────────────────────────────────────────────────────
    /Podfile\.lock$/,
    /xcuserdata\//,
    /\.xcworkspace\//,
    /DerivedData\//,

    // ── Rust ──────────────────────────────────────────────────────────────
    /Cargo\.lock$/,           // keep for apps, but lock files add noise in tree
    /\.cargo\//,

    // ── Go ────────────────────────────────────────────────────────────────
    /go\.sum$/,

    // ── .NET / C# ─────────────────────────────────────────────────────────
    /\.suo$/,
    /\.user$/,
    /packages\//,             // NuGet
    /\.nuget\//,

    // ── Ruby ──────────────────────────────────────────────────────────────
    /Gemfile\.lock$/,
    /\.bundle\//,
    /tmp\//,
    /log\//,

    // ── PHP ───────────────────────────────────────────────────────────────
    /composer\.lock$/,

    // ── Env / secrets ─────────────────────────────────────────────────────
    /^\.env$/,
    /^\.env\.[^e]/,           // .env.local, .env.production etc — hide from tree
    // but keep .env.example, .env.sample

    // ── Binary / media / fonts ────────────────────────────────────────────
    /\.(png|jpg|jpeg|gif|bmp|webp|ico|svg|tiff)$/i,
    /\.(mp4|mp3|wav|ogg|flac|avi|mov|mkv|webm)$/i,
    /\.(ttf|otf|woff|woff2|eot)$/i,
    /\.(pdf|docx?|xlsx?|pptx?)$/i,
    /\.(zip|tar|gz|rar|7z|bz2)$/i,
    /\.(so|dylib|dll|exe|bin|apk|ipa|deb|rpm)$/i,

    // ── Misc generated / noisy ────────────────────────────────────────────
    /\.min\.js$/,
    /\.min\.css$/,
    /\.map$/,                 // source maps
    /\.snap$/,                // Jest snapshots — keep if you want, noisy otherwise
    /migration.*\.sql$/,      // generated migrations (comment out if you want these)
    /schema\.prisma$/,        // uncomment to hide Prisma schema
];

// Files/dirs that are always useful regardless
const ALWAYS_INCLUDE_NAMES = new Set([
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Makefile",
    "Procfile",
    ".env.example",
    ".env.sample",
    ".env.template",
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
]);

// Allowed source code + config extensions
const ALLOWED_EXTENSIONS = new Set([
    // Application code
    ".dart", ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".go", ".rs", ".java", ".kt", ".kts", ".swift",
    ".rb", ".cpp", ".c", ".h", ".cs", ".php",
    ".vue", ".svelte", ".astro",
    ".ex", ".exs",              // Elixir
    ".clj", ".cljs",            // Clojure
    ".scala", ".sbt",           // Scala
    ".hs",                      // Haskell
    ".lua",                     // Lua
    ".r", ".R",                 // R

    // Config / infra
    ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".json",                    // but package-lock.json is excluded above
    ".xml",
    ".gradle", ".properties",
    ".tf", ".tfvars",           // Terraform
    ".sh", ".bash", ".zsh", ".fish",
    ".sql",
    ".prisma",
    ".graphql", ".gql",

    // Docs
    ".md", ".mdx",
    ".txt",                     // requirements.txt etc
]);

const filterImportantFiles = (files: string[]): string[] => {
    return files.filter(file => {
        const name = file.split("/").pop() || "";

        // Always include special named files
        if (ALWAYS_INCLUDE_NAMES.has(name)) return true;

        // Reject anything matching ignore patterns
        if (IGNORED_PATTERNS.some(pattern => pattern.test(file))) return false;

        // Must have an allowed extension
        const hasAllowed = Array.from(ALLOWED_EXTENSIONS).some(ext =>
            file.toLowerCase().endsWith(ext)
        );
        return hasAllowed;
    });
};

// ─── Types & Config ──────────────────────────────────────────────────────────

type DocType =
    | "system_e2e" | "function_docs" | "class_docs" | "module_docs" | "api_docs"
    | "readme" | "changelog" | "architecture" | "db_schema"
    | "env_docs" | "onboarding";

type FormatType = "markdown" | "jsdoc" | "docstring" | "openapi";

interface DocTypeConfig {
    id: DocType;
    label: string;
    description: string;
    icon: React.ReactNode;
    needsFile: boolean;
    formats: FormatType[];
}

const DOC_TYPES: DocTypeConfig[] = [
    { id: "system_e2e", label: "Complete System Flow", description: "End-to-End application documentation", icon: <Layers className="w-5 h-5 text-emerald-600" />, needsFile: true, formats: ["markdown"] },
    { id: "architecture", label: "Architecture", description: "System overview diagrams", icon: <Cpu className="w-5 h-5" />, needsFile: false, formats: ["markdown"] },
    { id: "api_docs", label: "API Reference", description: "REST endpoint documentation", icon: <Terminal className="w-5 h-5" />, needsFile: false, formats: ["markdown", "openapi"] },
    { id: "db_schema", label: "DB Schema", description: "Database models docs", icon: <Database className="w-5 h-5" />, needsFile: false, formats: ["markdown"] },
    { id: "module_docs", label: "Module Overview", description: "Module-level documentation", icon: <FileText className="w-5 h-5" />, needsFile: true, formats: ["markdown"] },
    { id: "function_docs", label: "Function Docs", description: "Document functions & methods", icon: <Code2 className="w-5 h-5" />, needsFile: false, formats: ["markdown", "jsdoc", "docstring"] },
    { id: "class_docs", label: "Class Docs", description: "Document classes & members", icon: <Layout className="w-5 h-5" />, needsFile: false, formats: ["markdown", "docstring"] },
    { id: "readme", label: "README", description: "Full project README", icon: <BookOpen className="w-5 h-5" />, needsFile: false, formats: ["markdown"] },
    { id: "changelog", label: "Changelog", description: "Generate from commits", icon: <GitCommit className="w-5 h-5" />, needsFile: false, formats: ["markdown"] },
    { id: "onboarding", label: "Onboarding", description: "New developer guide", icon: <Users className="w-5 h-5" />, needsFile: false, formats: ["markdown"] },
];

// ─── Diagram & Tree Components ───────────────────────────────────────────────

const MermaidDiagram = ({ code, isStreaming }: { code: string; isStreaming: boolean }) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const [renderState, setRenderState] = useState<"idle" | "loading" | "done" | "error">("idle");
    const [zoom, setZoom] = useState(1);
    const renderAttemptRef = useRef(0);

    useEffect(() => {
        // Don't attempt render while streaming — diagram is likely incomplete
        if (isStreaming) return;
        if (!code?.trim() || !containerRef.current) return;

        // Debounce: wait 300ms after last change before rendering
        const attempt = ++renderAttemptRef.current;
        const timer = setTimeout(async () => {
            if (attempt !== renderAttemptRef.current) return;
            setRenderState("loading");
            try {
                // Unique ID to avoid mermaid cache collisions
                const id = `mermaid-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
                const { svg } = await mermaid.render(id, code);
                if (attempt !== renderAttemptRef.current) return; // stale
                if (containerRef.current) {
                    containerRef.current.innerHTML = svg;
                    const svgEl = containerRef.current.querySelector("svg") as unknown as HTMLElement | null;
                    if (svgEl) {
                        svgEl.style.maxWidth = "100%";
                        svgEl.style.height = "auto";
                        svgEl.style.transformOrigin = "top center";
                    }
                }
                setRenderState("done");
            } catch (e) {
                console.warn("[mermaid] render error:", e);
                setRenderState("error");
            }
        }, 300);

        return () => clearTimeout(timer);
    }, [code, isStreaming]);

    useEffect(() => {
        const svgEl = containerRef.current?.querySelector("svg") as unknown as HTMLElement | null;
        if (svgEl) svgEl.style.transform = `scale(${zoom})`;
    }, [zoom]);

    // While streaming: show the raw code as a placeholder
    if (isStreaming) {
        return (
            <div className="my-6 bg-white/40 rounded-xl border border-[#0E1B2E]/10 p-4">
                <div className="flex items-center gap-2 mb-3">
                    <div className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-[#0E1B2E]/40" />
                    <span className={`text-[11px] font-bold text-[#0E1B2E]/40 uppercase tracking-widest ${firaCode.className}`}>
                        Building diagram...
                    </span>
                </div>
                <pre className={`text-[11px] text-[#0E1B2E]/30 overflow-hidden max-h-24 ${firaCode.className}`}>
                    {code.slice(0, 200)}{code.length > 200 ? "…" : ""}
                </pre>
            </div>
        );
    }

    // Error: show raw code block as fallback (never blank)
    if (renderState === "error") {
        return (
            <div className="my-6 rounded-xl overflow-hidden border border-[#0E1B2E]/10 shadow-sm bg-white/60 backdrop-blur-md">
                <div className="flex items-center justify-between px-4 py-2 bg-white/80 border-b border-[#0E1B2E]/10">
                    <span className={`text-[11px] font-bold text-[#0E1B2E]/50 uppercase tracking-widest ${firaCode.className}`}>
                        mermaid
                    </span>
                    <span className={`text-[11px] text-amber-500 font-semibold ${firaCode.className}`}>
                        Could not render — showing source
                    </span>
                </div>
                <pre className={`p-5 text-[12px] leading-relaxed text-[#0E1B2E]/70 overflow-auto max-h-[400px] ${firaCode.className}`}>
                    {code}
                </pre>
            </div>
        );
    }

    return (
        <div className="my-6 bg-white/50 backdrop-blur-sm rounded-xl border border-[#0E1B2E]/10 shadow-sm relative overflow-hidden group">
            {renderState === "loading" && (
                <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-10 min-h-[120px]">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0E1B2E]" />
                </div>
            )}
            {renderState === "done" && (
                <div className="absolute top-3 right-3 z-20 flex items-center gap-1 bg-white/90 backdrop-blur-md rounded-lg p-1.5 border border-[#0E1B2E]/10 shadow-sm opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={() => setZoom(p => Math.max(0.3, p - 0.2))} className="p-1.5 hover:bg-[#0E1B2E]/5 rounded-md">
                        <ZoomOut className="w-4 h-4 text-[#0E1B2E]" />
                    </button>
                    <span className={`px-2 text-xs font-medium text-[#0E1B2E] min-w-[48px] text-center ${firaCode.className}`}>
                        {(zoom * 100).toFixed(0)}%
                    </span>
                    <button onClick={() => setZoom(p => Math.min(3, p + 0.2))} className="p-1.5 hover:bg-[#0E1B2E]/5 rounded-md">
                        <ZoomIn className="w-4 h-4 text-[#0E1B2E]" />
                    </button>
                    <div className="w-px h-4 bg-[#0E1B2E]/10 mx-1" />
                    <button onClick={() => setZoom(1)} className="p-1.5 hover:bg-[#0E1B2E]/5 rounded-md">
                        <RotateCcw className="w-4 h-4 text-[#0E1B2E]" />
                    </button>
                </div>
            )}
            <div className="p-6 overflow-auto" style={{ minHeight: 120, maxHeight: 600 }}>
                <div ref={containerRef} className="flex justify-center" />
            </div>
        </div>
    );
};

function buildTree(files: string[]) {
    const root: Record<string, any> = {};
    for (const f of files) {
        const parts = f.split("/");
        let node = root;
        for (const part of parts) {
            node[part] = node[part] || {};
            node = node[part];
        }
    }
    return root;
}

function FileTreeNode({
    name, node, depth, path, selected, onSelect,
}: {
    name: string; node: Record<string, any>; depth: number; path: string; selected: string | null; onSelect: (p: string) => void;
}) {
    const [open, setOpen] = useState(depth < 1);
    const isLeaf = Object.keys(node).length === 0;
    const isSelected = selected === path;

    if (isLeaf) {
        return (
            <motion.button
                initial={{ opacity: 0, x: -5 }}
                animate={{ opacity: 1, x: 0 }}
                onClick={() => onSelect(path)}
                className={`w-full text-left flex items-center gap-2 py-1.5 px-2 rounded-md text-[13px] transition-all relative group ${isSelected
                    ? "text-[#0E1B2E] font-bold bg-[#0E1B2E]/10 backdrop-blur-sm"
                    : "text-[#0E1B2E]/70 hover:text-[#0E1B2E] hover:bg-white/50"
                    } ${firaCode.className}`}
            >
                <div className="absolute left-0 top-0 bottom-0 flex" style={{ width: depth * 14, paddingLeft: 6 }}>
                    {Array.from({ length: depth }).map((_, i) => (
                        <div key={i} className="h-full border-l border-[#0E1B2E]/10" style={{ marginLeft: 13 }} />
                    ))}
                </div>
                <div className="flex items-center gap-2 relative z-10" style={{ marginLeft: depth * 14 }}>
                    <FileCode className={`w-3.5 h-3.5 flex-shrink-0 ${isSelected ? "text-[#0E1B2E]" : "text-[#0E1B2E]/40"}`} />
                    <span className="truncate">{name}</span>
                </div>
                {isSelected && (
                    <motion.div layoutId="file-selector" className="absolute left-0 top-1.5 bottom-1.5 w-[3px] bg-[#0E1B2E] rounded-r-full shadow-[0_0_8px_rgba(14,27,46,0.4)]" />
                )}
            </motion.button>
        );
    }

    return (
        <div className="relative">
            <button
                onClick={() => setOpen(o => !o)}
                className={`w-full text-left flex items-center gap-1.5 py-1.5 px-2 rounded-md text-[13px] font-semibold text-[#0E1B2E]/90 hover:bg-white/40 transition-all group ${spaceGrotesk.className}`}
            >
                <div className="absolute left-0 top-0 bottom-0 flex" style={{ width: depth * 14, paddingLeft: 6 }}>
                    {Array.from({ length: depth }).map((_, i) => (
                        <div key={i} className="h-full border-l border-[#0E1B2E]/10" style={{ marginLeft: 13 }} />
                    ))}
                </div>
                <div className="flex items-center gap-1.5 relative z-10" style={{ marginLeft: depth * 14 }}>
                    <div className="w-4 h-4 flex items-center justify-center text-[#0E1B2E]/40 group-hover:text-[#0E1B2E] transition-colors">
                        {open ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                    </div>
                    {open ? <FolderOpen className="w-3.5 h-3.5 text-[#0E1B2E]/60" /> : <Folder className="w-3.5 h-3.5 text-[#0E1B2E]/60" />}
                    <span className="truncate">{name}</span>
                </div>
            </button>
            <AnimatePresence>
                {open && (
                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                        {Object.entries(node).map(([k, v]) => (
                            <FileTreeNode key={k} name={k} node={v as any} depth={depth + 1} path={path ? `${path}/${k}` : k} selected={selected} onSelect={onSelect} />
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

function DocMarkdown({ content, isStreaming }: { content: string; isStreaming: boolean }) {
    return (
        <div className="markdown-content prose prose-sm max-w-none antialiased overflow-x-auto">
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight]}  // ← removed rehypeRaw: causes <deeplinkservice> false-positive
                components={{
                    h1: ({ node, ...props }) => (
                        <h1 className={`text-3xl font-black text-[#0E1B2E] mb-6 mt-8 tracking-tight first:mt-0 pb-4 border-b border-[#0E1B2E]/10 ${spaceGrotesk.className}`} {...props} />
                    ),
                    h2: ({ node, ...props }) => (
                        <h2 className={`text-2xl font-bold text-[#0E1B2E] mb-4 mt-8 tracking-tight first:mt-0 ${spaceGrotesk.className}`} {...props} />
                    ),
                    h3: ({ node, ...props }) => (
                        <h3 className={`text-xl font-semibold text-[#0E1B2E] mb-3 mt-6 tracking-tight first:mt-0 ${spaceGrotesk.className}`} {...props} />
                    ),
                    h4: ({ node, ...props }) => (
                        <h4 className={`text-lg font-semibold text-[#0E1B2E] mb-2 mt-5 ${spaceGrotesk.className}`} {...props} />
                    ),
                    p: ({ node, ...props }) => (
                        <p className={`text-[#0E1B2E]/80 leading-relaxed mb-5 text-[15px] ${spaceGrotesk.className}`} {...props} />
                    ),
                    ul: ({ node, ...props }) => (
                        <ul className={`list-disc list-outside ml-5 space-y-2 mb-6 text-[#0E1B2E]/80 ${spaceGrotesk.className}`} {...props} />
                    ),
                    ol: ({ node, ...props }) => (
                        <ol className={`list-decimal list-outside ml-5 space-y-2 mb-6 text-[#0E1B2E]/80 ${spaceGrotesk.className}`} {...props} />
                    ),
                    li: ({ node, ...props }) => (
                        <li className={`text-[15px] leading-relaxed ${spaceGrotesk.className}`} {...props} />
                    ),
                    table: ({ node, ...props }) => (
                        <div className="overflow-x-auto my-6 rounded-xl border border-[#0E1B2E]/10">
                            <table className="w-full text-sm" {...props} />
                        </div>
                    ),
                    th: ({ node, ...props }) => (
                        <th className={`px-4 py-3 bg-[#0E1B2E]/5 text-left font-bold text-[#0E1B2E] text-[13px] border-b border-[#0E1B2E]/10 ${spaceGrotesk.className}`} {...props} />
                    ),
                    td: ({ node, ...props }) => (
                        <td className={`px-4 py-3 text-[#0E1B2E]/75 text-[13px] border-b border-[#0E1B2E]/5 ${spaceGrotesk.className}`} {...props} />
                    ),
                    blockquote: ({ node, ...props }) => (
                        <blockquote className="border-l-4 border-[#0E1B2E]/20 pl-4 my-4 text-[#0E1B2E]/60 italic" {...props} />
                    ),
                    hr: () => <hr className="border-[#0E1B2E]/10 my-8" />,
                    code: ({ node, inline, className, children, ...props }: any) => {
                        const match = /language-(\w+)/.exec(className || "");
                        const language = match ? match[1] : "";

                        // Mermaid — pass isStreaming to defer render
                        if (!inline && language === "mermaid") {
                            const code = String(children ?? "").replace(/\n$/, "").trim();
                            return code ? <MermaidDiagram code={code} isStreaming={isStreaming} /> : null;
                        }

                        // Fenced code block
                        if (!inline && match) {
                            return (
                                <div className="my-6 rounded-xl overflow-hidden border border-[#0E1B2E]/10 shadow-sm bg-white/60 backdrop-blur-md">
                                    <div className="flex items-center justify-between px-4 py-2 bg-white/80 border-b border-[#0E1B2E]/10">
                                        <span className={`text-[11px] font-bold text-[#0E1B2E]/50 uppercase tracking-widest ${firaCode.className}`}>
                                            {language}
                                        </span>
                                    </div>
                                    <div className="relative max-h-[500px] overflow-auto">
                                        <pre className="p-5 text-[13px] leading-relaxed">
                                            <code className={`${className} ${firaCode.className} text-[#0E1B2E]/90`} {...props}>
                                                {children}
                                            </code>
                                        </pre>
                                    </div>
                                </div>
                            );
                        }

                        // Inline code — sanitize: don't let class/function names become HTML tags
                        const raw = String(children ?? "");
                        return (
                            <code
                                className={`px-1.5 py-0.5 bg-[#0E1B2E]/5 border border-[#0E1B2E]/10 text-[#0E1B2E] font-semibold rounded-[4px] text-[13px] ${firaCode.className}`}
                                {...props}
                            >
                                {raw}
                            </code>
                        );
                    },
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function AutoDocumentationPage() {
    const router = useRouter();
    const { user } = useAuth();

    const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    const [selectedDocType, setSelectedDocType] = useState<DocType>("system_e2e");
    const [selectedFile, setSelectedFile] = useState<string | null>(null);
    const [format, setFormat] = useState<FormatType>("markdown");

    const [files, setFiles] = useState<string[]>([]);
    const [coverage, setCoverage] = useState<any>(null);
    const [streamedContent, setStreamedContent] = useState("");
    const [isGenerating, setIsGenerating] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [editedContent, setEditedContent] = useState("");
    const [copiedId, setCopiedId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loadingFiles, setLoadingFiles] = useState(false);

    const abortRef = useRef<AbortController | null>(null);
    const outputRef = useRef<HTMLDivElement>(null);

    const docTypeConfig = DOC_TYPES.find(d => d.id === selectedDocType)!;
    const displayContent = isEditing ? editedContent : streamedContent;

    useEffect(() => {
        if (!user?.username) return;
        fetchFiles();
        fetchCoverage();
    }, [user]);

    useEffect(() => {
        if (streamedContent && !isGenerating) {
            setStreamedContent("");
            setEditedContent("");
            setIsEditing(false);
        }
    }, [selectedFile, selectedDocType]);

    const fetchFiles = async () => {
        setLoadingFiles(true);
        try {
            const res = await fetch(`${baseURL}/docs/files?username=${encodeURIComponent(user?.username || "")}`);
            const data = await res.json();
            // Apply aggressive filtering to hide junk files
            const importantFiles = filterImportantFiles(data.files || []);
            setFiles(importantFiles);
        } catch (e) {
            console.error("Failed to fetch files:", e);
        } finally {
            setLoadingFiles(false);
        }
    };

    const fetchCoverage = async () => {
        try {
            const res = await fetch(`${baseURL}/docs/coverage?username=${encodeURIComponent(user?.username || "")}`);
            const data = await res.json();
            setCoverage(data.function_coverage);
        } catch (e) {
            console.error("Failed to fetch coverage:", e);
        }
    };

    useEffect(() => {
        if (!docTypeConfig.needsFile) setSelectedFile(null);
        if (!docTypeConfig.formats.includes(format)) {
            setFormat(docTypeConfig.formats[0]);
        }
    }, [selectedDocType]);

    const generate = async () => {
        if (isGenerating) {
            abortRef.current?.abort();
            setIsGenerating(false);
            return;
        }

        setError(null);
        setStreamedContent("");
        setIsEditing(false);
        setEditedContent("");
        setIsGenerating(true);

        const controller = new AbortController();
        abortRef.current = controller;

        try {
            const body: any = { doc_type: selectedDocType, format, username: user?.username || "", options: {} };
            if (selectedFile) body.target = selectedFile;

            const response = await fetch(`${baseURL}/docs/generate`, {
                method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal: controller.signal,
            });

            if (!response.ok || !response.body) throw new Error("HTTP Error");

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = ""; let accumulated = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() ?? "";

                for (const line of lines) {
                    if (!line.startsWith("data: ")) continue;
                    const raw = line.slice(6).trim();
                    if (!raw || raw === "[DONE]") continue;
                    try {
                        const chunk = JSON.parse(raw);
                        if (chunk.type === "token") {
                            accumulated += chunk.content;
                            setStreamedContent(accumulated);
                            if (outputRef.current) outputRef.current.scrollTop = outputRef.current.scrollHeight;
                        }
                        if (chunk.type === "error") setError(chunk.content);
                        if (chunk.type === "done") { setIsGenerating(false); fetchCoverage(); }
                    } catch { }
                }
            }
        } catch (e: any) {
            if (e.name !== "AbortError") setError(e.message || "Generation failed");
        } finally {
            setIsGenerating(false);
        }
    };

    const generateGlobalArchitecture = async () => {
        // Switch to architecture doc type, clear file selection, then generate
        setSelectedDocType("architecture");
        setSelectedFile(null);
        setStreamedContent("");
        setEditedContent("");
        setIsEditing(false);
        setError(null);

        // Small tick to let state settle before firing
        await new Promise(r => setTimeout(r, 50));

        setIsGenerating(true);
        const controller = new AbortController();
        abortRef.current = controller;

        try {
            const body = {
                doc_type: "architecture",
                format: "markdown",
                username: user?.username || "",
                options: {},
                // no target — backend uses full system mode
            };

            const response = await fetch(`${baseURL}/docs/generate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
                signal: controller.signal,
            });

            if (!response.ok || !response.body) throw new Error("HTTP Error");

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = ""; let accumulated = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() ?? "";

                for (const line of lines) {
                    if (!line.startsWith("data: ")) continue;
                    const raw = line.slice(6).trim();
                    if (!raw || raw === "[DONE]") continue;
                    try {
                        const chunk = JSON.parse(raw);
                        if (chunk.type === "token") {
                            accumulated += chunk.content;
                            setStreamedContent(accumulated);
                            if (outputRef.current) outputRef.current.scrollTop = outputRef.current.scrollHeight;
                        }
                        if (chunk.type === "error") setError(chunk.content);
                        if (chunk.type === "done") { setIsGenerating(false); fetchCoverage(); }
                    } catch { }
                }
            }
        } catch (e: any) {
            if (e.name !== "AbortError") setError(e.message || "Generation failed");
        } finally {
            setIsGenerating(false);
        }
    };


    const copyOutput = () => {
        navigator.clipboard.writeText(displayContent);
        setCopiedId("output");
        setTimeout(() => setCopiedId(null), 2000);
    };

    const downloadOutput = () => {
        const ext = format === "openapi" ? "yaml" : "md";
        const a = document.createElement("a");
        a.href = URL.createObjectURL(new Blob([displayContent], { type: "text/plain" }));
        a.download = `${selectedDocType}_docs.${ext}`;
        a.click();
    };

    const coveragePct = coverage?.coverage_pct ?? 0;
    const dashOffset = (2 * Math.PI * 36) - (coveragePct / 100) * (2 * Math.PI * 36);
    const fileTree = buildTree(files);
    const canGenerate = !docTypeConfig.needsFile || selectedFile;

    return (
        <div className="flex h-screen bg-[#F0F2F5] text-[#0E1B2E] antialiased relative selection:bg-[#0E1B2E] selection:text-white overflow-hidden">

            {/* ── ARCHITECTURAL GRID BACKGROUND ── */}
            <div className="fixed inset-0 pointer-events-none z-0">
                <div
                    className="absolute inset-0 opacity-[0.4]"
                    style={{
                        backgroundImage: `linear-gradient(to right, #0E1B2E15 1px, transparent 1px), linear-gradient(to bottom, #0E1B2E15 1px, transparent 1px)`,
                        backgroundSize: `40px 40px`
                    }}
                />
                <div className="absolute inset-0 bg-gradient-to-br from-transparent via-white/40 to-white/10" />
            </div>

            {/* ── LEFT PANEL: Explorer (Glassmorphism) ── */}
            {/* ── LEFT PANEL: Explorer ── */}
            <div className="w-[300px] bg-white/60 backdrop-blur-2xl border-r border-[#0E1B2E]/15 flex flex-col z-10 flex-shrink-0 shadow-[4px_0_30px_rgba(14,27,46,0.03)] relative">
                <div className="p-5 border-b border-[#0E1B2E]/10 flex-shrink-0 bg-white/40">
                    <button onClick={() => router.back()} className="flex items-center gap-2 mb-6 text-[#0E1B2E]/50 hover:text-[#0E1B2E] transition-colors group">
                        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                        <span className={`text-sm font-semibold ${spaceGrotesk.className}`}>Back to Suite</span>
                    </button>
                    <div className="flex items-center justify-between">
                        <h2 className={`text-sm font-bold text-[#0E1B2E] uppercase tracking-widest ${firaCode.className}`}>Explorer</h2>
                        <button onClick={fetchFiles} className="p-1.5 hover:bg-white/60 rounded-md transition-colors text-[#0E1B2E]/50 hover:text-[#0E1B2E] shadow-sm">
                            <RefreshCw className={`w-3.5 h-3.5 ${loadingFiles ? "animate-spin" : ""}`} />
                        </button>
                    </div>
                </div>

                {/* File tree — scrollable */}
                <div className="flex-1 overflow-y-auto p-3 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
                    {loadingFiles ? (
                        <div className="flex flex-col items-center justify-center h-40 gap-3 text-[#0E1B2E]/40">
                            <Loader2 className="w-5 h-5 animate-spin" />
                        </div>
                    ) : (
                        <div className="pb-4">
                            {Object.entries(fileTree).map(([k, v]) => (
                                <FileTreeNode key={k} name={k} node={v as any} depth={0} path={k} selected={selectedFile} onSelect={setSelectedFile} />
                            ))}
                        </div>
                    )}
                </div>

                {/* ── Full System Architecture button — pinned to bottom of explorer ── */}
                <div className="flex-shrink-0 p-4 border-t border-[#0E1B2E]/10 bg-white/40 backdrop-blur-md">
                    <button
                        onClick={isGenerating ? () => { abortRef.current?.abort(); setIsGenerating(false); } : generateGlobalArchitecture}
                        className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl border font-semibold text-[13px] transition-all duration-200 group ${isGenerating && selectedDocType === "architecture" && !selectedFile
                            ? "bg-red-500 border-red-500 text-white shadow-lg shadow-red-500/20"
                            : "bg-white/80 border-[#0E1B2E]/15 text-[#0E1B2E] hover:border-[#0E1B2E]/40 hover:bg-white shadow-sm"
                            } ${spaceGrotesk.className}`}
                    >
                        <div className={`p-1.5 rounded-lg transition-colors flex-shrink-0 ${isGenerating && selectedDocType === "architecture" && !selectedFile
                            ? "bg-white/20"
                            : "bg-[#0E1B2E]/5 group-hover:bg-[#0E1B2E]/10"
                            }`}>
                            {isGenerating && selectedDocType === "architecture" && !selectedFile
                                ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                : <Cpu className="w-3.5 h-3.5" />
                            }
                        </div>
                        <div className="flex flex-col items-start min-w-0">
                            <span className="leading-tight">
                                {isGenerating && selectedDocType === "architecture" && !selectedFile
                                    ? "Abort Generation"
                                    : "Full System Architecture"
                                }
                            </span>
                        </div>
                    </button>
                </div>
            </div>


            {/* ── CENTER PANEL: Canvas ── */}
            <div className="flex-1 flex flex-col relative z-10 min-w-0 bg-transparent">

                {/* Canvas Header */}
                <div className="h-[72px] px-8 border-b border-[#0E1B2E]/15 flex items-center justify-between flex-shrink-0 bg-white/80 backdrop-blur-xl shadow-sm">
                    <div className="flex items-center gap-3 min-w-0">
                        <div className="p-2.5 bg-[#0E1B2E]/5 rounded-xl border border-[#0E1B2E]/10 text-[#0E1B2E]">
                            {docTypeConfig.icon}
                        </div>
                        <div className="min-w-0 flex flex-col justify-center">
                            <h2 className={`text-[15px] font-bold text-[#0E1B2E] leading-tight ${spaceGrotesk.className}`}>{docTypeConfig.label}</h2>
                            <div className={`text-xs text-[#0E1B2E]/50 truncate flex items-center gap-1.5 mt-0.5 ${firaCode.className}`}>
                                <span>Target:</span>
                                {selectedFile ? <span className="text-[#0E1B2E]/80 font-bold">{selectedFile}</span> : <span className="italic">Global App Scope</span>}
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-3 flex-shrink-0">
                        {streamedContent && !isGenerating && (
                            <button onClick={() => { if (!isEditing) setEditedContent(streamedContent); setIsEditing(e => !e); }}
                                className={`text-sm px-4 py-2 rounded-xl font-bold transition-all ${spaceGrotesk.className} ${isEditing ? "bg-[#0E1B2E] text-white shadow-md shadow-[#0E1B2E]/20" : "bg-white/80 text-[#0E1B2E] border border-[#0E1B2E]/15 hover:border-[#0E1B2E]/40"}`}
                            >
                                {isEditing ? "Preview Changes" : "Edit Markdown"}
                            </button>
                        )}
                        {displayContent && (
                            <div className="flex items-center gap-2 border-l border-[#0E1B2E]/10 pl-3">
                                <button onClick={copyOutput} className="p-2.5 rounded-xl bg-white/80 border border-[#0E1B2E]/15 hover:border-[#0E1B2E]/40 transition-all shadow-sm"><Copy className="w-4 h-4 text-[#0E1B2E]" /></button>
                                <button onClick={downloadOutput} className="p-2.5 rounded-xl bg-white/80 border border-[#0E1B2E]/15 hover:border-[#0E1B2E]/40 transition-all shadow-sm"><Download className="w-4 h-4 text-[#0E1B2E]" /></button>
                            </div>
                        )}
                    </div>
                </div>

                {/* Canvas Workspace */}
                <div ref={outputRef} className="flex-1 overflow-y-auto p-8 xl:p-12 scroll-smooth">
                    {!streamedContent && !isGenerating ? (
                        <div className="flex flex-col items-center justify-center h-full max-w-lg mx-auto text-center">
                            {!canGenerate ? (
                                <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="flex flex-col items-center">
                                    <div className="w-20 h-20 bg-white/60 backdrop-blur-md rounded-3xl flex items-center justify-center mb-6 shadow-sm border border-[#0E1B2E]/10 text-[#0E1B2E]/40">
                                        <Search className="w-8 h-8" />
                                    </div>
                                    <h2 className={`text-3xl font-black text-[#0E1B2E] tracking-tight mb-3 ${spaceGrotesk.className}`}>Select a Target</h2>
                                    <p className={`text-[15px] text-[#0E1B2E]/60 leading-relaxed ${spaceGrotesk.className}`}>
                                        The <strong>{docTypeConfig.label}</strong> template requires a specific file context. Please select a file from the Explorer on the left.
                                    </p>
                                </motion.div>
                            ) : (
                                <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="flex flex-col items-center">
                                    <div className="w-20 h-20 bg-white/80 backdrop-blur-md rounded-3xl flex items-center justify-center mb-6 shadow-md border border-[#0E1B2E]/10 text-[#0E1B2E]">
                                        {docTypeConfig.id === "system_e2e" ? <Layers className="w-8 h-8 text-emerald-600" /> : <FileCheck2 className="w-8 h-8" />}
                                    </div>
                                    <h2 className={`text-3xl font-black text-[#0E1B2E] tracking-tight mb-3 ${spaceGrotesk.className}`}>
                                        {docTypeConfig.id === "system_e2e" ? "Global Context Ready" : "Target Acquired"}
                                    </h2>
                                    <p className={`text-[15px] text-[#0E1B2E]/70 leading-relaxed mb-8 ${spaceGrotesk.className}`}>
                                        Ready to execute <strong>{docTypeConfig.label}</strong> generation for {selectedFile ? <span className="font-semibold bg-white/50 px-2 py-0.5 rounded border border-[#0E1B2E]/10">{selectedFile}</span> : "the complete application architecture"}.
                                    </p>

                                    <button
                                        onClick={generate}
                                        className={`flex items-center gap-2 px-8 py-4 rounded-xl font-bold text-base transition-all shadow-xl shadow-[#0E1B2E]/10 bg-[#0E1B2E] text-white hover:bg-[#1a2f4d] hover:-translate-y-1 ${spaceGrotesk.className}`}
                                    >
                                        <Sparkles className="w-5 h-5" /> Initialize Generation
                                    </button>
                                </motion.div>
                            )}
                        </div>
                    ) : isEditing ? (
                        <div className="max-w-4xl mx-auto h-full pb-10">
                            <textarea
                                value={editedContent}
                                onChange={e => setEditedContent(e.target.value)}
                                className={`w-full h-full min-h-[600px] p-10 bg-white/95 backdrop-blur-2xl border border-[#0E1B2E]/15 shadow-2xl shadow-[#0E1B2E]/5 rounded-2xl text-[#0E1B2E] focus:outline-none focus:ring-4 focus:ring-[#0E1B2E]/5 resize-none text-[15px] leading-relaxed ${firaCode.className}`}
                                spellCheck={false}
                            />
                        </div>
                    ) : (
                        <div className="max-w-4xl mx-auto bg-white/95 backdrop-blur-2xl border border-[#0E1B2E]/15 shadow-2xl shadow-[#0E1B2E]/5 rounded-2xl p-10 xl:p-14 mb-10">
                            {isGenerating && (
                                <div className="flex items-center gap-3 mb-8 pb-6 border-b border-[#0E1B2E]/10">
                                    <div className="w-8 h-8 rounded-full bg-[#0E1B2E]/5 flex items-center justify-center">
                                        <Loader2 className="w-4 h-4 animate-spin text-[#0E1B2E]" />
                                    </div>
                                    <span className={`text-sm font-bold text-[#0E1B2E]/70 tracking-wide uppercase ${spaceGrotesk.className}`}>Synthesizing {docTypeConfig.label}...</span>
                                </div>
                            )}
                            <DocMarkdown content={streamedContent} isStreaming={isGenerating} />
                        </div>
                    )}
                </div>
            </div>

            {/* ── RIGHT PANEL: Inspector (Glassmorphism) ── */}
            <div className="w-[340px] bg-white/60 backdrop-blur-2xl border-l border-[#0E1B2E]/15 flex flex-col z-20 flex-shrink-0 shadow-[-4px_0_30px_rgba(14,27,46,0.03)] relative">
                <div className="h-[72px] px-6 border-b border-[#0E1B2E]/10 flex items-center flex-shrink-0 bg-white/40">
                    <h2 className={`text-sm font-bold text-[#0E1B2E] uppercase tracking-widest ${firaCode.className}`}>Inspector</h2>
                </div>

                <div className="flex-1 overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none] pb-28">

                    {/* Coverage Widget */}
                    <div className="p-6 border-b border-[#0E1B2E]/10">
                        <div className="bg-white/80 backdrop-blur-md rounded-2xl p-5 border border-[#0E1B2E]/15 shadow-sm relative overflow-hidden">
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <h3 className={`text-sm font-bold text-[#0E1B2E] ${spaceGrotesk.className}`}>Documentation</h3>
                                    <p className={`text-xs font-semibold text-[#0E1B2E]/50 mt-0.5 ${spaceGrotesk.className}`}>Global Coverage</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-6">
                                <div className="relative w-20 h-20 flex-shrink-0">
                                    <svg className="w-20 h-20 -rotate-90 transform origin-center" viewBox="0 0 80 80">
                                        <circle cx="40" cy="40" r="36" fill="none" stroke="#0E1B2E0A" strokeWidth="6" />
                                        <circle cx="40" cy="40" r="36" fill="none" stroke="#0E1B2E" strokeWidth="6" strokeDasharray={2 * Math.PI * 36} strokeDashoffset={dashOffset} strokeLinecap="round" className="transition-all duration-1000 ease-out" />
                                    </svg>
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <span className={`text-xl font-black text-[#0E1B2E] ${firaCode.className}`}>{coveragePct}%</span>
                                    </div>
                                </div>
                                <div className="flex-1 space-y-2.5">
                                    {[{ label: "Total", value: coverage?.total || 0, color: "bg-[#0E1B2E]/10" }, { label: "Done", value: coverage?.documented || 0, color: "bg-[#0E1B2E]" }].map(row => (
                                        <div key={row.label} className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <div className={`w-2 h-2 rounded-full ${row.color}`} />
                                                <span className={`text-xs font-bold text-[#0E1B2E]/60 ${spaceGrotesk.className}`}>{row.label}</span>
                                            </div>
                                            <span className={`text-xs font-bold text-[#0E1B2E] ${firaCode.className}`}>{row.value}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Doc Type Selector */}
                    <div className="p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className={`text-[11px] font-bold text-[#0E1B2E]/40 uppercase tracking-widest ${firaCode.className}`}>Template Type</h3>
                        </div>
                        <div className="flex flex-col gap-3">
                            {/* Prominent End-to-End Selector */}
                            {DOC_TYPES.slice(0, 1).map(dt => {
                                const isSelected = selectedDocType === dt.id;
                                return (
                                    <button
                                        key={dt.id}
                                        onClick={() => setSelectedDocType(dt.id)}
                                        className={`relative w-full flex items-center gap-4 text-left p-4 rounded-2xl border transition-all duration-200 group ${isSelected ? "bg-[#0E1B2E] border-[#0E1B2E] shadow-lg shadow-[#0E1B2E]/20" : "bg-white/80 border-[#0E1B2E]/15 hover:border-[#0E1B2E]/40"}`}
                                    >
                                        <div className={`p-2.5 rounded-xl transition-colors ${isSelected ? "bg-white/10 text-emerald-400" : "bg-emerald-50 border border-emerald-100"}`}>
                                            {dt.icon}
                                        </div>
                                        <div>
                                            <span className={`block text-[14px] font-bold leading-tight mb-0.5 ${spaceGrotesk.className} ${isSelected ? "text-white" : "text-[#0E1B2E]"}`}>{dt.label}</span>
                                            <span className={`block text-xs font-medium ${spaceGrotesk.className} ${isSelected ? "text-white/60" : "text-[#0E1B2E]/50"}`}>{dt.description}</span>
                                        </div>
                                    </button>
                                );
                            })}

                            <div className="h-px bg-[#0E1B2E]/10 my-1 w-full" />

                            <div className="grid grid-cols-2 gap-3">
                                {DOC_TYPES.slice(1).map(dt => {
                                    const isSelected = selectedDocType === dt.id;
                                    return (
                                        <button
                                            key={dt.id}
                                            onClick={() => setSelectedDocType(dt.id)}
                                            className={`relative flex flex-col items-start text-left p-3.5 rounded-2xl border transition-all duration-200 group ${isSelected ? "bg-[#0E1B2E] border-[#0E1B2E] shadow-lg shadow-[#0E1B2E]/20" : "bg-white/80 border-[#0E1B2E]/15 hover:border-[#0E1B2E]/40"}`}
                                        >
                                            <div className={`mb-3 p-2 rounded-xl inline-flex transition-colors ${isSelected ? "bg-white/10 text-white" : "bg-[#0E1B2E]/5 text-[#0E1B2E]"}`}>
                                                {dt.icon}
                                            </div>
                                            <span className={`text-[12px] font-bold leading-tight ${spaceGrotesk.className} ${isSelected ? "text-white" : "text-[#0E1B2E]"}`}>{dt.label}</span>
                                        </button>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Fixed Action Bottom Bar */}
                <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-white/90 via-white/80 to-transparent backdrop-blur-md">
                    <button
                        onClick={generate}
                        disabled={!canGenerate && !isGenerating}
                        className={`relative w-full flex items-center justify-center gap-2 px-6 py-4 rounded-xl font-bold text-[15px] transition-all duration-300 shadow-xl ${spaceGrotesk.className} ${isGenerating ? "bg-red-500 hover:bg-red-600 text-white shadow-red-500/20" : !canGenerate ? "bg-[#0E1B2E]/10 text-[#0E1B2E]/40 cursor-not-allowed shadow-none border border-[#0E1B2E]/5" : "bg-[#0E1B2E] text-white hover:bg-[#1a2f4d] shadow-[#0E1B2E]/20 hover:-translate-y-0.5"}`}
                    >
                        {isGenerating ? <><Loader2 className="w-5 h-5 animate-spin" /> Abort</> : !canGenerate ? "Select File" : <><Zap className="w-5 h-5" /> Generate Docs</>}
                    </button>
                </div>
            </div>
        </div>
    );
}