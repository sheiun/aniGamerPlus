/**
 * 單頁應用主入口 - 整合登入和主應用功能
 */

console.log('app.js loaded!');

import './styles/main.css';
import '@fortawesome/fontawesome-free/css/all.min.css';

import { Tab } from './components/Tab.js';
import { Switch } from './components/Switch.js';
import { toast } from './components/Toast.js';
import { darkMode } from './components/DarkMode.js';
import { configManager } from './utils/config-manager.js';
import { taskMonitor } from './utils/monitor.js';
import { logout, postJSON, postText, fetchText } from './utils/api.js';

// 設定 ID 列表
const SETTING_IDS = [
  'bangumi_dir',
  'temp_dir',
  'classify_bangumi',
  'lock_resolution',
  'segment_download_mode',
  'add_bangumi_name_to_video_filename',
  'add_resolution_to_video_filename',
  'download_resolution',
  'default_download_mode',
  'check_frequency',
  'multi_thread',
  'multi_downloading_segment',
  'customized_video_filename_prefix',
  'customized_video_filename_suffix',
  'ua',
  'use_mobile_api',
  'danmu',
  'disable_guest_mode',
  'use_proxy',
  'proxy_protocol',
  'proxy_ip',
  'proxy_port',
  'proxy_user',
  'proxy_passwd',
  'check_latest_version',
  'read_sn_list_when_checking_update',
  'read_config_when_checking_update',
  'save_logs',
  'quantity_of_logs',
  'max_completed_tasks',
  'download_cd',
  'parse_sn_cd',
  'cookie',
];

// ==================== 視圖管理 ====================

/**
 * 檢查是否已登入（通過後端 API）
 */
async function isLoggedIn() {
  try {
    const response = await fetch('/api/check_auth');
    const data = await response.json();
    return data.authenticated === true;
  } catch (error) {
    console.error('Failed to check auth status:', error);
    return false;
  }
}

/**
 * 顯示登入視圖
 */
function showLoginView() {
  const loginView = document.getElementById('loginView');
  const appView = document.getElementById('appView');

  if (loginView && appView) {
    loginView.classList.remove('hidden');
    appView.classList.add('hidden');
  }
}

/**
 * 顯示主應用視圖
 */
function showAppView() {
  const loginView = document.getElementById('loginView');
  const appView = document.getElementById('appView');

  if (loginView && appView) {
    loginView.classList.add('hidden');
    appView.classList.remove('hidden');
  }
}

// ==================== 登入功能 ====================

/**
 * 初始化登入表單
 */
function initLoginForm() {
  const usernameInput = document.getElementById('username');
  const passwordInput = document.getElementById('password');
  const loginForm = document.getElementById('loginForm');
  const errorMsg = document.getElementById('errorMsg');
  const errorText = document.getElementById('errorText');
  const loginBtn = document.getElementById('loginBtn');
  const btnText = loginBtn?.querySelector('.btn-text');

  // Focus on username field
  usernameInput?.focus();

  // 表單提交
  loginForm?.addEventListener('submit', e => {
    e.preventDefault();
    handleLogin();
  });

  // Clear error on input
  usernameInput?.addEventListener('input', hideError);
  passwordInput?.addEventListener('input', hideError);

  function hideError() {
    errorMsg?.classList.add('hidden');
  }

  async function handleLogin() {
    errorMsg?.classList.add('hidden');

    const username = usernameInput?.value.trim();
    const password = passwordInput?.value;

    if (!username || password === undefined || password === '') {
      errorText.textContent = '請輸入用戶名和密碼';
      errorMsg?.classList.remove('hidden');
      return;
    }

    const originalText = btnText.textContent;
    loginBtn.disabled = true;
    btnText.innerHTML = '<span class="loading-spinner"></span>登入中...';

    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw { status: response.status, data };
      }

      btnText.innerHTML = '<i class="fas fa-check"></i> 登入成功！';

      // 延遲後切換到主應用視圖並初始化
      setTimeout(async () => {
        showAppView();
        await initMainApp();
      }, 500);
    } catch (error) {
      loginBtn.disabled = false;
      btnText.textContent = originalText;

      let errorMessage = '用戶名或密碼錯誤';
      if (error.status === 401) {
        errorMessage = '用戶名或密碼錯誤，請重試';
      } else if (error.data?.detail) {
        errorMessage = error.data.detail;
      } else if (error.status >= 500) {
        errorMessage = '伺服器錯誤，請稍後再試';
      } else if (!error.status) {
        errorMessage = '無法連接到伺服器';
      }

      errorText.textContent = errorMessage;
      errorMsg?.classList.remove('hidden');

      if (passwordInput) {
        passwordInput.value = '';
        passwordInput.focus();
      }
    }
  }
}

