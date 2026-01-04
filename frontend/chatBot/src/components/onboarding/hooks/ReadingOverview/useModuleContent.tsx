import { useState, useCallback } from 'react';
import { ContentService } from '../../services/ReadingOverview/contentService';
import type { ModuleSectionResponse } from '../../../../../types/onboarding';

interface UseModuleContentReturn {
  content: ModuleSectionResponse | null;
  isLoading: boolean;
  error: string | null;
  fetchContent: (moduleId: string, repo?: string) => Promise<void>;
  clearContent: () => void;
}

export function useModuleContent(): UseModuleContentReturn {
  const [content, setContent] = useState<ModuleSectionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchContent = useCallback(async (moduleId: string, repo?: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await ContentService.fetchModuleContent(moduleId, repo);
      
      if (!data) {
        throw new Error('Failed to fetch content');
      }

      setContent(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      setContent(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearContent = useCallback(() => {
    setContent(null);
    setError(null);
    setIsLoading(false);
  }, []);

  return {
    content,
    isLoading,
    error,
    fetchContent,
    clearContent,
  };
}
