import { NextRequest, NextResponse } from 'next/server';
import { readJsonFromS3WithFallback, writeJsonToS3 } from '../../../../components/offboarding/s3Utils';

export async function GET() {
  try {
    const possibleFiles = [
      '4employee_tasks_with_metadata_finalCallData.json',
    ];

    const { data: jsonData } = await readJsonFromS3WithFallback(possibleFiles);

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

    const fileName = '4employee_tasks_with_metadata_finalCallData.json';

    // For adding new manager task
    if (action === 'add' && title && priority) {
      if (!employeeId) {
        return NextResponse.json(
          { error: 'Employee ID is required' },
          { status: 400 }
        );
      }

      // Read current data
      const jsonData = await readJsonFromS3WithFallback([fileName]);

      // Find employee
      const employeeIndex = jsonData.data.employees.findIndex(
        (emp: any) => emp.employeeId === employeeId
      );

      if (employeeIndex === -1) {
        return NextResponse.json(
          { error: 'Employee not found' },
          { status: 404 }
        );
      }

      // Ensure tasks object exists
      if (!jsonData.data.employees[employeeIndex].tasks) {
        jsonData.data.employees[employeeIndex].tasks = {};
      }

      // Ensure manager array exists
      if (!jsonData.data.employees[employeeIndex].tasks.manager) {
        jsonData.data.employees[employeeIndex].tasks.manager = [];
      }

      // Generate task ID
      const managerTasks = jsonData.data.employees[employeeIndex].tasks.manager || [];
      const newTaskId = `${employeeId}-m${managerTasks.length + 1}`;

      // Create new manager task
      const newTask = {
        id: newTaskId,
        title: title,
        priority: priority,
        tags: ['Manual'],
        source: 'Manager'
      };

      // Add to manager tasks
      jsonData.data.employees[employeeIndex].tasks.manager.push(newTask);

      // Write back to S3
      await writeJsonToS3(fileName, jsonData.data);

      return NextResponse.json(
        { success: true, task: newTask },
        {
          headers: {
            'Cache-Control': 'no-cache',
          },
        }
      );
    }

    // For updating existing task status
    if (status && !priority) {
      if (!employeeId || !taskId) {
        return NextResponse.json(
          { error: 'Employee ID and Task ID are required' },
          { status: 400 }
        );
      }

      const jsonData = await readJsonFromS3WithFallback([fileName]);

      // Find employee
      const employeeIndex = jsonData.data.employees.findIndex(
        (emp: any) => emp.employeeId === employeeId
      );

      if (employeeIndex === -1) {
        return NextResponse.json(
          { error: 'Employee not found' },
          { status: 404 }
        );
      }

      // Find and update task
      const tasks = jsonData.data.employees[employeeIndex].tasks || {};
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

      // Write back to S3
      await writeJsonToS3(fileName, jsonData.data);

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

    const jsonData = await readJsonFromS3WithFallback([fileName]);

    // Find employee
    const employeeIndex = jsonData.data.employees.findIndex(
      (emp: any) => emp.employeeId === employeeId
    );

    if (employeeIndex === -1) {
      return NextResponse.json(
        { error: 'Employee not found' },
        { status: 404 }
      );
    }

    // Find and update task
    const tasks = jsonData.data.employees[employeeIndex].tasks || {};
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
        { error: 'Task not found', taskId, employeeId },
        { status: 404 }
      );
    }

    // Update priority
    taskList[taskIndex].priority = priority;
    
    if (isManagerTask) {
      if (!tasks.manager) {
        tasks.manager = [];
      }
      tasks.manager[taskIndex].priority = priority;
    } else {
      tasks.ai[taskIndex].priority = priority;
    }

    // Write back to S3
    await writeJsonToS3(fileName, jsonData.data);

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
