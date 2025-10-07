/**
 * 進度條組件 - 替代 Layui Progress
 */

export class ProgressBar {
  constructor(container) {
    this.container = typeof container === 'string' ? document.getElementById(container) : container;
    this.percent = 0;
    this.render();
  }

  render() {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="progress-bar">
        <div class="progress-fill" style="width: ${this.percent}%"></div>
        <div class="progress-text">${this.percent}%</div>
      </div>
    `;
  }

  setPercent(percent) {
    this.percent = Math.min(Math.max(percent, 0), 100);
    const fill = this.container?.querySelector('.progress-fill');
    const text = this.container?.querySelector('.progress-text');

    if (fill && text) {
      fill.style.width = `${this.percent}%`;
      text.textContent = `${Math.round(this.percent)}%`;
    }
  }

  static create(containerId, initialPercent = 0) {
    const bar = new ProgressBar(containerId);
    bar.setPercent(initialPercent);
    return bar;
  }
}
