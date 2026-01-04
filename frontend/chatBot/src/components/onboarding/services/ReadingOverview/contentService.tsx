import type { ModuleSectionResponse } from '../../../../../types/onboarding';

export class ContentService {
  private static readonly BASE_URL = '/api/onboarding/overview';
  private static cache: Map<string, ModuleSectionResponse> = new Map();

  static async fetchModuleContent(moduleId: string, repo?: string): Promise<ModuleSectionResponse | null> {
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

      if (!data || typeof data !== 'object' || !data.sections || !Array.isArray(data.sections)) {
        return null;
      }

      const typedData: ModuleSectionResponse = data as ModuleSectionResponse;
      this.cache.set(cacheKey, typedData);
      
      return typedData;
    } catch (error) {
      return null;
    }
  }

  static clearCache(): void {
    this.cache.clear();
  }

  static getCachedContent(moduleId: string): ModuleSectionResponse | null {
    return this.cache.get(moduleId) || null;
  }
}
