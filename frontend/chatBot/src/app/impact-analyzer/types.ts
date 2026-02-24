export interface FileNode {
  id: string;
  name: string;
  path: string;
  riskScore: number;
  symbols: string[];
  content: string;
}

export interface SymbolImpact {
  callers: string[];
  callees: string[];
  risk: number;
  impactRadius: number;
}