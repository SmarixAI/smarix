"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Stars } from "@react-three/drei";
import { motion } from "framer-motion";
import { useRef, useMemo } from "react";
import * as THREE from "three";
import Link from "next/link";
import {
  Code2,
  Zap,
  Brain,
  Search,
  GitBranch,
  MessageSquare,
  ArrowRight,
  Sparkles,
  LogIn,
} from "lucide-react";

function FloatingParticles() {
  const group = useRef<THREE.Group>(null);

  useFrame(() => {
    if (group.current) {
      group.current.rotation.y += 0.001;
      group.current.rotation.x += 0.0005;
    }
  });

  const particles = useMemo(() => {
    return Array.from({ length: 250 }, () => [
      (Math.random() - 0.5) * 60,
      (Math.random() - 0.5) * 40,
      (Math.random() - 0.5) * 60,
    ]);
  }, []);

  return (
    <group ref={group}>
      {particles.map((pos, i) => (
        <mesh key={i} position={pos as [number, number, number]}>
          <sphereGeometry args={[0.05, 8, 8]} />
          <meshStandardMaterial
            color={"#ffffff"}
            emissive="#60a5fa"
            emissiveIntensity={0.6}
          />
        </mesh>
      ))}
    </group>
  );
}

function HeroText() {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center z-30 px-4 pb-32 mb-20">
      <div className="max-w-5xl mx-auto text-center">
        {/* <motion.div
          initial={{ opacity: 0, y: 60 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1 }}
          className="mb-6 inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-500/10 to-purple-500/10 border border-cyan-400/30 rounded-full backdrop-blur-md"
        >
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <span className="text-sm text-cyan-300 font-medium">
            AI-Powered Codebase Intelligence
          </span>
        </motion.div> */}

        <motion.h1
          initial={{ opacity: 0, y: 60 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.2 }}
          className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-extrabold leading-tight mb-6"
        >
          <span className="text-transparent bg-clip-text bg-gradient-to-br from-cyan-400 via-indigo-400 to-purple-500 drop-shadow-lg">
            Your Codebase,
          </span>
          <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-cyan-400">
            Fully Understood
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.4 }}
          className="text-gray-300 text-base sm:text-lg md:text-lg mb-10 leading-relaxed"
        >
          Supercharge your development with AI-powered codebase intelligence.
          <br />
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.8 }}
          className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-20"
        >
          <div className="relative group">
            <motion.div
              animate={{
                scale: [1, 1.05, 1],
                opacity: [0.3, 0.6, 0.3],
              }}
              transition={{ repeat: Infinity, duration: 3 }}
              className="absolute -inset-1 rounded-full blur-xl bg-gradient-to-r from-purple-600 via-indigo-400 to-cyan-500 opacity-50"
            />
            <Link
              href="/login"
              className="relative z-20 flex items-center gap-2 px-6 sm:px-5 py-1 sm:py-2 bg-gradient-to-r from-cyan-500 to-purple-500 text-white text-xs sm:text-xs font-semibold rounded-full shadow-2xl transition-all duration-300 hover:shadow-cyan-500/50 hover:scale-105 group-hover:gap-3"
            >
              <MessageSquare className="w-4 h-4 sm:w-5 sm:h-5" />
              <span>Launch App</span>
            </Link>
          </div>

          <Link
            href="/demo"
            className="flex items-center gap-2 px-6 sm:px-5 py-1 sm:py-2 bg-white/5 border border-white/20 hover:border-cyan-400/60 text-white text-xs sm:text-xs font-medium rounded-full backdrop-blur-md transition-all duration-300 hover:bg-white/10"
          >
            <Search className="w-4 h-4 sm:w-5 sm:h-5" />
            <span>Watch Demo</span>
          </Link>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 1 }}
          className="flex flex-wrap justify-center gap-4 sm:gap-8 text-xs sm:text-sm text-gray-400"
        >
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span>Live AI-powered analysis</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-cyan-400 rounded-full" />
            <span>100% private & secure</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-purple-400 rounded-full" />
            <span>Works with any language</span>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

