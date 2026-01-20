'use client';

import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import ModuleCard from '../cards/ReadingOverview/ModuleCard';
import OverviewModal from '../modals/ReadingOverview/ContentModal';
import { modules } from '../constants/ReadingOverview/modules';
import { useModuleContent } from '../hooks/ReadingOverview/useModuleContent';
import type { Module } from '../../../../types/onboarding';
import { Inter, JetBrains_Mono, Space_Grotesk } from 'next/font/google';

interface ReadingOverviewProps {
  employeeId?: string | null;
  activeRepos?: string[];
  onboardingData?: any;
  onUpdateProgress?: (section: string, itemId: string, updates: any) => void;
  onModalChange?: (isOpen: boolean) => void; // New prop to notify parent
}

const spaceGrotesk = Space_Grotesk({ subsets: ['latin'] });
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'] });
const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700'] });

export default function ReadingOverview({ 
  employeeId, 
  activeRepos = [], 
  onboardingData, 
  onUpdateProgress,
  onModalChange // Destructure new prop
}: ReadingOverviewProps) {
  const [visibleModules, setVisibleModules] = useState<Set<string>>(
    new Set(modules.map(m => `module-${m.id}`))
  );
  const moduleRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedModule, setSelectedModule] = useState<Module | null>(null);
  const [darkMode, setDarkMode] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  
  const { content, isLoading, error, fetchContent, clearContent } = useModuleContent();

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        setVisibleModules((prevVisible) => {
          const newVisibleModules = new Set(prevVisible);
          let hasChanges = false;

          entries.forEach((entry) => {
            if (entry.isIntersecting && !newVisibleModules.has(entry.target.id)) {
              newVisibleModules.add(entry.target.id);
              hasChanges = true;
            }
          });

          return hasChanges ? newVisibleModules : prevVisible;
        });
      },
      { threshold: 0.1, rootMargin: '0px' }
    );

    Object.values(moduleRefs.current).forEach((ref) => {
      if (ref) observer.observe(ref);
    });

    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };

    window.addEventListener('mousemove', handleMouseMove);

    return () => {
      observer.disconnect();
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  const handleCardClick = useCallback(async (moduleId: string) => {
    const module = modules.find((m) => m.id === moduleId);
    if (!module || module.locked) return;

    setSelectedModule(module);
    setIsModalOpen(true);
    if (onModalChange) onModalChange(true); // Notify parent: Modal Open
    
    const repo = activeRepos.length > 0 ? activeRepos[0] : undefined;
    fetchContent(moduleId, repo);
  }, [fetchContent, activeRepos, onModalChange]);

  const handleModalClose = useCallback(() => {
    setIsModalOpen(false);
    if (onModalChange) onModalChange(false); // Notify parent: Modal Closed
    clearContent();
    setTimeout(() => setSelectedModule(null), 300);
  }, [clearContent, onModalChange]);

  const memoizedModules = useMemo(() => modules, []);

  return (
    <>
      <div className="mb-10 relative">
        <h2 className={`${inter.className} text-2xl font-semibold tracking-tight mb-3 text-[#0E1B2E] relative`}>
          Reading & Overview
        </h2>
        <p className={`${jetbrainsMono.className} text-[15px] text-[#0E1B2E]/60 leading-relaxed`}>
          Start your journey with these essential topics. Get familiar with the basics before diving deeper.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-6 mb-6">
        {memoizedModules.map((module, index) => (
          <ModuleCard
            key={module.id}
            module={module}
            index={index}
            isVisible={visibleModules.has(`module-${module.id}`)}
            onCardClick={handleCardClick}
            darkMode={darkMode}
            mousePosition={mousePosition}
            ref={(el) => {
              if (el) {
                moduleRefs.current[`module-${module.id}`] = el;
              }
            }}
          />
        ))}
      </div>

      {error && (
        <div className="fixed bottom-6 right-6 z-50">
          <div className="px-5 py-4 rounded-xl shadow-xl bg-white/90 backdrop-blur-xl text-red-600 border border-red-200/60 flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
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
          employeeId={employeeId}
          onProgressUpdate={onUpdateProgress}
        />
      )}
    </>
  );
}