// ==================== 主應用功能 ====================

/**
 * 初始化主應用
 */
async function initMainApp() {
  console.log('Initializing main app...');

  // 初始化 Tab
  new Tab(document.getElementById('mainTabs'));

  // 初始化所有開關
  console.log('Initializing switches...');
  Switch.init('[data-switch]');

  // 載入配置
  console.log('Loading settings data...');
  await loadSettings();

  // 載入 sn_list 內容
  await loadSnListContent();

  // 登出功能
  document.getElementById('logoutBtn')?.addEventListener('click', async () => {
    try {
      // 登出前停止任務監控
      taskMonitor.stop();
      await logout();
      // 登出後切換回登入視圖
      showLoginView();
      // 清空密碼欄位
      const passwordInput = document.getElementById('password');
      if (passwordInput) passwordInput.value = '';
    } catch (error) {
      console.error('Logout failed:', error);
    }
  });

  // Dark Mode Toggle
  document.getElementById('darkModeToggle')?.addEventListener('click', () => {
    const isDark = darkMode.toggle();
    toast.info(isDark ? '已切換至深色模式' : '已切換至淺色模式', 2000);
  });

  // Tab 切換事件
  document.querySelectorAll('[role="tab"]').forEach(tabElement => {
    tabElement.addEventListener('shown.bs.tab', handleTabChange);
  });

  // 綁定全局函數供 HTML 調用
  window.readSettings = saveSettings;
  window.reloadSetting = loadSettings;
  window.getUA = getCurrentUA;
  window.readManualConfig = submitManualTask;
  window.saveSnList = saveSnList;
}

/**
 * 載入設定到表單
 */
async function loadSettings() {
  try {
    await configManager.load();
    renderSettings();
  } catch (error) {
    console.error('Failed to load settings:', error);
    toast.error('載入配置失敗');
  }
}

/**
 * 渲染設定到表單
 */
function renderSettings() {
  for (const id of SETTING_IDS) {
    if (id === 'proxy') continue;

    const element = document.getElementById(id);
    if (!element) continue;

    const value = configManager.get(id);
    const tagName = element.tagName.toLowerCase();

    if (tagName === 'textarea') {
      element.value = value || '';
    } else {
      switch (element.type) {
        case 'text':
        case 'number':
        case 'password':
          element.value = value ?? '';
          if (id === 'multi_thread') {
            const manualThread = document.getElementById('manual_thread_limit');
            if (manualThread) manualThread.value = value;
          }
          break;

        case 'checkbox': {
          const switchInstance = new Switch(element);
          switchInstance.setState(value);
          break;
        }

        case 'select-one':
          if (id === 'proxy_protocol') {
            element.value = (value || '').toUpperCase();
          } else if (id === 'download_resolution') {
            element.value = `${value}P`;
          } else {
            element.value = value;
          }
          break;
      }
    }
  }
}

/**
 * 保存設定
 */
async function saveSettings() {
  try {
    // 讀取表單值
    for (const id of SETTING_IDS) {
      if (id === 'proxy') continue;

      const element = document.getElementById(id);
      if (!element) continue;

      const tagName = element.tagName.toLowerCase();
      let value;

      if (tagName === 'textarea') {
        value = element.value;
      } else {
        switch (element.type) {
          case 'number':
            value = Number(element.value);
            break;
          case 'text':
          case 'password':
            value = element.value;
            break;
          case 'checkbox': {
            const switchInstance = new Switch(element);
            value = switchInstance.getState();
            break;
          }
          case 'select-one':
            if (id === 'proxy_protocol') {
              value = element.value.toLowerCase();
            } else if (id === 'download_resolution') {
              value = element.value.replace('P', '');
            } else {
              value = element.value;
            }
            break;
        }
      }

      configManager.updateField(id, value);
    }

    // 保存
    await configManager.save();
    toast.success('設定保存成功！');
  } catch (error) {
    console.error('Failed to save settings:', error);
    toast.error('設定保存失敗，請重試');
  }
}

