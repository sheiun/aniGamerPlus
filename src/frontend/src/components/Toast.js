/**
 * Toast 通知組件
 */

export class Toast {
  constructor() {
    this.container = null;
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.createContainer());
    } else {
      this.createContainer();
    }
  }

  createContainer() {
    if (!this.container && document.body) {
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      this.container.className =
        'fixed top-20 left-1/2 -translate-x-1/2 z-[100] flex flex-col gap-3 pointer-events-none items-center';
      document.body.appendChild(this.container);
    }
  }

  show(message, type = 'success', duration = 3000) {
    if (!this.container) {
      this.createContainer();
    }

    if (!this.container) {
      console.error('Toast container not available');
      return null;
    }

    const toast = document.createElement('div');
    toast.className = 'pointer-events-auto toast-enter';

    const config = {
      success: { bg: 'bg-green-500', icon: 'fa-check-circle' },
      error: { bg: 'bg-red-500', icon: 'fa-times-circle' },
      warning: { bg: 'bg-yellow-500', icon: 'fa-exclamation-triangle' },
      info: { bg: 'bg-blue-500', icon: 'fa-info-circle' },
    };

    const { bg, icon } = config[type] || config.info;

    toast.innerHTML = `
      <div class="${bg} text-white px-6 py-5 rounded-2xl shadow-2xl flex items-center gap-4 min-w-[320px] max-w-md border-2 border-white/20">
        <i class="fas ${icon} text-3xl flex-shrink-0"></i>
        <span class="flex-1 font-semibold text-base leading-relaxed">${message}</span>
        <button class="toast-close ml-2 hover:bg-white/30 rounded-lg p-2 transition-all hover:scale-110 flex-shrink-0">
          <i class="fas fa-times text-lg"></i>
        </button>
      </div>
    `;

    this.container.appendChild(toast);

    // 關閉按鈕
    toast.querySelector('.toast-close').addEventListener('click', () => this.hide(toast));

    // 自動關閉
    if (duration > 0) {
      setTimeout(() => this.hide(toast), duration);
    }

    return toast;
  }

  hide(toast) {
    toast.classList.remove('toast-enter');
    toast.classList.add('toast-exit');
    setTimeout(() => toast.remove(), 500);
  }

  success(message, duration = 5000) {
    return this.show(message, 'success', duration);
  }

  error(message, duration = 6000) {
    return this.show(message, 'error', duration);
  }

  warning(message, duration = 5500) {
    return this.show(message, 'warning', duration);
  }

  info(message, duration = 5000) {
    return this.show(message, 'info', duration);
  }
}

// 創建全局實例
export const toast = new Toast();
