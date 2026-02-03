"use client";

import { useState, useEffect } from "react";
import Header from "@/components/onboarding/Header";
import Sidebar from "@/components/onboarding/Sidebar";
import ReadingOverview from "@/components/onboarding/tabs/ReadingOverview";
import PracticeTasks from "@/components/onboarding/tabs/PracticeTasks";
import BugFixing from "@/components/onboarding/tabs/BugFixing";
import Chatbot from "@/components/onboarding/Chatbot";
import RightSidebar from "@/components/onboarding/RightSidebar";


export default function OnboardingPage() {
  const [activeTab, setActiveTab] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('onboardingActiveTab') || 'reading';
    }
    return 'reading';
  });
  const [practiceTasks, setPracticeTasks] = useState<any[]>([]);
  const [selectedPracticeTask, setSelectedPracticeTask] = useState<number | null>(null);
  const [employeeId, setEmployeeId] = useState<string | null>(null);
  const [activeRepos, setActiveRepos] = useState<string[]>([]);
  const [onboardingData, setOnboardingData] = useState<any>(null);
  const [completedModules, setCompletedModules] = useState(0);
  const [totalModules, setTotalModules] = useState(0);
  
  // State to control Header visibility
  const [isHeaderVisible, setIsHeaderVisible] = useState(true);

  useEffect(() => {
    localStorage.setItem('onboardingActiveTab', activeTab);
  }, [activeTab]);

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
          const bugfixTutorials = data.onboarding?.bugfix?.tutorials || [];
          const bugfixChallenges = data.onboarding?.bugfix?.challenges || [];
          const bugfixQuestions = data.onboarding?.bugfix?.coding_questions || [];
          const practice = data.onboarding?.practice?.tasks || [];

          
          const allItems = [...reading, ...practice, ...bugfixTutorials, ...bugfixChallenges, ...bugfixQuestions];
              const total = allItems.length;
              const completed = allItems.filter((item: any) => item.status === 'completed').length;
              
              // If no items found, set to 0 to show 0% progress
              setTotalModules(total);
              setCompletedModules(completed);
              
            } else {
              // If API call fails, set empty data
              setOnboardingData({
                employee: { employeeId: id },
                onboarding: {
                  reading: { modules: [] },
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


  // 🔹 Fetch practice tasks for sidebar + main panel
  useEffect(() => {
    if (activeTab !== 'practice') return;

    const fetchPracticeTasks = async () => {
      try {
        const repo = activeRepos?.[0];
        const repoParam = repo ? `?repo=${encodeURIComponent(repo)}` : '';

        const res = await fetch(`/api/onboarding/practice/practice1${repoParam}`);
        if (!res.ok) return;

        const json = await res.json();
        const tasks = json.tasks || [];

        setPracticeTasks(tasks);

        if (tasks.length > 0 && selectedPracticeTask == null) {
          setSelectedPracticeTask(tasks[0].question_number);
        }
      } catch (e) {
        console.error('Failed to load practice tasks', e);
      }
    };

    fetchPracticeTasks();
  }, [activeTab, activeRepos?.[0]]);



  // Auto-select first task when practice tab becomes active and tasks are loaded
  useEffect(() => {
    if (activeTab === 'practice' && practiceTasks.length > 0 && selectedPracticeTask === null) {
      setSelectedPracticeTask(practiceTasks[0].question_number);
    }
  }, [activeTab, practiceTasks, selectedPracticeTask]);

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
          const practice = updatedData.onboarding?.practice?.tasks || [];
          const bugfixTutorials = updatedData.onboarding?.bugfix?.tutorials || [];
          const bugfixChallenges = updatedData.onboarding?.bugfix?.challenges || [];
          const bugfixQuestions = updatedData.onboarding?.bugfix?.coding_questions || [];
          
          const allItems = [...reading, ...practice, ...bugfixTutorials, ...bugfixChallenges, ...bugfixQuestions];
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
            employeeId={employeeId}
            activeRepos={activeRepos}
            onboardingData={onboardingData}
            onUpdateProgress={updateProgress}
            onModalChange={(isOpen) => setIsHeaderVisible(!isOpen)} 
          />
        );
      case "practice":
        return (
          <PracticeTasks
            activeRepos={activeRepos}
            tasks={practiceTasks}
            openTask={selectedPracticeTask}
            onSelectTask={(n: number | null) => setSelectedPracticeTask(n)}
            employeeId={employeeId}
            onUpdateProgress={updateProgress}
          />
        );
      case "bugfix":
        const bugfixTutorials = onboardingData?.onboarding?.bugfix?.tutorials || [];
        const bugfixChallenges = onboardingData?.onboarding?.bugfix?.challenges || [];
        return <BugFixing
          activeRepos={activeRepos}
          employeeId={employeeId}
          onboardingData={onboardingData}
          onUpdateProgress={updateProgress}
        />;
      default:
        return (
          <ReadingOverview 
            employeeId={employeeId}
            activeRepos={activeRepos}
            onboardingData={onboardingData}
            onUpdateProgress={updateProgress}
            onModalChange={(isOpen) => setIsHeaderVisible(!isOpen)}
          />
        );
    }
  };

    return (
      <div className="min-h-screen bg-[#FAFAFA] text-[#0E1B2E]">
        <div className="relative z-10 min-h-screen">
          {/* Conditionally render Header */}
          {isHeaderVisible && (
            <Header
              activeTab={activeTab}
              setActiveTab={setActiveTab}
            />
          )}

          <div className="max-w-[1800px] mx-auto px-3 py-4 relative">
            {activeTab !== "practice" && (
              <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
            )}

            <div
              className="relative z-10 grid grid-cols-12 gap-2 h-[calc(100vh-180px)]"
            >

              {/* LEFT SIDEBAR */}
              {(activeTab === "practice" || activeTab === "bugfix") && (
                <div className="col-span-3 h-full overflow-y-auto overflow-x-hidden">
                  <Sidebar
                    completedModules={completedModules}
                    totalModules={totalModules}
                    activeTab={activeTab}
                    practiceTasks={practiceTasks}
                    selectedPracticeTask={selectedPracticeTask}
                    onSelectPracticeTask={(n: number | null) =>
                      setSelectedPracticeTask(n)
                    }
                    tutorialsCount={onboardingData?.onboarding?.bugfix?.tutorials?.length || 0}
                    challengesCount={onboardingData?.onboarding?.bugfix?.challenges?.length || 0}
                  />
                </div>
              )}

              {/* MIDDLE CONTENT */}
              <main
                className={`${
                  activeTab === "bugfix"
                    ? "col-span-6"
                    : activeTab === "practice"
                    ? "col-span-9"
                    : "col-span-12"
                } h-full overflow-y-auto overflow-x-hidden bg-[#FAFAFA] min-w-0`}
              >
                {renderTabContent()}
              </main>


              {/* RIGHT SIDEBAR */}
              {activeTab === "bugfix" && (
                <aside className="col-span-3 h-full overflow-y-auto overflow-x-hidden border-l border-slate-200 bg-[#FAFAFA]">
                  <RightSidebar />
                </aside>
              )}

            </div>

          </div>
        </div>

        {/* Chatbot */}
        <Chatbot role="onboarding" />
      </div>
    );

}