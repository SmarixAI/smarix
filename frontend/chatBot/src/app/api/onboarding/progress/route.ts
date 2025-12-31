import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { employeeId, section, itemId, updates } = body;

    if (!employeeId || !section || !itemId || !updates) {
      return NextResponse.json(
        { error: 'Missing required fields: employeeId, section, itemId, updates' },
        { status: 400 }
      );
    }

    // Path to the JSON file - try multiple possible paths
    const possiblePaths = [
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Onboarding', 'employee_onboarding_tasks.json'),
      path.join(process.cwd(), '..', 'backend', 'data', 'Onboarding', 'employee_onboarding_tasks.json'),
      path.join(process.cwd(), 'backend', 'data', 'Onboarding', 'employee_onboarding_tasks.json'),
      path.join(process.cwd(), 'backend/data/Onboarding/employee_onboarding_tasks.json'),
    ];

    let filePath: string | null = null;
    let fileContent: string | null = null;

    // Try to find the file
    for (const p of possiblePaths) {
      try {
        await fs.access(p);
        filePath = p;
        fileContent = await fs.readFile(p, 'utf-8');
        break;
      } catch {
        continue;
      }
    }

    if (!filePath || !fileContent) {
      return NextResponse.json(
        { error: 'Employee onboarding tasks file not found' },
        { status: 404 }
      );
    }

    const jsonData = JSON.parse(fileContent);

    // Find the employee
    const employeeIndex = jsonData.employees?.findIndex((emp: any) =>
      emp.employeeId === employeeId ||
      emp.employee_id === employeeId ||
      String(emp.employeeId) === String(employeeId) ||
      String(emp.employee_id) === String(employeeId) ||
      emp.username === employeeId ||
      emp.name === employeeId
    );

    if (employeeIndex === -1 || !jsonData.employees[employeeIndex]) {
      return NextResponse.json(
        { error: 'Employee not found' },
        { status: 404 }
      );
    }

    const employee = jsonData.employees[employeeIndex];

    // Ensure onboarding structure exists
    if (!employee.onboarding) {
      employee.onboarding = {};
    }

    // Update based on section
    if (section === 'reading') {
      if (!employee.onboarding.reading) {
        employee.onboarding.reading = { modules: [] };
      }
      const moduleIndex = employee.onboarding.reading.modules.findIndex(
        (m: any) => m.id === itemId
      );
      if (moduleIndex !== -1) {
        employee.onboarding.reading.modules[moduleIndex] = {
          ...employee.onboarding.reading.modules[moduleIndex],
          ...updates,
          // Set completedAt if status is completed
          ...(updates.status === 'completed' && !updates.completedAt
            ? { completedAt: new Date().toISOString() }
            : {}),
          // Set startedAt if status is in-progress and not already set
          ...(updates.status === 'in-progress' && !employee.onboarding.reading.modules[moduleIndex].startedAt
            ? { startedAt: new Date().toISOString() }
            : {}),
        };
      }
    } else if (section === 'qa') {
      if (!employee.onboarding.qa) {
        employee.onboarding.qa = { modules: [] };
      }
      const moduleIndex = employee.onboarding.qa.modules.findIndex(
        (m: any) => m.id === itemId
      );
      if (moduleIndex !== -1) {
        // Update existing module
        employee.onboarding.qa.modules[moduleIndex] = {
          ...employee.onboarding.qa.modules[moduleIndex],
          ...updates,
          ...(updates.status === 'completed' && !updates.completedAt
            ? { completedAt: new Date().toISOString() }
            : {}),
          ...(updates.status === 'in-progress' && !employee.onboarding.qa.modules[moduleIndex].startedAt
            ? { startedAt: new Date().toISOString() }
            : {}),
        };
      } else {
        // Create new module if it doesn't exist
        const newModule = {
          id: itemId,
          title: updates.title || itemId,
          status: updates.status || 'pending',
          score: updates.score !== undefined ? updates.score : 0,
          totalQuestions: updates.totalQuestions || 0,
          progress: updates.progress || 0,
          ...(updates.status === 'completed' ? { completedAt: new Date().toISOString() } : {}),
          ...(updates.status === 'in-progress' ? { startedAt: new Date().toISOString() } : {}),
        };
        employee.onboarding.qa.modules.push(newModule);
      }
    } else if (section === 'practice') {
      if (!employee.onboarding.practice) {
        employee.onboarding.practice = { tasks: [] };
      }
      const taskIndex = employee.onboarding.practice.tasks.findIndex(
        (t: any) => t.id === itemId || t.question_number === itemId
      );
      if (taskIndex !== -1) {
        employee.onboarding.practice.tasks[taskIndex] = {
          ...employee.onboarding.practice.tasks[taskIndex],
          ...updates,
          ...(updates.status === 'completed' && !updates.completedAt
            ? { completedAt: new Date().toISOString() }
            : {}),
          ...(updates.status === 'in-progress' && !employee.onboarding.practice.tasks[taskIndex].startedAt
            ? { startedAt: new Date().toISOString() }
            : {}),
        };
      }
    } else if (section === 'bugfix') {
      if (!employee.onboarding.bugfix) {
        employee.onboarding.bugfix = { tutorials: [], challenges: [], coding_questions: [] };
      }
      const { type } = updates; // 'tutorial', 'challenge', or 'coding_question'
      delete updates.type; // Remove type from updates

      if (type === 'tutorial') {
        const tutorialIndex = employee.onboarding.bugfix.tutorials.findIndex(
          (t: any) => t.id === itemId
        );
        if (tutorialIndex !== -1) {
          employee.onboarding.bugfix.tutorials[tutorialIndex] = {
            ...employee.onboarding.bugfix.tutorials[tutorialIndex],
            ...updates,
            ...(updates.status === 'completed' && !updates.completedAt
              ? { completedAt: new Date().toISOString() }
              : {}),
            ...(updates.status === 'in-progress' && !employee.onboarding.bugfix.tutorials[tutorialIndex].startedAt
              ? { startedAt: new Date().toISOString() }
              : {}),
          };
        }
      } else if (type === 'challenge') {
        const challengeIndex = employee.onboarding.bugfix.challenges.findIndex(
          (c: any) => c.id === itemId
        );
        if (challengeIndex !== -1) {
          employee.onboarding.bugfix.challenges[challengeIndex] = {
            ...employee.onboarding.bugfix.challenges[challengeIndex],
            ...updates,
            ...(updates.status === 'completed' && !updates.completedAt
              ? { completedAt: new Date().toISOString() }
              : {}),
            ...(updates.status === 'in-progress' && !employee.onboarding.bugfix.challenges[challengeIndex].startedAt
              ? { startedAt: new Date().toISOString() }
              : {}),
          };
        }
      } else if (type === 'coding_question') {
        const questionIndex = employee.onboarding.bugfix.coding_questions.findIndex(
          (q: any) => q.id === itemId
        );
        if (questionIndex !== -1) {
          employee.onboarding.bugfix.coding_questions[questionIndex] = {
            ...employee.onboarding.bugfix.coding_questions[questionIndex],
            ...updates,
            ...(updates.status === 'completed' && !updates.completedAt
              ? { completedAt: new Date().toISOString() }
              : {}),
            ...(updates.status === 'in-progress' && !employee.onboarding.bugfix.coding_questions[questionIndex].startedAt
              ? { startedAt: new Date().toISOString() }
              : {}),
          };
        }
      }
    }

    // Write the updated data back to the file (use the found filePath)
    if (filePath) {
      await fs.writeFile(filePath, JSON.stringify(jsonData, null, 2), 'utf-8');
    } else {
      return NextResponse.json(
        { error: 'Could not determine file path for writing' },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      message: 'Progress updated successfully',
      employee: employee
    });
  } catch (error: any) {
    console.error('Error updating progress:', error);
    return NextResponse.json(
      { error: 'Failed to update progress', details: error.message },
      { status: 500 }
    );
  }
}

