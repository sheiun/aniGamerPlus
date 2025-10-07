/**
 * 任務監控模組 - 替代 monitor.js (移除 Layui 依賴)
 */

import { ProgressBar } from '../components/ProgressBar.js';
import { fetchText } from './api.js';

export class TaskMonitor {
  constructor() {
    this.ws = null;
    this.active = false;
    this.progressBars = new Map();
    // 追蹤當前顯示的任務 SN
    this.currentActiveTasks = new Set();
    this.currentPendingTasks = new Set();
    this.currentCompletedTasks = new Set();
  }

  async start() {
    if (this.active) return;

    try {
      // 獲取 WebSocket token
      const token = await fetchText('/data/get_token');
      const protocol = window.location.protocol.replace('http', 'ws');
      const wsUrl = `${protocol}//${window.location.host}/data/tasks_progress?token=${token}`;

      this.ws = new WebSocket(wsUrl);
      this.active = true;

      this.ws.onmessage = evt => this.handleMessage(evt);
      this.ws.onclose = () => {
        this.active = false;
      };
      this.ws.onerror = error => {
        console.error('WebSocket error:', error);
        this.active = false;
      };
    } catch (error) {
      console.error('Failed to start monitoring:', error);
    }
  }

  handleMessage(evt) {
    try {
      const data = JSON.parse(evt.data);
      const noTaskEl = document.getElementById('no_task');
      const panel = document.getElementById('task_info_panel');

      // 檢查是否有任務（執行中、等待中或已完成）
      const hasActiveTasks = data.active && Object.keys(data.active).length > 0;
      const hasPendingTasks = data.pending && Object.keys(data.pending).length > 0;
      const hasCompletedTasks = data.completed && Object.keys(data.completed).length > 0;
      const hasAnyTasks = hasActiveTasks || hasPendingTasks || hasCompletedTasks;

      // 更新統計資訊
      this.updateStats(data.stats || {
        active_count: hasActiveTasks ? Object.keys(data.active).length : 0,
        pending_count: hasPendingTasks ? Object.keys(data.pending).length : 0,
        completed_count: hasCompletedTasks ? Object.keys(data.completed).length : 0
      });

      if (!hasAnyTasks) {
        if (noTaskEl) noTaskEl.classList.remove('hidden');
        // 清空時使用淡出動畫
        this.clearAllTasks(panel);
      } else {
        if (noTaskEl) noTaskEl.classList.add('hidden');

        // 使用增量更新而非全部重建（順序：執行中 → 等待中 → 已完成）
        this.updateActiveTasks(data.active || {}, panel);
        this.updatePendingTasks(data.pending || {}, panel);
        this.updateCompletedTasks(data.completed || {}, panel);
      }
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e);
    }
  }

  updateStats(stats) {
    const activeCountEl = document.getElementById('active_count');
    const pendingCountEl = document.getElementById('pending_count');
    const totalCountEl = document.getElementById('total_count');
    const completedCountEl = document.getElementById('completed_count');

    if (activeCountEl) activeCountEl.textContent = stats.active_count || 0;
    if (pendingCountEl) pendingCountEl.textContent = stats.pending_count || 0;
    if (completedCountEl) completedCountEl.textContent = stats.completed_count || 0;
    if (totalCountEl) {
      // 總計 = 執行中 + 等待中 + 已完成
      const total = (stats.active_count || 0) + (stats.pending_count || 0) + (stats.completed_count || 0);
      totalCountEl.textContent = total;
    }
  }

  createActiveTask(sn, taskData, panel, insertBefore = null) {
    if (!panel) return;

    const taskCard = document.createElement('div');
    taskCard.id = `active-${sn}`;
    taskCard.className = 'pixel-card bg-white dark:bg-gray-800 p-6 mb-4 animate-fadeIn border-l-4 border-green-500';
    taskCard.innerHTML = `
      <div class="flex items-center justify-between gap-2 mb-2">
        <div class="flex items-center gap-2">
          <span class="inline-block w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
          <span class="text-xs font-semibold text-green-600 dark:text-green-400 uppercase">執行中</span>
        </div>
        <span class="text-xs font-mono bg-gray-100 dark:bg-gray-700 px-3 py-1 rounded-full text-gray-600 dark:text-gray-300">
          SN: ${sn}
        </span>
      </div>
      <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-3 break-all">
        ${taskData.filename}
      </h3>
      <div class="flex items-center gap-4">
        <div class="flex-shrink-0 text-center">
          <span class="inline-block px-4 py-2 bg-primary/10 text-primary dark:bg-primary/20 dark:text-primary-300 rounded-lg font-medium status-text">
            ${taskData.status}
          </span>
        </div>
        <div class="flex-1" id="progress${sn}"></div>
      </div>
    `;

    // 插入到正確位置：執行中任務在前，等待中任務在後
    if (insertBefore) {
      panel.insertBefore(taskCard, insertBefore);
    } else {
      panel.appendChild(taskCard);
    }

    // 創建進度條
    const progressBar = ProgressBar.create(`progress${sn}`, Math.round(taskData.rate));
    this.progressBars.set(sn, progressBar);
  }

  createPendingTask(sn, taskData, panel, insertBefore = null) {
    if (!panel) return;

    const taskCard = document.createElement('div');
    taskCard.id = `pending-${sn}`;
    taskCard.className = 'pixel-card bg-gray-50 dark:bg-gray-700 p-6 mb-4 animate-fadeIn border-l-4 border-yellow-500';
    taskCard.innerHTML = `
      <div class="flex items-center justify-between gap-2 mb-2">
        <div class="flex items-center gap-2">
          <span class="inline-block w-3 h-3 bg-yellow-500 rounded-full"></span>
          <span class="text-xs font-semibold text-yellow-600 dark:text-yellow-400 uppercase">等待中</span>
        </div>
        <span class="text-xs font-mono bg-gray-100 dark:bg-gray-600 px-3 py-1 rounded-full text-gray-600 dark:text-gray-300">
          SN: ${sn}
        </span>
      </div>
      <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-3 break-all">
        ${taskData.filename}
      </h3>
      <div class="flex flex-wrap items-center gap-4">
        <div class="flex items-center gap-2 text-gray-600 dark:text-gray-300">
          <i class="fas fa-list-ol"></i>
          <span>佇列位置: <span class="font-semibold text-primary">#${taskData.position}</span></span>
        </div>
        <div class="flex items-center gap-2 text-gray-600 dark:text-gray-300">
          <i class="fas fa-info-circle"></i>
          <span>模式: <span class="font-semibold">${this.formatMode(taskData.mode)}</span></span>
        </div>
      </div>
    `;

    // 插入到正確位置：等待中任務在執行中任務後，已完成任務前
    if (insertBefore) {
      panel.insertBefore(taskCard, insertBefore);
    } else {
      panel.appendChild(taskCard);
    }
  }

  /**
   * 增量更新執行中的任務
   */
  updateActiveTasks(activeTasks, panel) {
    if (!panel) return;

    const newActiveSNs = new Set(Object.keys(activeTasks));

    // 1. 移除已完成的任務（不在新資料中的任務）
    for (const sn of this.currentActiveTasks) {
      if (!newActiveSNs.has(sn)) {
        this.removeTaskWithAnimation(`active-${sn}`);
        this.currentActiveTasks.delete(sn);
        this.progressBars.delete(sn);
      }
    }

    // 2. 更新或新增任務
    // 反轉遍歷順序後依次追加，這樣新的會在最上面，舊的在最下面
    const activeEntries = Object.entries(activeTasks).reverse();
    for (const [sn, taskData] of activeEntries) {
      const taskCard = document.getElementById(`active-${sn}`);

      if (taskCard) {
        // 任務已存在，只更新進度和狀態
        this.updateActiveTaskContent(sn, taskData, taskCard);
      } else {
        // 新任務，插入到等待中/已完成任務之前（執行中區域的末尾）
        const firstNonActive = panel.querySelector('[id^="pending-"],[id^="completed-"]');
        this.createActiveTask(sn, taskData, panel, firstNonActive);
        this.currentActiveTasks.add(sn);
      }
    }
  }

  /**
   * 增量更新等待中的任務
   */
  updatePendingTasks(pendingTasks, panel) {
    if (!panel) return;

    const newPendingSNs = new Set(Object.keys(pendingTasks));

    // 1. 移除不再等待的任務（開始執行或被取消）
    for (const sn of this.currentPendingTasks) {
      if (!newPendingSNs.has(sn)) {
        this.removeTaskWithAnimation(`pending-${sn}`);
        this.currentPendingTasks.delete(sn);
      }
    }

    // 2. 更新或新增任務
    // 等待中任務按佇列位置順序顯示（#1 在最上面，#N 在最下面）
    // 按 position 排序（從小到大）
    const pendingEntries = Object.entries(pendingTasks).sort((a, b) => {
      return (a[1].position || 0) - (b[1].position || 0);
    });
    
    for (const [sn, taskData] of pendingEntries) {
      const taskCard = document.getElementById(`pending-${sn}`);

      if (taskCard) {
        // 任務已存在，更新位置和資訊
        this.updatePendingTaskContent(sn, taskData, taskCard);
      } else {
        // 新任務，插入到已完成任務之前（等待中區域的末尾）
        const firstCompleted = panel.querySelector('[id^="completed-"]');
        this.createPendingTask(sn, taskData, panel, firstCompleted);
        this.currentPendingTasks.add(sn);
      }
    }
  }

  /**
   * 更新執行中任務的內容（進度條、狀態）
   */
  updateActiveTaskContent(sn, taskData, taskCard) {
    // 更新狀態文字
    const statusEl = taskCard.querySelector('.status-text');
    if (statusEl && statusEl.textContent !== taskData.status) {
      statusEl.textContent = taskData.status;
    }

    // 更新進度條（只在進度變化時更新）
    const progressBar = this.progressBars.get(sn);
    if (progressBar) {
      const newRate = Math.round(taskData.rate);
      if (progressBar.percent !== newRate) {
        progressBar.setPercent(newRate);
      }
    }
  }

  /**
   * 更新等待中任務的內容（佇列位置）
   */
  updatePendingTaskContent(sn, taskData, taskCard) {
    // 更新佇列位置
    const positionEl = taskCard.querySelector('.font-semibold.text-primary');
    if (positionEl) {
      positionEl.textContent = `#${taskData.position}`;
    }
  }

  /**
   * 增量更新已完成的任務
   */
  updateCompletedTasks(completedTasks, panel) {
    if (!panel) return;

    const newCompletedSNs = new Set(Object.keys(completedTasks));

    // 1. 移除不再存在的已完成任務（被清理的舊任務）
    for (const sn of this.currentCompletedTasks) {
      if (!newCompletedSNs.has(sn)) {
        this.removeTaskWithAnimation(`completed-${sn}`);
        this.currentCompletedTasks.delete(sn);
      }
    }

    // 2. 添加新完成的任務
    // 反轉遍歷順序後依次追加，這樣新的會在最上面，舊的在最下面
    const completedEntries = Object.entries(completedTasks).reverse();
    for (const [sn, taskData] of completedEntries) {
      if (!this.currentCompletedTasks.has(sn)) {
        // 新完成的任務，追加到 panel 末尾（已完成區域）
        this.createCompletedTask(sn, taskData, panel);
        this.currentCompletedTasks.add(sn);
      }
    }
  }

  createCompletedTask(sn, taskData, panel) {
    if (!panel) return;

    const isSuccess = taskData.status === 'success';
    const borderColor = isSuccess ? 'border-blue-500' : 'border-red-500';
    const bgColor = isSuccess ? 'bg-blue-50 dark:bg-blue-900/20' : 'bg-red-50 dark:bg-red-900/20';
    const iconColor = isSuccess ? 'bg-blue-500' : 'bg-red-500';
    const textColor = isSuccess ? 'text-blue-600 dark:text-blue-400' : 'text-red-600 dark:text-red-400';
    const icon = isSuccess ? 'fa-check-circle' : 'fa-times-circle';
    const statusText = isSuccess ? '已完成' : '失敗';

    const taskCard = document.createElement('div');
    taskCard.id = `completed-${sn}`;
    taskCard.className = `pixel-card ${bgColor} p-6 mb-4 animate-fadeIn border-l-4 ${borderColor}`;
    taskCard.innerHTML = `
      <div class="flex items-center justify-between gap-2 mb-2">
        <div class="flex items-center gap-2">
          <span class="inline-block w-3 h-3 ${iconColor} rounded-full"></span>
          <span class="text-xs font-semibold ${textColor} uppercase">${statusText}</span>
        </div>
        <span class="text-xs font-mono bg-gray-100 dark:bg-gray-700 px-3 py-1 rounded-full text-gray-600 dark:text-gray-300">
          SN: ${sn}
        </span>
      </div>
      <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-2 break-all">
        ${taskData.filename}
      </h3>
      <div class="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
        <div class="flex items-center gap-1">
          <i class="fas ${icon}"></i>
          <span>${taskData.completion_time}</span>
        </div>
      </div>
    `;

    // 直接追加到 panel 末尾
    panel.appendChild(taskCard);
  }

  /**
   * 帶淡出動畫移除任務卡片
   */
  removeTaskWithAnimation(taskId) {
    const taskCard = document.getElementById(taskId);
    if (taskCard) {
      taskCard.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
      taskCard.style.opacity = '0';
      taskCard.style.transform = 'translateX(20px)';
      setTimeout(() => {
        taskCard.remove();
      }, 300);
    }
  }

  /**
   * 清空所有任務
   */
  clearAllTasks(panel) {
    if (!panel) return;

    // 為所有現有任務添加淡出動畫
    const allTasks = panel.querySelectorAll('[id^="active-"], [id^="pending-"], [id^="completed-"]');
    allTasks.forEach(task => {
      task.style.transition = 'opacity 0.3s ease-out';
      task.style.opacity = '0';
    });

    setTimeout(() => {
      if (panel) panel.innerHTML = '';
      this.progressBars.clear();
      this.currentActiveTasks.clear();
      this.currentPendingTasks.clear();
      this.currentCompletedTasks.clear();
    }, 300);
  }

  formatMode(mode) {
    const modeMap = {
      'single': '單集',
      'latest': '最新一集',
      'all': '全部',
      'largest-sn': '最大 SN',
      'unknown': '未知'
    };
    return modeMap[mode] || mode;
  }

  stop() {
    if (this.ws && this.active) {
      this.ws.close();
      this.ws = null;
      this.active = false;
      this.progressBars.clear();
    }
  }
}

// 創建全局實例
export const taskMonitor = new TaskMonitor();
