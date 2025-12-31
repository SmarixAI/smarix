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
    const rafRef = useRef<number | null>(null);

    const createRipple = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
      const target = e.currentTarget;
      const ripple = document.createElement('span');
      const rect = target.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      const x = e.clientX - rect.left - size / 2;
      const y = e.clientY - rect.top - size / 2;

      ripple.style.width = ripple.style.height = size + 'px';
      ripple.style.left = x + 'px';
      ripple.style.top = y + 'px';
      ripple.className = 'ripple';

      target.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    }, []);

    const handleMagneticMove = useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }

      const button = e.currentTarget;
      const rect = button.getBoundingClientRect();
      const clientX = e.clientX;
      const clientY = e.clientY;

      rafRef.current = requestAnimationFrame(() => {
        if (button) {
          const x = clientX - rect.left - rect.width / 2;
          const y = clientY - rect.top - rect.height / 2;
          button.style.transform = `translate(${x * 0.3}px, ${y * 0.3}px) scale(1.05)`;
        }
      });
    }, []);

    const handleMagneticLeave = useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
      const button = e.currentTarget;
      if (button) {
        button.style.transform = 'translate(0, 0) scale(1)';
      }
    }, []);

    const handleClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
      createRipple(e);
      if (!module.locked) {
        onCardClick(module.id);
      }
    }, [createRipple, module.locked, module.id, onCardClick]);

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
        className={`rounded-2xl p-7 transition-all duration-500 cursor-pointer relative overflow-hidden group shadow-xl ${
          isVisible ? 'animate-scale-in opacity-100' : 'opacity-100'
        } ${
          module.locked
            ? darkMode
              ? 'glass-card-dark opacity-60'
              : 'glass-card-light opacity-60'
            : darkMode
            ? 'glass-card-dark hover:shadow-2xl hover:scale-105 hover:-translate-y-2'
            : 'glass-card-light hover:shadow-2xl hover:scale-105 hover:-translate-y-2'
        }`}
        style={{
          animationDelay: `${index * 0.1}s`,
          willChange: isVisible ? 'transform, opacity' : 'auto',
          transform: 'translateZ(0)',
        }}
      >
        <div
          className={`absolute top-0 right-0 w-40 h-40 rounded-full blur-3xl opacity-0 group-hover:opacity-30 transition-opacity ${
            module.locked ? 'bg-gray-500' : `bg-gradient-to-br ${module.color}`
          }`}
          style={{ willChange: 'opacity' }}
        />

        <div
          className={`w-16 h-16 rounded-xl flex items-center justify-center mb-5 transition-all duration-300 group-hover:scale-110 relative z-10 shadow-lg ${
            module.locked
              ? darkMode
                ? 'bg-gray-700'
                : 'bg-slate-300'
              : `bg-gradient-to-br ${module.color}`
          }`}
          style={{ willChange: 'transform' }}
        >
          <div className={`${module.locked ? 'text-gray-500' : 'text-white'}`}>
            {module.icon}
          </div>
          {!module.locked && (
            <div className="absolute inset-0 shimmer-effect rounded-xl" />
          )}
        </div>

        <h3
          className={`text-xl font-bold mb-3 relative z-10 ${
            module.locked
              ? darkMode
                ? 'text-gray-400'
                : 'text-slate-500'
              : darkMode
              ? 'text-gray-100 group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:from-blue-400 group-hover:via-purple-400 group-hover:to-pink-400 group-hover:bg-clip-text'
              : 'text-slate-900 group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:from-indigo-600 group-hover:via-cyan-600 group-hover:to-teal-600 group-hover:bg-clip-text'
          }`}
        >
          {module.title}
        </h3>

        <p
          className={`text-sm mb-5 relative z-10 leading-relaxed line-clamp-2 ${
            darkMode ? 'text-gray-400' : 'text-slate-600'
          }`}
        >
          {module.description}
        </p>

        <div className="flex items-center justify-between relative z-10">
          <span
            className={`text-xs font-medium ${
              darkMode ? 'text-gray-500' : 'text-slate-500'
            }`}
          >
            {module.duration}
          </span>

          {module.locked ? (
            <button
              className={`px-4 py-2.5 rounded-xl text-sm font-semibold flex items-center space-x-2 cursor-not-allowed ${
                darkMode ? 'bg-gray-700 text-gray-500' : 'bg-slate-200 text-slate-500'
              }`}
              disabled
            >
              <Lock className="w-4 h-4" />
              <span>Locked</span>
            </button>
          ) : (
            <button
              onMouseMove={handleMagneticMove}
              onMouseLeave={handleMagneticLeave}
              onClick={handleButtonClick}
              className={`px-5 py-2.5 rounded-xl text-sm font-bold transition-all duration-300 hover:shadow-xl relative overflow-hidden group/btn ${
                darkMode
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-500 hover:to-purple-500'
                  : `bg-gradient-to-r ${module.color} text-white shadow-md hover:shadow-lg`
              }`}
              style={{ willChange: 'transform' }}
            >
              <span className="relative z-10">Start Learning →</span>
              <div className="absolute inset-0 shimmer-effect" />
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
