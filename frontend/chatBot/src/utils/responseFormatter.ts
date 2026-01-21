/**
 * Response formatting utility for chatbot responses.
 * Converts plain text responses with special formatting into proper markdown
 * for better UI display.
 */

/**
 * Format chatbot response for professional UI display.
 * 
 * Converts:
 * - Triple-quoted data blocks (''') to markdown code blocks
 * - Special symbols (@@, #) to formatted text
 * - Code changes/diffs to syntax-highlighted code blocks
 * - Inline code patterns to proper markdown
 */
export function formatResponseForUI(response: string): string {
  if (!response) {
    return response;
  }

  // Step 1: Handle triple-quoted blocks ('''data''')
  let formatted = formatTripleQuotedBlocks(response);

  // Step 2: Handle code blocks that might be in triple quotes or other formats
  formatted = formatCodeBlocks(formatted);

  // Step 3: Handle special symbols (@@, #) in context
  formatted = formatSpecialSymbols(formatted);

  // Step 4: Handle diff/code change patterns
  formatted = formatCodeChanges(formatted);

  // Step 5: Clean up any remaining formatting issues
  formatted = cleanupFormatting(formatted);

  return formatted;
}

/**
 * Convert triple-quoted blocks to markdown code blocks.
 * Handles patterns like:
 * - '''data'''
 * - '''python code'''
 * - '''json data'''
 * - '''data''' (inline)
 */
function formatTripleQuotedBlocks(text: string): string {
  // First, handle multi-line triple-quoted blocks
  // Pattern: '''lang\ncontent\n''' or '''\ncontent\n'''
  const multiLinePattern = /'''(\w+)?\s*\n([\s\S]*?)\n'''/g;

  let result = text.replace(multiLinePattern, (match, lang, content) => {
    const detectedLang = lang || detectLanguage(content);
    return `\`\`\`${detectedLang}\n${content}\n\`\`\``;
  });

  // Handle inline triple quotes ('''data''') - convert to inline code
  // But avoid matching if it's part of a multi-line block we already processed
  result = result.replace(/'''([^'\n]+)'''/g, '`$1`');

  return result;
}

/**
 * Format code blocks that might be improperly formatted.
 * Detects code patterns and wraps them in proper markdown code blocks.
 */
function formatCodeBlocks(text: string): string {
  // Handle cases where code is between specific markers
  // Pattern: lines starting with +, -, or | (diff markers)
  const diffPattern = /((?:^[+\-|].*$\n?)+)/gm;

  return text.replace(diffPattern, (match) => {
    const lines = match.trim().split('\n');
    if (lines.length > 2) {
      // Only format if multiple lines
      return `\`\`\`diff\n${match.trim()}\n\`\`\``;
    }
    return match;
  });
}

/**
 * Format special symbols (@@, #) for better display.
 * - @@ symbols (often used for mentions or tags) -> formatted badges
 * - # symbols (hashtags or references) -> formatted text
 */
function formatSpecialSymbols(text: string): string {
  // Format @@ mentions as inline code/badges
  // Pattern: @@username or @@tag
  let result = text.replace(/@@(\w+)/g, '`@$1`');

  // Format standalone # symbols that aren't part of markdown headers
  // Only format if it's not already part of a markdown header
  // Format hashtags that are inline (not headers)
  result = result.replace(/(?<!^)#(\w+)/gm, '`#$1`');

  return result;
}

/**
 * Format code changes/diffs for display in code viewer.
 * Detects patterns like:
 * - +added lines
 * - -removed lines
 * - File paths with changes
 * - Function signatures with changes
 */
function formatCodeChanges(text: string): string {
  // Detect diff-like content
  const diffLines = text.match(/^[+\-].*$/gm);
  
  if (diffLines && diffLines.length > 3) {
    // Likely a code diff
    const lines = text.split('\n');
    let diffStart: number | null = null;
    let diffEnd: number | null = null;

    for (let i = 0; i < lines.length; i++) {
      if (/^[+\-]/.test(lines[i].trim())) {
        if (diffStart === null) {
          diffStart = i;
        }
        diffEnd = i + 1;
      }
    }

    if (diffStart !== null && diffEnd !== null) {
      // Extract context before and after
      const before = lines.slice(0, diffStart).join('\n');
      const diffContent = lines.slice(diffStart, diffEnd).join('\n');
      const after = lines.slice(diffEnd).join('\n');

      // Format the diff section
      const formattedDiff = `\`\`\`diff\n${diffContent}\n\`\`\``;

      // Reconstruct with formatted diff
      const parts = [before, formattedDiff, after].filter(p => p.trim());
      return parts.join('\n\n');
    }
  }

  return text;
}

/**
 * Detect programming language from content.
 */
function detectLanguage(content: string): string {
  const contentLower = content.toLowerCase().trim();

  // Language detection patterns
  const patterns: Record<string, RegExp[]> = {
    python: [
      /\b(def|class|import|from|if __name__|print\(|lambda\s)/,
      /\b(True|False|None)\b/,
      /->\s*\w+:/, // Type hints
    ],
    javascript: [
      /\b(function|const|let|var|=>|console\.log)/,
      /\{.*\}/, // Object literals
    ],
    json: [
      /^\s*[\{\[]/, // Starts with { or [
      /"[^"]+":\s*/, // JSON key-value pairs
    ],
    yaml: [
      /^\s*\w+:\s*/, // YAML key-value
      /^\s*-\s+/, // YAML list
    ],
    sql: [
      /\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN)\b/i,
      /CREATE\s+TABLE/i,
    ],
    bash: [
      /^\s*#!/, // Shebang
      /\$\{|\$\(/, // Variable expansion
    ],
    html: [
      /<[a-z]+[^>]*>/i,
      /<\/[a-z]+>/i,
    ],
    css: [
      /\{[^}]*:[^}]*\}/,
      /@media|@import/i,
    ],
  };

  for (const [lang, langPatterns] of Object.entries(patterns)) {
    const matches = langPatterns.filter(pattern => pattern.test(contentLower));
    if (matches.length >= 2) {
      // At least 2 patterns match
      return lang;
    }
  }

  // Check for specific file extensions or keywords
  if (/\.py|python/i.test(contentLower)) {
    return 'python';
  }
  if (/\.(js|ts)|javascript|typescript/i.test(contentLower)) {
    return 'javascript';
  }
  if (/\.json/i.test(contentLower)) {
    return 'json';
  }

  return 'text'; // Default
}

/**
 * Clean up any formatting issues and ensure proper spacing.
 */
function cleanupFormatting(text: string): string {
  // Remove excessive blank lines (more than 2 consecutive)
  let result = text.replace(/\n{3,}/g, '\n\n');

  // Ensure code blocks have proper spacing
  result = result.replace(/```(\w+)\n([^`]+)```/g, '```$1\n$2\n```');

  // Fix inline code that might have been double-formatted
  result = result.replace(/``([^`]+)``/g, '`$1`');

  // Ensure proper spacing around code blocks
  result = result.replace(/([^\n])\n```/g, '$1\n\n```');
  result = result.replace(/```\n([^\n])/g, '```\n\n$1');

  return result.trim();
}

