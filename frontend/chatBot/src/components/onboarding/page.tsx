"use client";

import { useState, useEffect } from "react";
import ThreeJsBackground from "@/components/onboarding/ThreeJsBackground";
import Header from "@/components/onboarding/Header";
import Sidebar from "@/components/onboarding/Sidebar";
import ReadingOverview from "@/components/onboarding/tabs/ReadingOverview";
import QASession from "@/components/onboarding/tabs/QASession";
import PracticeTasks from "@/components/onboarding/tabs/PracticeTasks";
import BugFixing from "@/components/onboarding/tabs/BugFixing";
import Chatbot from "@/components/onboarding/Chatbot";

export default function OnboardingPage() {
  const [darkMode, setDarkMode] = useState(true);
  const [activeTab, setActiveTab] = useState("reading");
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [scrollProgress, setScrollProgress] = useState(0);
  const [qnaSections, setQnaSections] = useState<any[]>([]);
  const [selectedQnaSection, setSelectedQnaSection] = useState<string | null>(
    null
  );
  const [practiceTasks, setPracticeTasks] = useState<any[]>([]);
  const [selectedPracticeTask, setSelectedPracticeTask] = useState<number | null>(null);
  const [employeeId, setEmployeeId] = useState<string | null>(null);
  const [activeRepos, setActiveRepos] = useState<string[]>([]);
  const [onboardingData, setOnboardingData] = useState<any>(null);
  const [completedModules, setCompletedModules] = useState(0);
  const [totalModules, setTotalModules] = useState(0);

  // Get employeeId from localStorage and fetch onboarding data
  useEffect(() => {
    const fetchEmployeeData = async () => {
      try {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
          const user = JSON.parse(storedUser);
          let id = user.employeeId;
          
          if (!id) {
            // Try to get from users.json
            const usersRes = await fetch('/api/users');
            if (usersRes.ok) {
              const usersData = await usersRes.json();
              const currentUser = usersData.users?.find((u: any) => 
                u.username === user.username || u.name === user.username
              );
              if (currentUser?.employeeId) {
                id = currentUser.employeeId;
                setActiveRepos(currentUser.active_repos || []);
              }
            }
          } else {
            // If we have id from localStorage, still fetch active_repos
            const usersRes = await fetch('/api/users');
            if (usersRes.ok) {
              const usersData = await usersRes.json();
              const currentUser = usersData.users?.find((u: any) => 
                u.employeeId === id || u.username === user.username || u.name === user.username
              );
              if (currentUser?.active_repos) {
                setActiveRepos(currentUser.active_repos);
              }
            }
          }
          
          if (id) {
            setEmployeeId(id);
            // Fetch onboarding data for this employee
            const onboardingRes = await fetch(`/api/onboarding/tasks?employeeId=${id}`);
            if (onboardingRes.ok) {
              const data = await onboardingRes.json();
              setOnboardingData(data);
              
              // Calculate progress - if no data exists, show 0%
              const reading = data.onboarding?.reading?.modules || [];
              const qa = data.onboarding?.qa?.modules || [];
              const practice = data.onboarding?.practice?.tasks || [];
              const bugfixTutorials = data.onboarding?.bugfix?.tutorials || [];
              const bugfixChallenges = data.onboarding?.bugfix?.challenges || [];
              const bugfixQuestions = data.onboarding?.bugfix?.coding_questions || [];
              
              const allItems = [...reading, ...qa, ...practice, ...bugfixTutorials, ...bugfixChallenges, ...bugfixQuestions];
              const total = allItems.length;
              const completed = allItems.filter((item: any) => item.status === 'completed').length;
              
              // If no items found, set to 0 to show 0% progress
              setTotalModules(total);
              setCompletedModules(completed);
              
              // Set practice tasks from data
              if (practice.length > 0) {
                setPracticeTasks(practice);
                if (selectedPracticeTask === null && practice.length > 0) {
                  setSelectedPracticeTask(practice[0].question_number);
                }
              } else {
                // If no practice tasks, set empty array
                setPracticeTasks([]);
              }
            } else {
              // If API call fails, set empty data
              setOnboardingData({
                employee: { employeeId: id },
                onboarding: {
                  reading: { modules: [] },
                  qa: { modules: [] },
                  practice: { tasks: [] },
                  bugfix: { tutorials: [], challenges: [], coding_questions: [] }
                }
              });
              setTotalModules(0);
              setCompletedModules(0);
              setPracticeTasks([]);
            }
          }
        }
      } catch (e) {
        console.error('Error getting employee data:', e);
      }
    };
    
    fetchEmployeeData();
  }, []);

  // Update Q&A sections when onboarding data changes
  useEffect(() => {
    if (onboardingData?.onboarding?.qa?.modules) {
      const modules = onboardingData.onboarding.qa.modules;
      setQnaSections(modules);
      // Auto-select first section if none selected
      if (!selectedQnaSection && modules.length > 0) {
        setSelectedQnaSection(modules[0].id);
      }
    }
  }, [onboardingData, selectedQnaSection]);

  // Auto-select first task when practice tab becomes active and tasks are loaded
  useEffect(() => {
    if (activeTab === 'practice' && practiceTasks.length > 0 && selectedPracticeTask === null) {
      setSelectedPracticeTask(practiceTasks[0].question_number);
    }
  }, [activeTab, practiceTasks, selectedPracticeTask]);
  const handleMouseMove = (e: React.MouseEvent) => {
    setMousePosition({
      x: (e.clientX / window.innerWidth) * 100,
      y: (e.clientY / window.innerHeight) * 100,
    });
  };

  // Function to update progress
  const updateProgress = async (section: string, itemId: string, updates: any) => {
    if (!employeeId) return;
    
    try {
      const response = await fetch('/api/onboarding/progress', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          employeeId,
          section,
          itemId,
          updates,
        }),
      });
      
      if (response.ok) {
        const data = await response.json();
        // Refresh onboarding data
        const onboardingRes = await fetch(`/api/onboarding/tasks?employeeId=${employeeId}`);
        if (onboardingRes.ok) {
          const updatedData = await onboardingRes.json();
          setOnboardingData(updatedData);
          
          // Recalculate progress
          const reading = updatedData.onboarding?.reading?.modules || [];
          const qa = updatedData.onboarding?.qa?.modules || [];
          const practice = updatedData.onboarding?.practice?.tasks || [];
          const bugfixTutorials = updatedData.onboarding?.bugfix?.tutorials || [];
          const bugfixChallenges = updatedData.onboarding?.bugfix?.challenges || [];
          const bugfixQuestions = updatedData.onboarding?.bugfix?.coding_questions || [];
          
          const allItems = [...reading, ...qa, ...practice, ...bugfixTutorials, ...bugfixChallenges, ...bugfixQuestions];
          const total = allItems.length;
          const completed = allItems.filter((item: any) => item.status === 'completed').length;
          
          setTotalModules(total);
          setCompletedModules(completed);
          
          // Update practice tasks if needed
          if (practice.length > 0) {
            setPracticeTasks(practice);
          }
        }
      }
    } catch (error) {
      console.error('Error updating progress:', error);
    }
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case "reading":
        return (
          <ReadingOverview 
            darkMode={darkMode} 
            mousePosition={mousePosition}
            employeeId={employeeId}
            activeRepos={activeRepos}
            onboardingData={onboardingData}
            onUpdateProgress={updateProgress}
          />
        );
      case "qa":
        return <QASession
          activeRepos={activeRepos}
          darkMode={darkMode} 
          selectedSection={selectedQnaSection} 
          employeeId={employeeId}
          onboardingData={onboardingData}
          onUpdateProgress={updateProgress}
        />;
      case "practice":
        return (
          <PracticeTasks
            activeRepos={activeRepos}
            darkMode={darkMode}
            tasks={practiceTasks}
            openTask={selectedPracticeTask}
            onSelectTask={(n: number | null) => setSelectedPracticeTask(n)}
            employeeId={employeeId}
            onUpdateProgress={updateProgress}
          />
        );
      case "bugfix":
        return <BugFixing
          activeRepos={activeRepos}
          darkMode={darkMode}
          employeeId={employeeId}
          onboardingData={onboardingData}
          onUpdateProgress={updateProgress}
        />;
      default:
        return (
          <ReadingOverview 
            darkMode={darkMode} 
            mousePosition={mousePosition}
            employeeId={employeeId}
            activeRepos={activeRepos}
            onboardingData={onboardingData}
            onUpdateProgress={updateProgress}
          />
        );
    }
  };

  return (
    <div
      className={`min-h-screen transition-colors duration-700 relative overflow-hidden ${
        darkMode
          ? "bg-gray-900 text-gray-100"
          : "bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 text-slate-900"
      }`}
      onMouseMove={handleMouseMove}
    >
      <style jsx global>{`
        @keyframes ripple {
          from {
            transform: scale(0);
            opacity: 0.6;
          }
          to {
            transform: scale(4);
            opacity: 0;
          }
        }

        .ripple {
          position: absolute;
          border-radius: 50%;
          background: ${darkMode
            ? "rgba(99, 102, 241, 0.5)"
            : "rgba(99, 102, 241, 0.4)"};
          pointer-events: none;
          animation: ripple 0.6s ease-out;
        }

        @keyframes slideInLeft {
          from {
            opacity: 0;
            transform: translateX(-100px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        @keyframes slideInRight {
          from {
            opacity: 0;
            transform: translateX(100px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        @keyframes slideInUp {
          from {
            opacity: 0;
            transform: translateY(100px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes scaleIn {
          from {
            opacity: 0;
            transform: scale(0.8);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        @keyframes glow {
          0%,
          100% {
            box-shadow: 0 0 20px rgba(99, 102, 241, 0.5);
          }
          50% {
            box-shadow: 0 0 40px rgba(99, 102, 241, 0.8);
          }
        }

        @keyframes shimmer {
          0% {
            background-position: -200% center;
          }
          100% {
            background-position: 200% center;
          }
        }

        .animate-slide-in-left {
          animation: slideInLeft 0.6s ease-out forwards;
        }
        .animate-slide-in-right {
          animation: slideInRight 0.6s ease-out forwards;
        }
        .animate-slide-in-up {
          animation: slideInUp 0.6s ease-out forwards;
        }
        .animate-scale-in {
          animation: scaleIn 0.6s ease-out forwards;
        }
        .animate-glow {
          animation: glow 2s ease-in-out infinite;
        }

        .glass-card {
          backdrop-filter: blur(16px) saturate(180%);
          -webkit-backdrop-filter: blur(16px) saturate(180%);
          border: 1px solid rgba(255, 255, 255, 0.125);
        }

        .glass-card-light {
          backdrop-filter: blur(20px) saturate(200%);
          -webkit-backdrop-filter: blur(20px) saturate(200%);
          background: rgba(255, 255, 255, 0.7);
          border: 1px solid rgba(255, 255, 255, 0.5);
        }

        .glass-card-dark {
          backdrop-filter: blur(16px) saturate(180%);
          -webkit-backdrop-filter: blur(16px) saturate(180%);
          background: rgba(17, 24, 39, 0.7);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .shimmer-effect {
          background: linear-gradient(
            90deg,
            transparent,
            rgba(255, 255, 255, 0.3),
            transparent
          );
          background-size: 200% 100%;
          animation: shimmer 3s infinite;
        }
      `}</style>

      <div
        className="fixed top-0 left-0 right-0 h-1 bg-gradient-to-r from-indigo-500 via-cyan-500 to-teal-500 z-50 origin-left transition-transform"
        style={{ transform: `scaleX(${scrollProgress / 100})` }}
      />

      <ThreeJsBackground darkMode={darkMode} />

      <div
        className="fixed inset-0 pointer-events-none z-0 transition-all duration-300"
        style={{
          background: darkMode
            ? `radial-gradient(circle at ${mousePosition.x}% ${
                mousePosition.y
              }%, rgba(99, 102, 241, 0.2) 0%, transparent 50%),
               radial-gradient(circle at ${100 - mousePosition.x}% ${
                100 - mousePosition.y
              }%, rgba(139, 92, 246, 0.2) 0%, transparent 50%)`
            : `radial-gradient(circle at ${mousePosition.x}% ${
                mousePosition.y
              }%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
               radial-gradient(circle at ${100 - mousePosition.x}% ${
                100 - mousePosition.y
              }%, rgba(6, 182, 212, 0.15) 0%, transparent 50%)`,
        }}
      />

      <div className="relative z-10">
        <Header
          darkMode={darkMode}
          setDarkMode={setDarkMode}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
        />

        <div className="max-w-[1800px] mx-auto px-6 py-6">
          <div className="grid grid-cols-12 gap-4">
            {activeTab !== "bugfix" && (
              <Sidebar
                darkMode={darkMode}
                completedModules={completedModules}
                totalModules={totalModules}
                activeTab={activeTab}
                qnaSections={qnaSections}
                onSelectQnASection={(key) => setSelectedQnaSection(key)}
                practiceTasks={practiceTasks}
                selectedPracticeTask={selectedPracticeTask}
                onSelectPracticeTask={(n: number | null) => setSelectedPracticeTask(n)}
              />
            )}

            <main className={activeTab === "bugfix" ? "col-span-12" : "col-span-9"}>
              {renderTabContent()}
            </main>
          </div>
        </div>
      </div>

      {/* Chatbot */}
      <Chatbot darkMode={darkMode} role="onboarding" />
    </div>
  );
}

