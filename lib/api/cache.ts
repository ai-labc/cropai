/**
 * Frontend cache utility for API responses
 * Uses localStorage for fast client-side caching
 */

const CACHE_PREFIX = 'cropai_cache_';
const CACHE_TTL_MS = 7 * 24 * 60 * 60 * 1000; // 7 days (longer cache for better performance)

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

export class APICache {
  private static getCacheKey(endpoint: string): string {
    return `${CACHE_PREFIX}${endpoint}`;
  }

  static get<T>(endpoint: string): T | null {
    try {
      const key = this.getCacheKey(endpoint);
      const cached = localStorage.getItem(key);
      
      if (!cached) {
        return null;
      }

      const entry: CacheEntry<T> = JSON.parse(cached);
      const now = Date.now();

      // Check if cache is expired
      if (now > entry.expiresAt) {
        localStorage.removeItem(key);
        return null;
      }

      return entry.data;
    } catch (error) {
      // Cache read error - return null to fetch fresh data
      return null;
    }
  }

  static set<T>(endpoint: string, data: T, ttlMs: number = CACHE_TTL_MS): void {
    try {
      const key = this.getCacheKey(endpoint);
      const now = Date.now();
      
      const entry: CacheEntry<T> = {
        data,
        timestamp: now,
        expiresAt: now + ttlMs,
      };

      localStorage.setItem(key, JSON.stringify(entry));
    } catch (error) {
      // localStorage might be full, try to clear old entries
      this.clearExpired();
    }
  }

  static clear(endpoint?: string): void {
    try {
      if (endpoint) {
        const key = this.getCacheKey(endpoint);
        localStorage.removeItem(key);
      } else {
        // Clear all cache entries
        const keys = Object.keys(localStorage);
        keys.forEach(key => {
          if (key.startsWith(CACHE_PREFIX)) {
            localStorage.removeItem(key);
          }
        });
      }
    } catch (error) {
      // Silently handle cache clear errors
    }
  }

  static clearExpired(): void {
    try {
      const keys = Object.keys(localStorage);
      const now = Date.now();
      
      keys.forEach(key => {
        if (key.startsWith(CACHE_PREFIX)) {
          try {
            const cached = localStorage.getItem(key);
            if (cached) {
              const entry: CacheEntry<any> = JSON.parse(cached);
              if (now > entry.expiresAt) {
                localStorage.removeItem(key);
              }
            }
          } catch {
            // Invalid entry, remove it
            localStorage.removeItem(key);
          }
        }
      });
    } catch (error) {
      // Silently handle expired cache cleanup errors
    }
  }

  static has(endpoint: string): boolean {
    const cached = this.get(endpoint);
    return cached !== null;
  }
}

