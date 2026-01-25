import mermaid from 'mermaid';

export class MermaidRenderer {
  private static initialized = false;

  static initialize(darkMode: boolean): void {
    mermaid.initialize({
      startOnLoad: false,
      theme: darkMode ? 'dark' : 'default',
      securityLevel: 'loose',
      fontFamily: 'Inter, system-ui, sans-serif',
      themeVariables: darkMode
        ? {
            primaryColor: '#60a5fa',
            primaryTextColor: '#fff',
            primaryBorderColor: '#3b82f6',
            lineColor: '#8b5cf6',
            secondaryColor: '#a78bfa',
            tertiaryColor: '#c084fc',
          }
        : {
            primaryColor: '#6366f1',
            primaryTextColor: '#fff',
            primaryBorderColor: '#4f46e5',
            lineColor: '#06b6d4',
            secondaryColor: '#14b8a6',
            tertiaryColor: '#0891b2',
          },
    });
    this.initialized = true;
  }

  static sanitizeMermaidCode(code: string): string {
    let sanitized = code
      .trim()
      .replace(/\\n/g, '\n')
      .replace(/\\"/g, '"')
      .replace(/\\\\/g, '\\')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'");

    sanitized = sanitized.replace(/^``````\s*$/i, '');

    return sanitized.trim();
  }



  static fixTruncatedMermaidCode(code: string): string {
    const lines = code.split('\n');
    const result: string[] = [];

    for (const line of lines) {
      result.push(line);
      if (line.trim().match(/^(end|stop)$/i)) break;
    }

    return result.join('\n');
  }


  static isValidMermaidCode(code: string): boolean {
    const validStarters = [
      'graph',
      'flowchart',
      'sequenceDiagram',
      'classDiagram',
      'stateDiagram',
      'erDiagram',
      'gantt',
      'pie',
      'journey',
      'gitGraph',
      'quadrantChart',
      'requirementDiagram',
      'C4Context',
    ];

    const firstLine = code.trim().split('\n')[0].trim().toLowerCase();
    const hasValidStarter = validStarters.some(starter => 
      firstLine.startsWith(starter.toLowerCase())
    );

    if (!hasValidStarter) {
      return false;
    }

    const lines = code.trim().split('\n').filter(l => l.trim());
    return lines.length > 1;
  }

  static async render(code: string, id: string): Promise<string> {
    if (!this.initialized) {
      this.initialize(false);
    }

    try {
      const sanitizedCode = this.sanitizeMermaidCode(code);

      if (!sanitizedCode.trim()) {
        return '';
      }

      const { svg } = await mermaid.render(id, sanitizedCode);
      return svg;
    } catch (error: any) {
      console.error('Mermaid render error:', error);
      return this.createErrorPlaceholder(
        error?.message || 'Invalid Mermaid syntax'
      );
    }
  }


  static createErrorPlaceholder(errorMessage: string): string {
    return `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 100" class="mermaid-error">
        <rect width="400" height="100" fill="#fee" stroke="#f88" stroke-width="2" rx="8"/>
        <text x="200" y="40" text-anchor="middle" font-family="monospace" font-size="12" fill="#c00">
          Diagram could not be rendered
        </text>
        <text x="200" y="65" text-anchor="middle" font-family="monospace" font-size="10" fill="#800">
          ${errorMessage.substring(0, 50)}
        </text>
      </svg>
    `;
  }

  static async renderMultiple(codes: string[]): Promise<string[]> {
    const results: string[] = [];

    for (let i = 0; i < codes.length; i++) {
      try {
        const svg = await this.render(codes[i], `mermaid-${i}-${Date.now()}`);
        results.push(svg);
        
        if (i < codes.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 50));
        }
      } catch (error) {
        console.error(`Failed to render diagram ${i}:`, error);
        results.push('');
      }
    }

    const successCount = results.filter(r => r && r.length > 0).length;
    return results;
  }

  static clearCache(): void {
    this.initialized = false;
  }
}