function TopBar() {
  return (
    <div className="absolute top-0 left-0 w-full px-4 sm:px-6 py-4 z-50 flex items-center justify-between backdrop-blur-sm border-b border-white/5">
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="flex items-center gap-2 sm:gap-3"
      >
        <img
          src="/logo.png"
          alt="Smarix Logo"
          className="w-5 h-5 sm:w-6 sm:h-6 object-contain"
        />
        <span className="text-white text-lg sm:text-xl font-bold tracking-tight">
          Smarix
        </span>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6, ease: "easeOut", delay: 0.2 }}
        className="flex items-center gap-3 sm:gap-4"
      >
        <Link
          href="/docs"
          className="hidden sm:block text-gray-300 hover:text-white transition-colors text-sm sm:text-base"
        >
          Docs
        </Link>
        <Link
          href="/pricing"
          className="hidden sm:block text-gray-300 hover:text-white transition-colors text-sm sm:text-base"
        >
          Pricing
        </Link>
        <Link
          href="/login"
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-600 hover:to-purple-600 text-white text-sm font-semibold rounded-lg shadow-lg transition-all duration-300 hover:shadow-cyan-500/50 hover:scale-105"
        >
          <LogIn className="w-4 h-4" />
          <span>Login</span>
        </Link>
      </motion.div>
    </div>
  );
}

function FeatureCards() {
  const features = [
    {
      icon: Brain,
      title: "Intelligent Chunking",
      description:
        "AST-based code analysis preserves semantic meaning and context",
      gradient: "from-cyan-500 to-blue-500",
    },
    {
      icon: Search,
      title: "Hybrid Search",
      description:
        "Combines semantic search with metadata filtering for precision",
      gradient: "from-purple-500 to-pink-500",
    },
    {
      icon: GitBranch,
      title: "Full Git Context",
      description: "Search through code, issues, PRs, and commits in one place",
      gradient: "from-indigo-500 to-cyan-500",
    },
    {
      icon: Zap,
      title: "Instant Answers",
      description:
        "Get accurate responses with actual code and file references",
      gradient: "from-pink-500 to-purple-500",
    },
  ];

  return (
    <div className="absolute bottom-4 sm:bottom-8 left-0 right-0 z-30 px-4">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, delay: 1.2 }}
        className="max-w-6xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4"
      >
        {features.map((feature, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 1.2 + i * 0.1 }}
            className="group relative"
          >
            <div
              className={`absolute -inset-0.5 bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-20 transition-opacity duration-300 rounded-xl blur-md`}
            />

            <div className="relative p-4 sm:p-5 bg-black/40 border border-white/10 rounded-xl backdrop-blur-md hover:bg-black/50 hover:border-white/20 transition-all duration-300 h-full">
              <div
                className={`w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br ${feature.gradient} rounded-lg flex items-center justify-center mb-3 sm:mb-4 group-hover:scale-110 transition-transform duration-300`}
              >
                <feature.icon className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
              </div>
              <h3 className="text-white font-semibold text-base sm:text-lg mb-2 leading-tight">
                {feature.title}
              </h3>
              <p className="text-gray-400 text-xs sm:text-sm leading-relaxed">
                {feature.description}
              </p>
            </div>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}

export default function HomeLandingPage() {
  return (
    <div className="relative h-screen w-screen bg-gradient-to-b from-black via-zinc-900 to-black overflow-hidden">
      <Canvas camera={{ position: [0, 0, 20], fov: 65 }}>
        <ambientLight intensity={1} />
        <pointLight position={[10, 10, 10]} intensity={2} />
        <Stars
          radius={150}
          depth={80}
          count={10000}
          factor={6}
          saturation={0}
          fade
          speed={1}
        />
        <FloatingParticles />
        <OrbitControls
          enableZoom={false}
          enablePan={false}
          mouseButtons={{
            LEFT: THREE.MOUSE.ROTATE,
            RIGHT: THREE.MOUSE.PAN,
          }}
        />
      </Canvas>

      <TopBar />
      <HeroText />
      <FeatureCards />

      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent pointer-events-none z-20" />
      <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-black/60 pointer-events-none z-10" />
    </div>
  );
}
