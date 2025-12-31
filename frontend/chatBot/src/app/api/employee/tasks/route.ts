import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const employeeId = searchParams.get('employeeId');
    const username = searchParams.get('username');

    if (!employeeId && !username) {
      return NextResponse.json(
        { error: 'Employee ID or username is required' },
        { status: 400 }
      );
    }

    // Find the file
    const possiblePaths = [
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Admin', 'employee_tasks.json'),
      path.join(process.cwd(), '..', 'backend', 'data', 'Admin', 'employee_tasks.json'),
      path.join(process.cwd(), 'backend', 'data', 'Admin', 'employee_tasks.json'),
    ];

    let filePath: string | null = null;

    for (const p of possiblePaths) {
      try {
        await fs.access(p);
        filePath = p;
        break;
      } catch {
        continue;
      }
    }

    if (!filePath) {
      // Return empty tasks if file doesn't exist
      return NextResponse.json({
        assignedByManager: [],
        ownTasks: []
      });
    }

    // Read current data
    const fileContent = await fs.readFile(filePath, 'utf-8');
    const jsonData = JSON.parse(fileContent);

    // Find employee
    const employee = jsonData.employees.find((emp: any) => 
      (employeeId && emp.employeeId === employeeId) ||
      (username && emp.username === username)
    );

    if (!employee || !employee.tasks) {
      return NextResponse.json({
        assignedByManager: [],
        ownTasks: []
      });
    }

    return NextResponse.json({
      assignedByManager: employee.tasks.assignedByManager || [],
      ownTasks: employee.tasks.ownTasks || []
    });
  } catch (error) {
    console.error('Error fetching employee tasks:', error);
    return NextResponse.json(
      { error: 'Failed to load tasks data' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { employeeId, username, taskId, priority, status, deadline, action, taskType } = body;

    // Find the file
    const possiblePaths = [
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Admin', 'employee_tasks.json'),
      path.join(process.cwd(), '..', 'backend', 'data', 'Admin', 'employee_tasks.json'),
      path.join(process.cwd(), 'backend', 'data', 'Admin', 'employee_tasks.json'),
    ];

    let filePath: string | null = null;

    for (const p of possiblePaths) {
      try {
        await fs.access(p);
        filePath = p;
        break;
      } catch {
        continue;
      }
    }

    if (!filePath) {
      // Create file if it doesn't exist
      filePath = path.join(process.cwd(), '..', '..', 'backend', 'data', 'Admin', 'employee_tasks.json');
      const initialData = { employees: [] };
      await fs.mkdir(path.dirname(filePath), { recursive: true });
      await fs.writeFile(filePath, JSON.stringify(initialData, null, 2), 'utf-8');
    }

    // Read current data
    const fileContent = await fs.readFile(filePath, 'utf-8');
    const jsonData = JSON.parse(fileContent);

    // Find or create employee
    let employeeIndex = jsonData.employees.findIndex((emp: any) => 
      (employeeId && emp.employeeId === employeeId) ||
      (username && emp.username === username)
    );

    if (employeeIndex === -1) {
      // Create new employee entry
      jsonData.employees.push({
        employeeId: employeeId || null,
        username: username || null,
        tasks: {
          assignedByManager: [],
          ownTasks: []
        }
      });
      employeeIndex = jsonData.employees.length - 1;
    }

    // Ensure tasks object exists
    if (!jsonData.employees[employeeIndex].tasks) {
      jsonData.employees[employeeIndex].tasks = {
        assignedByManager: [],
        ownTasks: []
      };
    }

    const tasks = jsonData.employees[employeeIndex].tasks;
    const taskList = taskType === 'assignedByManager' ? tasks.assignedByManager : tasks.ownTasks;

    if (action === 'update' && taskId) {
      // Update existing task
      const taskIndex = taskList.findIndex((t: any) => t.id === taskId);
      if (taskIndex !== -1) {
        if (priority) taskList[taskIndex].priority = priority;
        if (status) taskList[taskIndex].status = status;
        if (deadline !== undefined) taskList[taskIndex].deadline = deadline;
      }
    } else if (action === 'markDone' && taskId) {
      // Mark task as done
      const taskIndex = taskList.findIndex((t: any) => t.id === taskId);
      if (taskIndex !== -1) {
        taskList[taskIndex].status = 'completed';
      }
    }

    // Write back to file
    await fs.writeFile(filePath, JSON.stringify(jsonData, null, 2), 'utf-8');

    return NextResponse.json({
      success: true,
      tasks: {
        assignedByManager: tasks.assignedByManager || [],
        ownTasks: tasks.ownTasks || []
      }
    });
  } catch (error) {
    console.error('Error updating employee tasks:', error);
    return NextResponse.json(
      { error: 'Failed to update tasks data' },
      { status: 500 }
    );
  }
}

