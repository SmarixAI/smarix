import { NextRequest, NextResponse } from 'next/server';
import { readJsonFromS3WithFallback, writeJsonToS3 } from '../../../../components/offboarding/s3Utils';

const RESOURCES = ['tasks', 'handovers', 'documents'] as const;
type Resource = (typeof RESOURCES)[number];

function getResource(params: { resource?: string[] }): Resource | null {
  const name = params.resource?.[0];
  return name && RESOURCES.includes(name as Resource) ? (name as Resource) : null;
}

const cacheHeaders = { 'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400' };
const noCache = { 'Cache-Control': 'no-cache' };

function getEmployeeIdFromRequest(request: NextRequest): string | null {
  return request.nextUrl.searchParams.get('employeeId')?.trim() || null;
}

/** Treat S3 missing key or "none of the files found" as non-fatal so we return empty data with 200. */
function isS3NotFoundError(error: unknown): boolean {
  const msg = error instanceof Error ? error.message : String(error);
  const code = (error as { Code?: string })?.Code;
  return code === 'NoSuchKey' || msg.includes('NoSuchKey') || msg.includes('None of the files found');
}

// --- GET handlers: read from Offboarding/{employeeId}/... ---
async function getTasks(employeeId: string) {
  try {
    const { data: jsonData } = await readJsonFromS3WithFallback(
      ['tasks.json', '4employee_tasks_with_metadata_finalCallData.json'],
      employeeId
    );
    const payload = jsonData.data ? { employees: jsonData.data.employees ?? [] } : jsonData;
    return NextResponse.json(payload, { headers: cacheHeaders });
  } catch (error) {
    if (isS3NotFoundError(error)) {
      return NextResponse.json({ employees: [] }, { headers: cacheHeaders });
    }
    throw error;
  }
}

async function getHandovers(employeeId: string) {
  try {
    const { data: jsonData } = await readJsonFromS3WithFallback(['handover_tasks.json'], employeeId);
    return NextResponse.json(jsonData, { headers: cacheHeaders });
  } catch (error) {
    if (isS3NotFoundError(error)) {
      return NextResponse.json({ employees: [] }, { headers: cacheHeaders });
    }
    throw error;
  }
}

async function getDocuments(employeeId: string) {
  try {
    const { data: jsonData } = await readJsonFromS3WithFallback(['documentation_tasks.json'], employeeId);
    return NextResponse.json(jsonData, { headers: cacheHeaders });
  } catch (error) {
    if (isS3NotFoundError(error)) {
      return NextResponse.json({ employees: [] }, { headers: cacheHeaders });
    }
    throw error;
  }
}

// --- POST handlers: read/write Offboarding/{employeeId}/... ---
const TASKS_FILE = 'tasks.json';

async function postTasks(body: any) {
  const { employeeId, taskId, priority, status, title, action } = body;
  if (!employeeId) return NextResponse.json({ error: 'Employee ID is required' }, { status: 400 });
  const { data: jsonData } = await readJsonFromS3WithFallback(
    [TASKS_FILE, '4employee_tasks_with_metadata_finalCallData.json'],
    employeeId
  );
  const employees = jsonData.data?.employees ?? jsonData.employees ?? [];
  const employeeIndex = employees.findIndex((emp: any) => emp.employeeId === employeeId);
  if (employeeIndex === -1) return NextResponse.json({ error: 'Employee not found' }, { status: 404 });
  const emp = employees[employeeIndex];
  if (!emp.tasks) emp.tasks = { ai: [], manager: [] };
  if (!emp.tasks.manager) emp.tasks.manager = [];

  if (action === 'add' && title && priority) {
    const newTask = { id: `${employeeId}-m${emp.tasks.manager.length + 1}`, title, priority, tags: ['Manual'], source: 'Manager' };
    emp.tasks.manager.push(newTask);
    const payload = jsonData.data ? jsonData : { data: { employees } };
    await writeJsonToS3(TASKS_FILE, payload, employeeId);
    return NextResponse.json({ success: true, task: newTask }, { headers: noCache });
  }

  if (status !== undefined && status !== null && !priority) {
    if (!taskId) return NextResponse.json({ error: 'Task ID is required' }, { status: 400 });
    const tasks = emp.tasks;
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
    if (taskIndex === -1) return NextResponse.json({ error: 'Task not found' }, { status: 404 });
    taskList[taskIndex].status = status;
    const payload = jsonData.data ? jsonData : { data: { employees } };
    await writeJsonToS3(TASKS_FILE, payload, employeeId);
    return NextResponse.json({ success: true, task: taskList[taskIndex] }, { headers: noCache });
  }

  if (!taskId || !priority) return NextResponse.json({ error: 'Task ID and Priority are required' }, { status: 400 });
  const tasks = emp.tasks;
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
  if (taskIndex === -1) return NextResponse.json({ error: 'Task not found' }, { status: 404 });
  taskList[taskIndex].priority = priority;
  const payload = jsonData.data ? jsonData : { data: { employees } };
  await writeJsonToS3(TASKS_FILE, payload, employeeId);
  return NextResponse.json({ success: true, task: taskList[taskIndex] }, { headers: noCache });
}

