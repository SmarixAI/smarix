import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';

export async function GET() {
  try {
    const possiblePaths = [
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Offboarding', '4employee_tasks_with_metadata_finalCallData.json'),
      path.join(process.cwd(), '..', 'backend', 'data', 'Offboarding', '4employee_tasks_with_metadata_finalCallData.json'),
      path.join(process.cwd(), 'backend', 'data', 'Offboarding', '4employee_tasks_with_metadata_finalCallData.json'),
    ];

    let fileContent: string | null = null;

    for (const filePath of possiblePaths) {
      try {
        await fs.access(filePath);
        fileContent = await fs.readFile(filePath, 'utf-8');
        break;
      } catch {
        continue;
      }
    }

    if (!fileContent) {
      return NextResponse.json(
        { error: 'Tasks file not found' },
        { status: 404 }
      );
    }

    const jsonData = JSON.parse(fileContent);

    return NextResponse.json(jsonData, {
      headers: {
        'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400',
      },
    });
  } catch (error) {
    return NextResponse.json({
      error: 'Failed to load tasks data',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { employeeId, taskId, priority, status, source, title, action } = body;

    // For adding new manager task
    if (action === 'add' && title && priority) {
      if (!employeeId) {
        return NextResponse.json(
          { error: 'Employee ID is required' },
          { status: 400 }
        );
      }

      // Find the file
      const possiblePaths = [
        path.join(process.cwd(), '..', '..', 'backend', 'data', 'offboarding', '4employee_tasks_with_metadata_finalCallData.json'),
        path.join(process.cwd(), '..', 'backend', 'data', 'offboarding', '4employee_tasks_with_metadata_finalCallData.json'),
        path.join(process.cwd(), 'backend', 'data', 'offboarding', '4employee_tasks_with_metadata_finalCallData.json'),
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
        return NextResponse.json(
          { error: 'Tasks file not found' },
          { status: 404 }
        );
      }

      // Read current data
      const fileContent = await fs.readFile(filePath, 'utf-8');
      const jsonData = JSON.parse(fileContent);

      // Find employee
      const employeeIndex = jsonData.employees.findIndex(
        (emp: any) => emp.employeeId === employeeId
      );

      if (employeeIndex === -1) {
        return NextResponse.json(
          { error: 'Employee not found' },
          { status: 404 }
        );
      }

      // Ensure tasks object exists
      if (!jsonData.employees[employeeIndex].tasks) {
        jsonData.employees[employeeIndex].tasks = {};
      }

      // Ensure manager array exists
      if (!jsonData.employees[employeeIndex].tasks.manager) {
        jsonData.employees[employeeIndex].tasks.manager = [];
      }

      // Generate task ID
      const managerTasks = jsonData.employees[employeeIndex].tasks.manager || [];
      const taskId = `${employeeId}-m${managerTasks.length + 1}`;

      // Create new manager task with minimal fields
      const newTask = {
        id: taskId,
        title: title,
        priority: priority,
        tags: ['Manual'],
        source: 'Manager'
      };

      // Add to manager tasks
      jsonData.employees[employeeIndex].tasks.manager.push(newTask);

      // Write back to file
      await fs.writeFile(
        filePath,
        JSON.stringify(jsonData, null, 2),
        'utf-8'
      );

      return NextResponse.json(
        { success: true, task: newTask },
        {
          headers: {
            'Cache-Control': 'no-cache',
          },
        }
      );
    }

    // For updating existing task status (not needed)
    if (status && !priority) {
      if (!employeeId || !taskId) {
        return NextResponse.json(
          { error: 'Employee ID and Task ID are required' },
          { status: 400 }
        );
      }

      // Find the file
      const possiblePaths = [
        path.join(process.cwd(), '..', '..', 'backend', 'data', 'offboarding', '4employee_tasks_with_metadata_finalCallData.json'),
        path.join(process.cwd(), '..', 'backend', 'data', 'offboarding', '4employee_tasks_with_metadata_finalCallData.json'),
        path.join(process.cwd(), 'backend', 'data', 'offboarding', '4employee_tasks_with_metadata_finalCallData.json'),
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
        return NextResponse.json(
          { error: 'Tasks file not found' },
          { status: 404 }
        );
      }

      // Read current data
      const fileContent = await fs.readFile(filePath, 'utf-8');
      const jsonData = JSON.parse(fileContent);

      // Find employee
      const employeeIndex = jsonData.employees.findIndex(
        (emp: any) => emp.employeeId === employeeId
      );

      if (employeeIndex === -1) {
        return NextResponse.json(
          { error: 'Employee not found' },
          { status: 404 }
        );
      }

      // Find and update task
      const tasks = jsonData.employees[employeeIndex].tasks || {};
      const aiTasks = tasks.ai || [];
      const managerTasks = tasks.manager || [];
      
      let taskIndex = aiTasks.findIndex((t: any) => t.id === taskId);
      let taskList = aiTasks;
      let isManagerTask = false;
      
      if (taskIndex === -1) {
        taskIndex = managerTasks.findIndex((t: any) => t.id === taskId);
        if (taskIndex !== -1) {
          taskList = managerTasks;
          isManagerTask = true;
        }
      }

      if (taskIndex === -1) {
        return NextResponse.json(
          { error: 'Task not found' },
          { status: 404 }
        );
      }

      // Update status
      taskList[taskIndex].status = status;
      
      if (isManagerTask) {
        tasks.manager[taskIndex].status = status;
      } else {
        tasks.ai[taskIndex].status = status;
      }

      // Write back to file
      await fs.writeFile(
        filePath,
        JSON.stringify(jsonData, null, 2),
        'utf-8'
      );

      return NextResponse.json(
        { success: true, task: isManagerTask ? tasks.manager[taskIndex] : tasks.ai[taskIndex] },
        {
          headers: {
            'Cache-Control': 'no-cache',
          },
        }
      );
    }

    // For updating existing task priority
    if (!employeeId || !taskId || !priority) {
      return NextResponse.json(
        { error: 'Employee ID, Task ID, and Priority are required' },
        { status: 400 }
      );
    }

    // Find the file
    const possiblePaths = [
      path.join(process.cwd(), '..', '..', 'backend', 'data', 'Offboarding', '4employee_tasks_with_metadata_finalCallData.json'),
      path.join(process.cwd(), '..', 'backend', 'data', 'Offboarding', '4employee_tasks_with_metadata_finalCallData.json'),
      path.join(process.cwd(), 'backend', 'data', 'Offboarding', '4employee_tasks_with_metadata_finalCallData.json'),
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
      return NextResponse.json(
        { error: 'Tasks file not found' },
        { status: 404 }
      );
    }

    // Read current data
    const fileContent = await fs.readFile(filePath, 'utf-8');
    const jsonData = JSON.parse(fileContent);

    // Find employee
    const employeeIndex = jsonData.employees.findIndex(
      (emp: any) => emp.employeeId === employeeId
    );

    if (employeeIndex === -1) {
      return NextResponse.json(
        { error: 'Employee not found' },
        { status: 404 }
      );
    }

    // Find and update task
    const tasks = jsonData.employees[employeeIndex].tasks || {};
    
    // Search in both ai and manager arrays
    const aiTasks = tasks.ai || [];
    const managerTasks = tasks.manager || [];
    
    // Try to find in ai tasks first
    let taskIndex = aiTasks.findIndex((t: any) => t.id === taskId);
    let taskList = aiTasks;
    let isManagerTask = false;
    
    // If not found in ai, try manager tasks
    if (taskIndex === -1) {
      taskIndex = managerTasks.findIndex((t: any) => t.id === taskId);
      if (taskIndex !== -1) {
        taskList = managerTasks;
        isManagerTask = true;
      }
    }

    if (taskIndex === -1) {
      return NextResponse.json(
        { error: 'Task not found', taskId, employeeId },
        { status: 404 }
      );
    }

    // Update priority in the correct array
    taskList[taskIndex].priority = priority;
    
    // Ensure the tasks object has the correct structure
    if (isManagerTask) {
      if (!tasks.manager) {
        tasks.manager = [];
      }
      tasks.manager[taskIndex].priority = priority;
    } else {
      tasks.ai[taskIndex].priority = priority;
    }

    // Write back to file
    await fs.writeFile(
      filePath,
      JSON.stringify(jsonData, null, 2),
      'utf-8'
    );

    return NextResponse.json(
      { success: true, task: isManagerTask ? tasks.manager[taskIndex] : tasks.ai[taskIndex] },
      {
        headers: {
          'Cache-Control': 'no-cache',
        },
      }
    );
  } catch (error) {
    return NextResponse.json({
      error: 'Failed to update task priority',
      details: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}

