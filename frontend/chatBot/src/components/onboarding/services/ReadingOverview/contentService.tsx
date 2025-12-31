import type { ModuleSectionResponse } from '../../../../../types/onboarding';

export class ContentService {
  private static readonly BASE_URL = '/api/onboarding/overview';
  private static cache: Map<string, ModuleSectionResponse> = new Map();

  static async fetchModuleContent(moduleId: string): Promise<ModuleSectionResponse | null> {
    if (this.cache.has(moduleId)) {
      return this.cache.get(moduleId)!;
    }

    try {
      const response = await fetch(`${this.BASE_URL}/${moduleId}`);
      
      if (!response.ok) {
        return null;
      }

      const data = await response.json();

      if (!data || typeof data !== 'object' || !data.sections || !Array.isArray(data.sections)) {
        return null;
      }

      const typedData: ModuleSectionResponse = data as ModuleSectionResponse;
      this.cache.set(moduleId, typedData);
      
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
