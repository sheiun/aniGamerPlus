/**
 * Tab 組件
 */

export class Tab {
  constructor(container) {
    this.container = typeof container === 'string' ? document.querySelector(container) : container;

    if (!this.container) {
      console.error('Tab: Container not found');
      return;
    }

    this.init();
  }

  init() {
    const tabButtons = this.container.querySelectorAll('[role="tab"]');

    if (tabButtons.length === 0) {
      console.error('Tab: No tab buttons found');
      return;
    }

    tabButtons.forEach(button => {
      button.addEventListener('click', e => {
        e.preventDefault();
        const targetId = button.getAttribute('href').substring(1);
        this.activateTab(targetId, button);
      });
    });

    // 支持 URL hash 激活
    this.handleHashChange();
    window.addEventListener('hashchange', () => this.handleHashChange());
  }

  handleHashChange() {
    const hash = window.location.hash.substring(1);
    if (hash) {
      const button = this.container.querySelector(`[href="#${hash}"]`);
      if (button) {
        this.activateTab(hash, button);
      }
    }
  }

  activateTab(targetId, clickedButton) {
    const allButtons = this.container.querySelectorAll('[role="tab"]');
    const allPanels = document.querySelectorAll('[role="tabpanel"]');

    // 移除所有激活狀態
    allButtons.forEach(btn => btn.setAttribute('aria-selected', 'false'));
    allPanels.forEach(panel => {
      panel.classList.add('hidden');
      panel.classList.remove('block');
    });

    // 激活目標
    clickedButton.setAttribute('aria-selected', 'true');
    const targetPanel = document.getElementById(targetId);

    if (targetPanel) {
      targetPanel.classList.remove('hidden');
      targetPanel.classList.add('block');

      // 觸發自定義事件
      const event = new CustomEvent('shown.bs.tab', {
        detail: { target: clickedButton, targetId },
      });
      clickedButton.dispatchEvent(event);
    }
  }
}
