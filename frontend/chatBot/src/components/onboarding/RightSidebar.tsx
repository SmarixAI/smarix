'use client';

import {
  BookOpen,
  Bug,
  CheckCircle2,
  Lightbulb,
  ExternalLink,
} from 'lucide-react';
import { Inter } from 'next/font/google';

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600'] });

interface RightSidebarProps {
  context?: 'bug-fix' | 'practice' | 'overview';
}

export default function RightSidebar({
  context = 'bug-fix',
}: RightSidebarProps) {
  return (
    <aside
      className={`${inter.className} h-full overflow-y-auto px-3 py-4 space-y-4`}
    >
      {/* ===================== CONTEXT HEADER ===================== */}
      <div className="rounded-xl border bg-white px-4 py-3">
        <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">
          Bug Fix Mode
        </p>
        <h3 className="text-sm font-semibold text-slate-900 mt-1">
          Improve Your Debugging Skills
        </h3>
        <p className="text-xs text-slate-600 mt-1 leading-relaxed">
          Use the guidance on this panel to approach problems
          methodically and efficiently.
        </p>
      </div>

      {/* ===================== GUIDES ===================== */}
      <Card title="Guides & Best Practices" icon={Lightbulb}>
        <GuideRow
          icon={Bug}
          title="Systematic Debugging"
          description="Reproduce the issue, isolate the cause, then apply the fix."
        />
        <GuideRow
          icon={CheckCircle2}
          title="Validate Your Fix"
          description="Ensure existing behavior is not broken by your change."
        />
        <GuideRow
          icon={BookOpen}
          title="Read PR Context"
          description="Understand why the change exists before modifying code."
        />
      </Card>

      {/* ===================== QUICK CHECKLIST ===================== */}
      <Card title="Quick Debug Checklist">
        <ChecklistItem text="Can you reproduce the bug locally?" />
        <ChecklistItem text="Is the root cause clearly identified?" />
        <ChecklistItem text="Are edge cases handled?" />
        <ChecklistItem text="Does the fix affect other modules?" />
      </Card>

      {/* ===================== RESOURCES ===================== */}
      <Card title="Helpful Resources">
        <ResourceLink text="How to Read Large Diffs" />
        <ResourceLink text="Effective Code Reviews" />
        <ResourceLink text="Debugging Production Issues" />
      </Card>

      {/* ===================== PRO TIP ===================== */}
      <div className="rounded-xl border bg-gradient-to-br from-slate-50 to-white px-4 py-4">
        <div className="flex items-start gap-2">
          <span className="text-lg">💡</span>
          <div>
            <p className="text-sm font-medium text-slate-800">
              Pro Tip
            </p>
            <p className="text-xs text-slate-600 leading-relaxed mt-1">
              If a fix feels complex, step back and ask:
              <br />
              <strong>
                “What assumption in the code is failing?”
              </strong>
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}

/* ===================== UI BUILDING BLOCKS ===================== */

function Card({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon?: any;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border bg-white px-4 py-3">
      <div className="flex items-center gap-2 mb-3">
        {Icon && <Icon className="w-4 h-4 text-slate-500" />}
        <h4 className="text-sm font-semibold text-slate-800">
          {title}
        </h4>
      </div>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

function GuideRow({
  icon: Icon,
  title,
  description,
}: {
  icon: any;
  title: string;
  description: string;
}) {
  return (
    <div className="flex gap-3 p-2 rounded-lg hover:bg-slate-50 transition cursor-pointer">
      <Icon className="w-5 h-5 text-blue-600 mt-0.5" />
      <div>
        <p className="text-sm font-medium text-slate-800">
          {title}
        </p>
        <p className="text-xs text-slate-600 leading-relaxed">
          {description}
        </p>
      </div>
    </div>
  );
}

function ChecklistItem({ text }: { text: string }) {
  return (
    <div className="flex items-start gap-2 text-xs text-slate-700">
      <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-slate-400" />
      <span>{text}</span>
    </div>
  );
}

function ResourceLink({ text }: { text: string }) {
  return (
    <div className="flex items-center justify-between text-sm text-blue-600 hover:underline cursor-pointer">
      <span>{text}</span>
      <ExternalLink className="w-3.5 h-3.5" />
    </div>
  );
}
