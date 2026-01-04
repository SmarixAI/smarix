import type { QAModuleResponse } from '../../../../../types/onboarding';

export class QAService {
  private static readonly BASE_URL = '/api/onboarding/qa';
  private static cache: Map<string, QAModuleResponse> = new Map();

  static async fetchQAModule(moduleId: string, repo?: string): Promise<QAModuleResponse | null> {
    const cacheKey = repo ? `${moduleId}-${repo}` : moduleId;
    
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey)!;
    }

    try {
      const url = repo 
        ? `${this.BASE_URL}/${moduleId}?repo=${encodeURIComponent(repo)}`
        : `${this.BASE_URL}/${moduleId}`;
      
      const response = await fetch(url);
      
      if (!response.ok) {
        return null;
      }

      const data = await response.json();

      if (!data || typeof data !== 'object' || !data.questions || !Array.isArray(data.questions)) {
        return null;
      }

      const typedData: QAModuleResponse = data as QAModuleResponse;
      this.cache.set(cacheKey, typedData);
      
      return typedData;
    } catch (error) {
      return null;
    }
  }

  static clearCache(): void {
    this.cache.clear();
  }

  static getCachedContent(moduleId: string): QAModuleResponse | null {
    return this.cache.get(moduleId) || null;
  }
}