async function postHandovers(body: any) {
  const { employeeId, handoverId, priority } = body;
  if (!employeeId || !handoverId || !priority) return NextResponse.json({ error: 'Employee ID, Handover ID, and Priority are required' }, { status: 400 });
  const { data: jsonData } = await readJsonFromS3WithFallback(['handover_tasks.json'], employeeId);
  const emp = jsonData.employees?.[0];
  if (!emp) return NextResponse.json({ error: 'Employee not found' }, { status: 404 });
  const handovers = emp.handovers || [];
  const handoverIndex = handovers.findIndex((h: any) => h.id === handoverId);
  if (handoverIndex === -1) return NextResponse.json({ error: 'Handover not found' }, { status: 404 });
  handovers[handoverIndex].priority = priority;
  await writeJsonToS3('handover_tasks.json', jsonData, employeeId);
  return NextResponse.json({ success: true, handover: handovers[handoverIndex] }, { headers: noCache });
}

async function postDocuments(body: any) {
  const { employeeId, documentId, priority, status } = body;
  if (!employeeId || !documentId) return NextResponse.json({ error: 'Employee ID and Document ID are required' }, { status: 400 });
  if (priority === undefined && status === undefined) return NextResponse.json({ error: 'Either Priority or Status must be provided' }, { status: 400 });
  const { data: jsonData } = await readJsonFromS3WithFallback(['documentation_tasks.json'], employeeId);
  const emp = jsonData.employees?.[0];
  if (!emp) return NextResponse.json({ error: 'Employee not found' }, { status: 404 });
  const documents = emp.documents || [];
  const documentIndex = documents.findIndex((d: any) => d.id === documentId);
  if (documentIndex === -1) return NextResponse.json({ error: 'Document not found' }, { status: 404 });
  if (priority !== undefined) documents[documentIndex].priority = priority;
  if (status !== undefined) documents[documentIndex].status = status;
  await writeJsonToS3('documentation_tasks.json', jsonData, employeeId);
  return NextResponse.json({ success: true, document: documents[documentIndex] }, { headers: noCache });
}

export async function GET(request: NextRequest, { params }: { params: Promise<{ resource?: string[] }> }) {
  const resource = getResource(await params);
  if (!resource) return NextResponse.json({ error: 'Invalid resource. Use: tasks, handovers, documents' }, { status: 400 });
  const employeeId = getEmployeeIdFromRequest(request);
  if (!employeeId) return NextResponse.json({ error: 'Query parameter employeeId is required' }, { status: 400 });
  try {
    switch (resource) {
      case 'tasks': return await getTasks(employeeId);
      case 'handovers': return await getHandovers(employeeId);
      case 'documents': return await getDocuments(employeeId);
    }
  } catch (error) {
    const msg = resource === 'tasks' ? 'tasks' : resource === 'handovers' ? 'handovers' : 'documents';
    return NextResponse.json({ error: `Failed to load ${msg} data`, details: error instanceof Error ? error.message : 'Unknown error' }, { status: 500 });
  }
  return NextResponse.json({ error: 'Not found' }, { status: 404 });
}

export async function POST(request: NextRequest, { params }: { params: Promise<{ resource?: string[] }> }) {
  const resource = getResource(await params);
  if (!resource) return NextResponse.json({ error: 'Invalid resource. Use: tasks, handovers, documents' }, { status: 400 });
  try {
    const body = await request.json();
    switch (resource) {
      case 'tasks': return await postTasks(body);
      case 'handovers': return await postHandovers(body);
      case 'documents': return await postDocuments(body);
    }
  } catch (error) {
    const msg = resource === 'tasks' ? 'task' : resource === 'handovers' ? 'handover' : 'document';
    return NextResponse.json({ error: `Failed to update ${msg}`, details: error instanceof Error ? error.message : 'Unknown error' }, { status: 500 });
  }
  return NextResponse.json({ error: 'Not found' }, { status: 404 });
}
