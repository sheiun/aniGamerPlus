/**
 * Toggle Switch 組件
 */

export class Switch {
  constructor(inputElement) {
    this.input = typeof inputElement === 'string' ? document.getElementById(inputElement) : inputElement;

    if (this.input && !this.input.classList.contains('switch-initialized')) {
      this.createSwitch();
      this.input.classList.add('switch-initialized');
    }
  }

  createSwitch() {
    // 檢查是否已經被包裝
    if (this.input.parentElement?.classList.contains('switch-wrapper')) {
      return;
    }

    // 創建 switch 容器
    const wrapper = document.createElement('label');
    wrapper.className = 'switch-wrapper';

    const switchTrack = document.createElement('div');
    switchTrack.className = 'switch-track';

    const switchThumb = document.createElement('div');
    switchThumb.className = 'switch-thumb';

    // 設置 input 類
    this.input.classList.add('switch-input');
    this.input.type = 'checkbox';

    // 組裝
    const parent = this.input.parentNode;
    const nextSibling = this.input.nextSibling;

    wrapper.appendChild(this.input);
    wrapper.appendChild(switchTrack);
    switchTrack.appendChild(switchThumb);

    // 插入到原始位置
    if (nextSibling) {
      parent.insertBefore(wrapper, nextSibling);
    } else {
      parent.appendChild(wrapper);
    }
  }

  setState(state) {
    if (this.input) {
      this.input.checked = state;
    }
  }

  getState() {
    return this.input?.checked || false;
  }

  static init(selector) {
    const elements = document.querySelectorAll(selector);
    elements.forEach(el => {
      if (!el.classList.contains('switch-initialized')) {
        new Switch(el);
      }
    });
  }
}
