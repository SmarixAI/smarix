import { useState, useCallback } from 'react';
import { QAService } from '../../services/QASession/contentService';
import type { QAModuleResponse } from '../../../../../types/onboarding';

interface UseQAModuleReturn {
  qaData: QAModuleResponse | null;
  isLoading: boolean;
  error: string | null;
  fetchQA: (moduleId: string) => Promise<void>;
  clearQA: () => void;
}

export function useQAModule(): UseQAModuleReturn {
  const [qaData, setQAData] = useState<QAModuleResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchQA = useCallback(async (moduleId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await QAService.fetchQAModule(moduleId);
      
      if (!data) {
        throw new Error('Failed to fetch Q&A data');
      }

      setQAData(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      setQAData(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearQA = useCallback(() => {
    setQAData(null);
    setError(null);
    setIsLoading(false);
  }, []);

  return {
    qaData,
    isLoading,
    error,
    fetchQA,
    clearQA,
  };
}
