'use client';

import { forwardRef, useCallback, memo } from 'react';
import { Lock } from 'lucide-react';
import type { Module } from '../../../../../types/onboarding';
import { Inter } from 'next/font/google';

interface ModuleCardProps {
  module: Module;
  index: number;
  darkMode: boolean;
  mousePosition: { x: number; y: number };
  isVisible: boolean;
  onCardClick: (moduleId: string) => void;
}

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700'] });

const ModuleCard = forwardRef<HTMLDivElement, ModuleCardProps>(
  ({ module, index, isVisible, onCardClick }, ref) => {
    
    const handleClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
      if (!module.locked) {
        onCardClick(module.id);
      }
    }, [module.locked, module.id, onCardClick]);

    const handleButtonClick = useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
      e.stopPropagation();
      if (!module.locked) {
        onCardClick(module.id);
      }
    }, [module.locked, module.id, onCardClick]);

    return (
      <div
        id={`module-${module.id}`}
        ref={ref}
        onClick={handleClick}
        className={`
          rounded-2xl p-6 transition-all duration-300 cursor-pointer relative overflow-hidden group border
          ${isVisible ? 'opacity-100' : 'opacity-100'}
          ${module.locked
            ? 'bg-gray-50 border-gray-200 opacity-60 cursor-not-allowed'
            : 'bg-white border-[#0E1B2E]/10 hover:border-[#0E1B2E]/30 hover:shadow-[0_8px_30px_rgba(14,27,46,0.06)] hover:-translate-y-1'
          }
        `}
      >
        {/* Subtle Background Gradient for Depth */}
        {!module.locked && (
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-[#0E1B2E]/[0.02] pointer-events-none rounded-2xl" />
        )}

        {/* Dynamic Glow Effect on Hover  */}
        {!module.locked && (
          <div 
            className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
            style={{
              background: `radial-gradient(circle at 100% 0%, ${module.color || '#0E1B2E'}10, transparent 40%)`
            }}
          />
        )}

        <div className="relative z-10 flex flex-col h-full">
          {/* Icon & Header */}
          <div className="flex items-start justify-between mb-5">
            <div
              className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-300 shadow-sm relative overflow-hidden border ${
                module.locked
                  ? 'bg-gray-100 border-gray-200 text-gray-400'
                  : 'text-white border-transparent group-hover:scale-105'
              }`}
              style={!module.locked && module.color ? { 
                backgroundColor: module.color,
                boxShadow: `0 4px 20px ${module.color}30`
              } : undefined}
            >
              {/* Glass sheen on icon */}
              {!module.locked && (
                <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent pointer-events-none" />
              )}
              
              <div className="relative z-10">
                {module.icon}
              </div>
            </div>

            {module.locked && <Lock className="w-5 h-5 text-gray-300" />}
          </div>

          <h3
            className={`${inter.className} text-[18px] font-bold mb-3 leading-tight ${
              module.locked ? 'text-gray-400' : 'text-[#0E1B2E]'
            }`}
          >
            {module.title}
          </h3>

          <p
            className={`${inter.className} text-[14px] mb-6 leading-relaxed line-clamp-2 flex-grow ${
              module.locked ? 'text-gray-400' : 'text-[#0E1B2E]/60'
            }`}
          >
            {module.description}
          </p>

          {/* Footer Area */}
          <div className={`flex items-center justify-between pt-5 border-t ${module.locked ? 'border-gray-200' : 'border-[#0E1B2E]/5'}`}>
            <span
              className={`${inter.className} text-xs font-semibold inline-flex items-center gap-2 px-3 py-1.5 rounded-lg ${
                module.locked 
                  ? 'bg-gray-100 text-gray-400' 
                  : 'bg-[#0E1B2E]/5 text-[#0E1B2E]/70'
              }`}
            >
              <div className={`w-1.5 h-1.5 rounded-full ${module.locked ? 'bg-gray-400' : 'bg-[#0E1B2E]'} opacity-50`} />
              {module.duration}
            </span>

            {!module.locked && (
              <button
                onClick={handleButtonClick}
                className={`${inter.className} px-5 py-2.5 rounded-xl text-[13px] font-semibold transition-all duration-300 bg-[#0E1B2E] text-white hover:shadow-lg hover:shadow-[#0E1B2E]/20 relative overflow-hidden group/btn`}
                onMouseEnter={(e) => {
                  if (module.color) {
                    e.currentTarget.style.backgroundColor = module.color;
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#0E1B2E';
                }}
              >
                <span className={`${inter.className} relative z-10 flex items-center gap-2`}>
                  Start Learning
                  <svg className="w-3.5 h-3.5 transition-transform duration-300 group-hover/btn:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
                  </svg>
                </span>
              </button>
            )}
          </div>
        </div>

        {/* Bottom colored line on hover */}
        {!module.locked && (
          <div 
            className="absolute bottom-0 left-0 right-0 h-[3px] scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left"
            style={{ backgroundColor: module.color || '#0E1B2E' }}
          />
        )}
      </div>
    );
  }
);

ModuleCard.displayName = 'ModuleCard';

export default memo(ModuleCard);