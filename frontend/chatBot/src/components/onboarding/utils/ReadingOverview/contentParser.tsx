import type { ContentSection } from '../../../../../types/onboarding';

export class ContentParser {
  static parseContent(text: string): ContentSection[] {
    if (!text || typeof text !== 'string') {
      return [];
    }

    // CRITICAL: Unescape any escaped backticks from JSON
    let unescapedText = text
      .replace(/\\`\\`\\`/g, '```')  // Handle escaped backticks
      .replace(/&#96;&#96;&#96;/g, '```')  // Handle HTML entities
      .replace(/\\\\/g, '\\');  // Handle double backslashes


    const sections: ContentSection[] = [];
    let mermaidIndex = 0;
    const codeBlockPlaceholders = new Map<string, {
      type: 'code' | 'mermaid';
      content: string;
      language?: string;
      index?: number;
    }>();
    
    let placeholderIndex = 0;

    // Match code blocks: ```language\ncontent\n```
    const codeBlockRegex = /```([^\n`]*)\n([\s\S]*?)```/g;
    
    let processedText = unescapedText.replace(codeBlockRegex, (match, language, code) => {
      const placeholder = `__CODE_BLOCK_${placeholderIndex}__`;
      const lang = (language || '').trim().toLowerCase();
      
      
      if (lang === 'mermaid') {
        codeBlockPlaceholders.set(placeholder, {
          type: 'mermaid',
          content: code.trim(),
          index: mermaidIndex++,
        });
      } else {
        codeBlockPlaceholders.set(placeholder, {
          type: 'code',
          content: code.trim(),
          language: lang || 'plaintext',
        });
      }
      
      placeholderIndex++;
      return `\n\n${placeholder}\n\n`;
    });


    const parts = processedText.split(/(__CODE_BLOCK_\d+__)/);

    parts.forEach((part) => {
      const trimmedPart = part.trim();
      if (!trimmedPart) return;

      if (trimmedPart.startsWith('__CODE_BLOCK_')) {
        const block = codeBlockPlaceholders.get(trimmedPart);
        if (block) {
          sections.push(block as ContentSection);
        }
      } else {
        sections.push({
          type: 'text',
          content: trimmedPart,
        });
      }
    });

    return sections;
  }

  static extractCodeBlocks(text: string): Array<{ language: string; code: string }> {
    // Unescape first
    const unescaped = text.replace(/\\`\\`\\`/g, '```').replace(/&#96;&#96;&#96;/g, '```');
    
    const codeBlocks: Array<{ language: string; code: string }> = [];
    const regex = /```([^\n`]*)\n([\s\S]*?)```/g;
    let match;

    while ((match = regex.exec(unescaped)) !== null) {
      const language = (match[1] || '').trim().toLowerCase();
      const code = match[2];

      if (language !== 'mermaid') {
        codeBlocks.push({
          language: language || 'plaintext',
          code: code.trim(),
        });
      }
    }

    return codeBlocks;
  }

  static extractMermaidDiagrams(text: string): string[] {
    // Unescape first
    const unescaped = text.replace(/\\`\\`\\`/g, '```').replace(/&#96;&#96;&#96;/g, '```');
    
    const diagrams: string[] = [];
    const regex = /```mermaid\n([\s\S]*?)```/g;
    let match;

    while ((match = regex.exec(unescaped)) !== null) {
      diagrams.push(match[1].trim());
    }

    return diagrams;
  }

  static hasCodeBlocks(text: string): boolean {
    const unescaped = text.replace(/\\`\\`\\`/g, '```').replace(/&#96;&#96;&#96;/g, '```');
    return /```[^\n`]*\n[\s\S]*?```/.test(unescaped);
  }

  static hasMermaidDiagrams(text: string): boolean {
    const unescaped = text.replace(/\\`\\`\\`/g, '```').replace(/&#96;&#96;&#96;/g, '```');
    return /```mermaid\n[\s\S]*?```/gi.test(unescaped);
  }

  static stripCodeBlocks(text: string): string {
    const unescaped = text.replace(/\\`\\`\\`/g, '```').replace(/&#96;&#96;&#96;/g, '```');
    return unescaped.replace(/```[^\n`]*\n[\s\S]*?```/g, '');
  }

  static getTextOnly(text: string): string {
    const unescaped = text.replace(/\\`\\`\\`/g, '```').replace(/&#96;&#96;&#96;/g, '```');
    return unescaped
      .replace(/```[^\n`]*\n[\s\S]*?```/g, '')
      .trim();
  }

  static countSections(text: string): { text: number; code: number; mermaid: number } {
    const codeBlocks = this.extractCodeBlocks(text);
    const mermaidDiagrams = this.extractMermaidDiagrams(text);
    const textContent = this.getTextOnly(text);

    return {
      text: textContent.length > 0 ? 1 : 0,
      code: codeBlocks.length,
      mermaid: mermaidDiagrams.length,
    };
  }
}