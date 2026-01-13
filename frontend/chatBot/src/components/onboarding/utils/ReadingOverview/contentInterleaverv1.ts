/**
 * Content Interleaver Utility
 * 
 * Reorganizes reading card content and QnA items in an interleaved pattern:
 * Positions 1-4: Content items
 * Position 5: QnA section
 * Positions 6-10: Content items
 * Position 11: QnA section
 * Positions 12-15: Content items
 * Position 16: QnA section
 * Positions 17-18: Content items
 * Position 19: QnA section
 * Positions 20-23: Content items
 * Position 24: QnA section
 */

export interface ContentItem {
  itemKey: string;
  itemTitle: string;
  question: string;
  answer: string;
  quality: number;
  qna: QuestionData[];
}

export interface QuestionData {
  question: string;
  options: { [key: string]: string };
  correct_answer: string;
  explanation: string;
  subsection?: string;
}

export interface ProcessedSection {
  sectionId: string;
  sectionTitle: string;
  items: ContentItem[];
}

export interface InterleavedItem {
  type: 'content' | 'qna';
  position: number;
  data: ContentItem | QuestionData | QuestionData[];
}

export interface InterleavedSection {
  sectionId: string;
  sectionTitle: string;
  interleavedItems: InterleavedItem[];
  totalItems: number;
}

/**
 * Defines the interleaving pattern
 * Each tuple represents: [content_count, qna_position]
 */
const INTERLEAVE_PATTERN: Array<{content: number; qnaPosition: number}> = [
  { content: 4, qnaPosition: 5 },      // 4 items, then QnA at position 5
  { content: 5, qnaPosition: 11 },     // 5 more items, then QnA at position 11
  { content: 4, qnaPosition: 16 },     // 4 more items, then QnA at position 16
  { content: 2, qnaPosition: 19 },     // 2 more items, then QnA at position 19
  { content: 4, qnaPosition: 24 },     // 4 more items, then QnA at position 24
];

/**
 * Interleaves content items and QnA questions for a section
 * @param section - The processed section with content items
 * @returns Interleaved section with content and QnA mixed
 */
export function interleaveSectionContent(section: ProcessedSection): InterleavedSection {
  const interleavedItems: InterleavedItem[] = [];
  let contentIndex = 0;
  let qnaIndex = 0;
  let position = 1;

  // Collect all unique QnA questions from all items
  const allQnA: QuestionData[] = [];
  const qnaByPosition: { [key: number]: QuestionData[] } = {};
  
  section.items.forEach((item, idx) => {
    if (item.qna && item.qna.length > 0) {
      allQnA.push(...item.qna);
      // Map QnA to the position where they should appear after their content item
      const patternIndex = INTERLEAVE_PATTERN.findIndex(p => p.qnaPosition >= position);
      if (patternIndex !== -1) {
        if (!qnaByPosition[INTERLEAVE_PATTERN[patternIndex].qnaPosition]) {
          qnaByPosition[INTERLEAVE_PATTERN[patternIndex].qnaPosition] = [];
        }
        qnaByPosition[INTERLEAVE_PATTERN[patternIndex].qnaPosition].push(...item.qna);
      }
    }
  });

  // Build interleaved items according to pattern
  let globalContentCount = 0;
  
  for (const patternRule of INTERLEAVE_PATTERN) {
    // Add content items
    for (let i = 0; i < patternRule.content; i++) {
      if (contentIndex < section.items.length) {
        interleavedItems.push({
          type: 'content',
          position: position,
          data: section.items[contentIndex],
        });
        contentIndex++;
        position++;
        globalContentCount++;
      } else {
        break;
      }
    }

    // Add QnA item at specified position if available
    if (qnaIndex < allQnA.length) {
      // Get QnA questions for this batch
      const batchQnA: QuestionData[] = [];
      const itemsInThisBatch = section.items.slice(
        Math.max(0, contentIndex - patternRule.content),
        contentIndex
      );
      
      itemsInThisBatch.forEach((item) => {
        if (item.qna && item.qna.length > 0) {
          batchQnA.push(...item.qna);
        }
      });

      if (batchQnA.length > 0) {
        interleavedItems.push({
          type: 'qna',
          position: position,
          data: batchQnA,
        });
        position++;
        qnaIndex += batchQnA.length;
      }
    }
  }

  // Add any remaining content items if there are more than what fits in the pattern
  while (contentIndex < section.items.length) {
    interleavedItems.push({
      type: 'content',
      position: position,
      data: section.items[contentIndex],
    });
    contentIndex++;
    position++;
  }

  // Add any remaining QnA if there are more than what fits in the pattern
  while (qnaIndex < allQnA.length) {
    const remainingQnA = allQnA.slice(qnaIndex, qnaIndex + 1);
    interleavedItems.push({
      type: 'qna',
      position: position,
      data: remainingQnA,
    });
    position++;
    qnaIndex += remainingQnA.length;
  }

  return {
    sectionId: section.sectionId,
    sectionTitle: section.sectionTitle,
    interleavedItems,
    totalItems: interleavedItems.length,
  };
}

/**
 * Interleaves all sections in a module
 * @param sections - Array of processed sections
 * @returns Array of interleaved sections
 */
export function interleaveModuleSections(sections: ProcessedSection[]): InterleavedSection[] {
  return sections.map(section => interleaveSectionContent(section));
}

/**
 * Generates navigation for interleaved content
 * @param interleavedSections - Sections with interleaved items
 * @returns Navigation info for pagination
 */
export function generateInterleavedNavigation(interleavedSections: InterleavedSection[]) {
  let totalItems = 0;
  const sectionNavigation: Array<{
    sectionIndex: number;
    sectionId: string;
    sectionTitle: string;
    startPosition: number;
    endPosition: number;
    itemCount: number;
  }> = [];

  interleavedSections.forEach((section, sectionIndex) => {
    sectionNavigation.push({
      sectionIndex,
      sectionId: section.sectionId,
      sectionTitle: section.sectionTitle,
      startPosition: totalItems + 1,
      endPosition: totalItems + section.totalItems,
      itemCount: section.totalItems,
    });
    totalItems += section.totalItems;
  });

  return {
    totalItems,
    sectionNavigation,
  };
}
