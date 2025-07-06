/**
 * Typisierte localStorage Wrapper
 */
export class TypedStorage {
  private prefix: string;

  constructor(prefix: string = 'llm-frontend') {
    this.prefix = prefix;
  }

  private getKey(key: string): string {
    return `${this.prefix}:${key}`;
  }

  set<T>(key: string, value: T): void {
    try {
      localStorage.setItem(this.getKey(key), JSON.stringify(value));
    } catch (error) {
      console.error('Error saving to localStorage:', error);
    }
  }

  get<T>(key: string): T | null {
    try {
      const item = localStorage.getItem(this.getKey(key));
      return item ? JSON.parse(item) : null;
    } catch (error) {
      console.error('Error reading from localStorage:', error);
      return null;
    }
  }

  remove(key: string): void {
    try {
      localStorage.removeItem(this.getKey(key));
    } catch (error) {
      console.error('Error removing from localStorage:', error);
    }
  }

  clear(): void {
    try {
      const keys = Object.keys(localStorage);
      keys.forEach((key) => {
        if (key.startsWith(this.prefix)) {
          localStorage.removeItem(key);
        }
      });
    } catch (error) {
      console.error('Error clearing localStorage:', error);
    }
  }

  has(key: string): boolean {
    return localStorage.getItem(this.getKey(key)) !== null;
  }
}

// Instanz für die App
export const storage = new TypedStorage();

// Spezifische Storage-Funktionen für häufig verwendete Daten
export const authStorage = {
  setToken: (token: string) => localStorage.setItem('llm-frontend:auth-token', token),
  getToken: () => localStorage.getItem('llm-frontend:auth-token'),
  removeToken: () => localStorage.removeItem('llm-frontend:auth-token'),
  
  setRefreshToken: (token: string) => localStorage.setItem('llm-frontend:refresh-token', token),
  getRefreshToken: () => localStorage.getItem('llm-frontend:refresh-token'),
  removeRefreshToken: () => localStorage.removeItem('llm-frontend:refresh-token'),
  
  clearAll: () => {
    localStorage.removeItem('llm-frontend:auth-token');
    localStorage.removeItem('llm-frontend:refresh-token');
  }
};

export const themeStorage = {
  setTheme: (theme: 'light' | 'dark' | 'system') => 
    localStorage.setItem('llm-frontend:theme', theme),
  getTheme: (): 'light' | 'dark' | 'system' => 
    (localStorage.getItem('llm-frontend:theme') as 'light' | 'dark' | 'system') || 'system',
  removeTheme: () => localStorage.removeItem('llm-frontend:theme')
};

export const settingsStorage = {
  setLanguage: (lang: string) => storage.set('settings:language', lang),
  getLanguage: () => storage.get<string>('settings:language') || 'de',
  setModelDefaults: (defaults: Record<string, any>) => storage.set('settings:model_defaults', defaults),
  getModelDefaults: () => storage.get<Record<string, any>>('settings:model_defaults') || {},
};

export const generalStorage = new TypedStorage('llm-frontend'); 