export interface UserPreferences {
  cookiesAccepted?: boolean;
  analytics?: boolean;
}

const PREFIX = 'icp_hosting_';

export const LocalStorage = {
  get<T>(key: string, fallback: T): T {
    if (typeof window === 'undefined') return fallback;
    try {
      const raw = window.localStorage.getItem(PREFIX + key);
      return raw ? (JSON.parse(raw) as T) : fallback;
    } catch {
      return fallback;
    }
  },
  set<T>(key: string, value: T): void {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(PREFIX + key, JSON.stringify(value));
  },
  remove(key: string): void {
    if (typeof window === 'undefined') return;
    window.localStorage.removeItem(PREFIX + key);
  },
};

export function getUserPreferences(): UserPreferences {
  return LocalStorage.get<UserPreferences>('preferences', {});
}

export function saveUserPreferences(prefs: UserPreferences): void {
  LocalStorage.set('preferences', prefs);
}