/**
 * 獲取當前 UA
 */
function getCurrentUA() {
  const uaElement = document.getElementById('ua');
  if (uaElement) {
    uaElement.value = navigator.userAgent;
    toast.success('已取得當前瀏覽器 UA');
  }
}

/**
 * 提交手動任務
 */
async function submitManualTask() {
  const linkElement = document.getElementById('manual_link');
  const link = linkElement?.value || '';

  if (!link.length) {
    toast.warning('請輸入影片鏈接！');
    return;
  }

  const sn = link.replace(/(https:\/\/)?ani\.gamer\.com\.tw\/animeVideo\.php\?sn=/i, '');

  const manualData = {
    sn,
    mode: document.getElementById('manual_mode')?.value || 'single',
    resolution: (document.getElementById('manual_resolution')?.value || 'auto').replace('P', ''),
    classify: new Switch(document.getElementById('manual_classify')).getState(),
    thread: document.getElementById('manual_thread_limit')?.value || 1,
    danmu: new Switch(document.getElementById('manual_danmu')).getState(),
  };

  try {
    await postJSON('/manualTask', manualData);
    if (linkElement) linkElement.value = '';
    toast.success('下載任務已提交！');
  } catch (error) {
    console.error('Failed to submit manual task:', error);
    toast.error('任務提交失敗，請重試');
  }
}

/**
 * 保存 sn_list
 */
async function saveSnList() {
  const textarea = document.getElementById('sn_list_textarea');
  if (!textarea) {
    toast.error('找不到文本框，請重新載入頁面');
    return;
  }

  const button = event?.target.closest('button');
  if (button) {
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>保存中...';
  }

  try {
    await postText('/api/sn_list', textarea.value);
    toast.success('訂閱清單保存成功！');
  } catch (error) {
    console.error('Failed to save sn_list:', error);
    toast.error('訂閱清單保存失敗，請重試');
  } finally {
    if (button) {
      button.disabled = false;
      button.innerHTML = '<i class="fas fa-save mr-2"></i>保存';
    }
  }
}

/**
 * 處理 Tab 切換
 */
function handleTabChange(e) {
  const targetId = e.detail.targetId;
  const targetPanel = document.getElementById(targetId);

  if (targetPanel) {
    targetPanel.classList.add('animate-fadeIn');
    setTimeout(() => targetPanel.classList.remove('animate-fadeIn'), 400);
  }

  if (targetId === 'monitor') {
    taskMonitor.start();
  }
  // 不再停止 taskMonitor，讓它在背景持續運行

  if (targetId === 'manual') {
    setTimeout(() => Switch.init('[data-switch]'), 100);
  }
}

/**
 * 載入 sn_list 內容
 */
async function loadSnListContent() {
  try {
    const content = await fetchText('/data/sn_list');
    const textarea = document.getElementById('sn_list_textarea');
    if (textarea) {
      textarea.value = content;
    }
  } catch (error) {
    console.error('Failed to load sn_list content:', error);
  }
}

// ==================== 應用初始化 ====================

/**
 * 主初始化函數
 */
async function initApp() {
  console.log('Initializing SPA...');

  // 初始化登入表單
  initLoginForm();

  // 根據登入狀態顯示對應視圖
  const loggedIn = await isLoggedIn();
  if (loggedIn) {
    console.log('User is logged in, showing app view');
    showAppView();
    await initMainApp();
  } else {
    console.log('User is not logged in, showing login view');
    showLoginView();
  }
}

// 初始化應用
console.log('Setting up app initialization, readyState:', document.readyState);
if (document.readyState === 'loading') {
  console.log('DOM still loading, waiting for DOMContentLoaded');
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  console.log('DOM ready, initializing immediately');
  initApp();
}
