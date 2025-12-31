import type { QAModuleResponse } from '../../../../../types/onboarding';

export class QAService {
  private static readonly BASE_URL = '/api/onboarding/qa';
  private static cache: Map<string, QAModuleResponse> = new Map();

  static async fetchQAModule(moduleId: string): Promise<QAModuleResponse | null> {
    if (this.cache.has(moduleId)) {
      return this.cache.get(moduleId)!;
    }

    try {
      const response = await fetch(`${this.BASE_URL}/${moduleId}`);
      
      if (!response.ok) {
        return null;
      }

      const data = await response.json();

      if (!data || typeof data !== 'object' || !data.questions || !Array.isArray(data.questions)) {
        return null;
      }

      const typedData: QAModuleResponse = data as QAModuleResponse;
      this.cache.set(moduleId, typedData);
      
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
