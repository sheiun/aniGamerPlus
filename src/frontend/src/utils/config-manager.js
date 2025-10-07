/**
 * 配置管理模組
 */

import { fetchJSON, postJSON } from './api.js';

/**
 * 配置管理器
 */
export class ConfigManager {
  constructor() {
    this.config = null;
    this.proxyFields = {
      protocol: '',
      ip: '',
      port: '',
      user: '',
      passwd: '',
    };
  }

  /**
   * 載入配置
   */
  async load() {
    this.config = await fetchJSON('/data/config.json');
    this.parseProxy(this.config.proxy || '');
    return this.config;
  }

  /**
   * 解析代理配置
   */
  parseProxy(proxyString) {
    let proxy = proxyString;

    // 解析協議
    this.proxyFields.protocol = proxy.replace(/:\/\/.*/i, '').toUpperCase();

    // 解析用戶名和密碼
    if (/.*@.*/.test(proxy)) {
      const userMatch = /:\/\/.*?:/g.exec(proxy);
      if (userMatch) {
        this.proxyFields.user = userMatch[0].replace(/:(\/\/)?/g, '');
      }

      const passwdMatch = /:.*@/.exec(proxy);
      if (passwdMatch) {
        this.proxyFields.passwd = passwdMatch[0]
          .replace(this.proxyFields.user, '')
          .replace(/(:\/\/:)?@?/g, '');
      }

      proxy = proxy.replace(`${this.proxyFields.user}:${this.proxyFields.passwd}@`, '');
    } else {
      this.proxyFields.user = '';
      this.proxyFields.passwd = '';
    }

    // 解析 IP 和端口
    if (proxy.length > 0) {
      const ipMatch = /:.*:/.exec(proxy);
      if (ipMatch) {
        this.proxyFields.ip = ipMatch[0].replace(/:(\/\/)?/g, '');
      }

      const portMatch = /:\d+/.exec(proxy);
      if (portMatch) {
        this.proxyFields.port = portMatch[0].replace(/:/, '');
      }
    } else {
      this.proxyFields.ip = '';
      this.proxyFields.port = '';
    }

    // 將代理字段添加到配置中
    this.config.proxy_protocol = this.proxyFields.protocol;
    this.config.proxy_ip = this.proxyFields.ip;
    this.config.proxy_port = this.proxyFields.port;
    this.config.proxy_user = this.proxyFields.user;
    this.config.proxy_passwd = this.proxyFields.passwd;
  }

  /**
   * 構建代理字符串
   */
  buildProxyString() {
    const { protocol, ip, port, user, passwd } = this.proxyFields;
    const ipPort = `${ip}:${port}`;
    const protocolPrefix = `${protocol.toLowerCase()}://`;

    if (!user || !passwd || user.length === 0 || passwd.length === 0) {
      return protocolPrefix + ipPort;
    }

    const userPw = `${user}:${passwd}@`;
    return protocolPrefix + userPw + ipPort;
  }

  /**
   * 更新配置字段
   */
  updateField(fieldName, value) {
    if (fieldName.startsWith('proxy_')) {
      const proxyField = fieldName.replace('proxy_', '');
      this.proxyFields[proxyField] = value;
    } else {
      this.config[fieldName] = value;
    }
  }

  /**
   * 保存配置
   */
  async save() {
    // 構建代理字符串
    this.config.proxy = this.buildProxyString();

    // 上傳配置
    await postJSON('/api/config', this.config);

    // 重新載入
    await this.load();
  }

  /**
   * 獲取配置值
   */
  get(fieldName) {
    if (fieldName.startsWith('proxy_')) {
      const proxyField = fieldName.replace('proxy_', '');
      return this.proxyFields[proxyField];
    }
    return this.config?.[fieldName];
  }
}

// 創建全局實例
export const configManager = new ConfigManager();
