"use client";

import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import ModuleCard from "../cards/ReadingOverview/ModuleCard";
import OverviewModal from "../modals/ReadingOverview/ContentModal";
import { modules } from "../constants/ReadingOverview/modules";
import { useModuleContent } from "../hooks/ReadingOverview/useModuleContent";
import type { Module } from "../../../../types/onboarding";
import { Inter, JetBrains_Mono, Space_Grotesk } from "next/font/google";
// ✅ 1. Import Auth Context
import { useAuth } from "@/components/auth/AuthContext";

interface ReadingOverviewProps {
  employeeId?: string | null;
  activeRepos?: string[];
  onboardingData?: any;
  onUpdateProgress?: (section: string, itemId: string, updates: any) => void;
  onModalChange?: (isOpen: boolean) => void;
}

const spaceGrotesk = Space_Grotesk({ subsets: ["latin"] });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"] });
const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export default function ReadingOverview({
  employeeId,
  activeRepos: propActiveRepos = [], // Rename prop to avoid conflict
  onboardingData,
  onUpdateProgress,
  onModalChange,
}: ReadingOverviewProps) {
  // ✅ 2. Get User from Context
  const { user } = useAuth();

  // ✅ 3. Merge Prop with Auth Context (Fallback logic)
  const activeRepos =
    propActiveRepos.length > 0 ? propActiveRepos : user?.activeRepos || [];

  const [visibleModules, setVisibleModules] = useState<Set<string>>(
    new Set(modules.map((m) => `module-${m.id}`)),
  );
  const moduleRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedModule, setSelectedModule] = useState<Module | null>(null);
  const [darkMode, setDarkMode] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  const { content, isLoading, error, fetchContent, clearContent } =
    useModuleContent();

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        setVisibleModules((prevVisible) => {
          const newVisibleModules = new Set(prevVisible);
          let hasChanges = false;

          entries.forEach((entry) => {
            if (
              entry.isIntersecting &&
              !newVisibleModules.has(entry.target.id)
            ) {
              newVisibleModules.add(entry.target.id);
              hasChanges = true;
            }
          });

          return hasChanges ? newVisibleModules : prevVisible;
        });
      },
      { threshold: 0.1, rootMargin: "0px" },
    );

    Object.values(moduleRefs.current).forEach((ref) => {
      if (ref) observer.observe(ref);
    });

    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };

    window.addEventListener("mousemove", handleMouseMove);

    return () => {
      observer.disconnect();
      window.removeEventListener("mousemove", handleMouseMove);
    };
  }, []);

  const handleCardClick = useCallback(
    async (moduleId: string) => {
      const module = modules.find((m) => m.id === moduleId);
      if (!module || module.locked) return;

      setSelectedModule(module);
      setIsModalOpen(true);
      if (onModalChange) onModalChange(true);

      // ✅ 4. Use the derived activeRepos variable
      const repo = activeRepos.length > 0 ? activeRepos[0] : "";

      // Now this call primes the cache safely
      fetchContent(moduleId, repo);
    },
    [fetchContent, activeRepos, onModalChange],
  );

  const handleModalClose = useCallback(() => {
    setIsModalOpen(false);
    if (onModalChange) onModalChange(false);
    clearContent();
    setTimeout(() => setSelectedModule(null), 300);
  }, [clearContent, onModalChange]);

  const memoizedModules = useMemo(() => modules, []);

  return (
    // The wrapper must be flex-col and h-full to calculate the available space
    <div className="flex flex-col h-full w-full overflow-hidden">
      
      {/* HEADER SECTION - Kept compact */}
      <div className="flex-shrink-0 mb-4">
        <h2 className={`${inter.className} text-2xl font-semibold tracking-tight mb-1 text-[#0E1B2E]`}>
          Reading & Overview
        </h2>
        <p className={`${jetbrainsMono.className} text-sm text-[#0E1B2E]/60`}>
          Start your journey with these essential topics. Get familiar with the basics before diving deeper.
        </p>
      </div>

      {/* THE GRID - This is the critical change */}
      <div className="grid grid-cols-3 grid-rows-2 gap-4 flex-1 min-h-0 min-w-0 mb-4">
        {memoizedModules.map((module, index) => (
          <div 
            key={module.id} 
            // 'min-h-0' here allows the card to shrink smaller than the text inside it
            className="flex min-h-0 min-w-0"
            ref={(el) => {
              if (el) {
                moduleRefs.current[`module-${module.id}`] = el;
              }
            }}
          >
            <ModuleCard
              key={module.id}
              module={module}
              index={index}
              isVisible={visibleModules.has(`module-${module.id}`)}
              onCardClick={handleCardClick}
              darkMode={darkMode}
              mousePosition={mousePosition}
              // This prop must be used inside ModuleCard to set 'height: 100%'
              className="h-full w-full"
            />
          </div>
        ))}
      </div>

      {/* ERROR MESSAGE */}
      {error && (
        <div className="fixed bottom-6 right-6 z-50">
          <div className="px-5 py-4 rounded-xl shadow-xl bg-white text-red-600 border border-red-200 flex items-center gap-3">
            {error}
          </div>
        </div>
      )}

      {selectedModule && (
        <OverviewModal
          isOpen={isModalOpen}
          onClose={handleModalClose}
          title={selectedModule.title}
          moduleId={selectedModule.id}
          activeRepos={activeRepos}
          employeeId={employeeId || user?.employeeId}
          onProgressUpdate={onUpdateProgress}
        />
      )}
    </div>
  );
}
