"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  Database,
  Code2,
  Sparkles,
  FileCode,
  AlertCircle,
  GitPullRequest,
  GitCommit,
  Clock,
  Bot,
  Workflow,
  BarChart3,
  MessageSquare,
  ChevronRight,
  Loader2,
} from "lucide-react";
import { Space_Grotesk } from "next/font/google";

const spaceGrotesk = Space_Grotesk({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  display: "swap",
});

// ── Pattern-based dynamic status resolver ──────────────────────────────────
const STATUS_PATTERNS: Array<{
  pattern: RegExp;
  icon: () => React.ReactNode;
  color: string;
}> = [
  {
    pattern: /cache/i,
    icon: () => <Database className="w-4 h-4" />,
    color: "text-blue-500",
  },
  {
    pattern: /classif/i,
    icon: () => <Code2 className="w-4 h-4" />,
    color: "text-indigo-500",
  },
  {
    pattern: /understand|rewrit/i,
    icon: () => <Sparkles className="w-4 h-4" />,
    color: "text-purple-500",
  },
  {
    pattern: /retriev|search|context/i,
    icon: () => <FileCode className="w-4 h-4" />,
    color: "text-cyan-500",
  },
  {
    pattern: /issue\s*#?\d+/i,
    icon: () => <AlertCircle className="w-4 h-4" />,
    color: "text-red-500",
  },
  {
    pattern: /pr\s*#?\d+|pull request\s*#?\d+/i,
    icon: () => <GitPullRequest className="w-4 h-4" />,
    color: "text-green-500",
  },
  {
    pattern: /commit/i,
    icon: () => <GitCommit className="w-4 h-4" />,
    color: "text-slate-500",
  },
  {
    pattern: /chronolog|timeline/i,
    icon: () => <Clock className="w-4 h-4" />,
    color: "text-orange-500",
  },
  {
    pattern: /generat|answer|respond/i,
    icon: () => <Bot className="w-4 h-4" />,
    color: "text-purple-500",
  },
  {
    pattern: /tutorial/i,
    icon: () => <Workflow className="w-4 h-4" />,
    color: "text-pink-500",
  },
  {
    pattern: /sub.?quer|sub.?question|split/i,
    icon: () => <BarChart3 className="w-4 h-4" />,
    color: "text-teal-500",
  },
  {
    pattern: /cached|⚡/i,
    icon: () => <Sparkles className="w-4 h-4" />,
    color: "text-yellow-500",
  },
  {
    pattern: /greeting|👋/i,
    icon: () => <MessageSquare className="w-4 h-4" />,
    color: "text-emerald-500",
  },
  {
    pattern: /expand|keyword/i,
    icon: () => <ChevronRight className="w-4 h-4" />,
    color: "text-slate-500",
  },
];

const getStatusConfig = (status: string) => {
  if (!status) {
    return {
      icon: <Loader2 className="w-4 h-4 animate-spin" />,
      color: "text-[#0E1B2E]",
    };
  }
  for (const { pattern, icon, color } of STATUS_PATTERNS) {
    if (pattern.test(status)) return { icon: icon(), color };
  }
  return {
    icon: <Loader2 className="w-4 h-4 animate-spin" />,
    color: "text-[#0E1B2E]",
  };
};

// ── Component ───────────────────────────────────────────────────────────────
interface StreamStatusLoaderProps {
  streamStatus: string;
}

export default function StreamStatusLoader({
  streamStatus,
}: StreamStatusLoaderProps) {
  const { icon, color } = getStatusConfig(streamStatus);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.2 }}
      className="flex gap-4"
    >
      {/* Bot avatar */}
      <div className="w-8 h-8 bg-[#0E1B2E] rounded-lg flex items-center justify-center flex-shrink-0 mt-1 shadow-md">
        <Bot className="w-5 h-5 text-white" />
      </div>

      {/* Status card */}
      <div className="p-4 bg-white/60 backdrop-blur-sm border border-[#0E1B2E]/10 rounded-2xl shadow-sm max-w-sm">
        <AnimatePresence mode="wait">
          <motion.div
            key={streamStatus}
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 6 }}
            transition={{ duration: 0.15 }}
            className="flex items-center gap-3"
          >
            {/* Dynamic icon */}
            <div className={`flex-shrink-0 ${color}`}>{icon}</div>

            {/* Status text + pulse dots */}
            <div className="flex flex-col gap-1">
              <span
                className={`text-sm font-medium text-[#0E1B2E] ${spaceGrotesk.className}`}
              >
                {streamStatus ||
                  "Searching through your codebase and related knowledge"}
              </span>
              <div className="flex items-center gap-1">
                {[0, 1, 2].map((i) => (
                  <motion.div
                    key={i}
                    className="w-1.5 h-1.5 rounded-full bg-[#0E1B2E]/40"
                    animate={{
                      opacity: [0.3, 1, 0.3],
                      scale: [0.8, 1.2, 0.8],
                    }}
                    transition={{
                      duration: 1.2,
                      repeat: Infinity,
                      delay: i * 0.2,
                      ease: "easeInOut",
                    }}
                  />
                ))}
              </div>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
