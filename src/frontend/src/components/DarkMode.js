/**
 * Dark Mode 管理器
 */

export class DarkMode {
  constructor() {
    this.key = 'darkMode';
    this.init();
  }

  init() {
    const saved = localStorage.getItem(this.key);
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (saved !== null) {
      this.setMode(saved === 'true');
    } else if (prefersDark) {
      this.setMode(true);
    }

    // 監聽系統主題變化
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
      if (localStorage.getItem(this.key) === null) {
        this.setMode(e.matches);
      }
    });
  }

  setMode(isDark) {
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem(this.key, isDark.toString());
  }

  toggle() {
    const isDark = document.documentElement.classList.contains('dark');
    this.setMode(!isDark);
    return !isDark;
  }

  isDark() {
    return document.documentElement.classList.contains('dark');
  }
}

// 創建全局實例
export const darkMode = new DarkMode();
