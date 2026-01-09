'use client';

import { forwardRef, useCallback, useRef, memo } from 'react';
import { Lock } from 'lucide-react';
import type { Module } from '../../../../../types/onboarding';

interface ModuleCardProps {
  module: Module;
  index: number;
  darkMode: boolean;
  mousePosition: { x: number; y: number };
  isVisible: boolean;
  onCardClick: (moduleId: string) => void;
}

const ModuleCard = forwardRef<HTMLDivElement, ModuleCardProps>(
  ({ module, index, darkMode, mousePosition, isVisible, onCardClick }, ref) => {
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
        className={`rounded-lg p-5 transition-all duration-200 cursor-pointer relative overflow-hidden group border border-gray-200 bg-white shadow-sm ${
          isVisible ? 'opacity-100' : 'opacity-100'
        } ${
          module.locked
            ? 'opacity-60'
            : 'hover:shadow-md'
        }`}
        style={!module.locked && module.color ? {
          '--border-hover': module.color + '40',
        } as React.CSSProperties & { '--border-hover': string } : undefined}
        onMouseEnter={(e) => {
          if (!module.locked && module.color) {
            e.currentTarget.style.borderColor = module.color + '40';
          }
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = '';
          e.currentTarget.style.backgroundColor = '';
        }}
      >
        {/* Subtle accent color background on hover */}
        {!module.locked && module.color && (
          <div 
            className="absolute inset-0 rounded-lg opacity-0 group-hover:opacity-5 transition-opacity duration-200 pointer-events-none"
            style={{ backgroundColor: module.color }}
          />
        )}
        
        <div
          className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 transition-all duration-200 relative z-10 ${
            module.locked
              ? 'bg-gray-200'
              : ''
          }`}
          style={!module.locked && module.color ? { backgroundColor: module.color } : undefined}
        >
          <div className={`${module.locked ? 'text-gray-400' : 'text-white'}`}>
            {module.icon}
          </div>
        </div>

        <h3
          className={`text-base font-semibold mb-2 relative z-10 ${
            module.locked
              ? 'text-[#0E1B2E]/40'
              : 'text-[#0E1B2E]'
          }`}
        >
          {module.title}
        </h3>

        <p
          className={`text-sm mb-4 relative z-10 leading-relaxed line-clamp-2 ${
            module.locked ? 'text-[#0E1B2E]/40' : 'text-[#0E1B2E]/60'
          }`}
        >
          {module.description}
        </p>

        <div className="flex items-center justify-between relative z-10">
          <span
            className={`text-xs font-medium ${
              module.locked ? 'text-[#0E1B2E]/40' : 'text-[#0E1B2E]/60'
            }`}
          >
            {module.duration}
          </span>

          {module.locked ? (
            <button
              className="px-4 py-2 rounded-lg text-sm font-medium flex items-center space-x-2 cursor-not-allowed bg-gray-100 text-gray-400"
              disabled
            >
              <Lock className="w-4 h-4" />
              <span>Locked</span>
            </button>
          ) : (
            <button
              onClick={handleButtonClick}
              className="px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 bg-[#0E1B2E] text-white hover:opacity-90"
              style={module.color ? { 
                '--hover-color': module.color,
              } as React.CSSProperties : undefined}
              onMouseEnter={(e) => {
                if (module.color) {
                  e.currentTarget.style.backgroundColor = module.color;
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#0E1B2E';
              }}
            >
              Start Learning →
            </button>
          )}
        </div>
      </div>
    );
  }
);

ModuleCard.displayName = 'ModuleCard';

export default memo(ModuleCard, (prevProps, nextProps) => {
  return (
    prevProps.module.id === nextProps.module.id &&
    prevProps.isVisible === nextProps.isVisible &&
    prevProps.darkMode === nextProps.darkMode
  );
});
