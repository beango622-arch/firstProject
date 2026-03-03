// jest.setup.js

// 添加 Web API 的 polyfill
const { TextDecoder, TextEncoder } = require('util');
global.TextDecoder = TextDecoder;
global.TextEncoder = TextEncoder;
global.ReadableStream = require('stream/web').ReadableStream;
global.WritableStream = require('stream/web').WritableStream;
global.TransformStream = require('stream/web').TransformStream;

// 模拟 localStorage
class LocalStorageMock {
  constructor() {
    this.store = {};
  }

  clear() {
    this.store = {};
  }

  getItem(key) {
    return this.store[key] || null;
  }

  setItem(key, value) {
    this.store[key] = String(value);
  }

  removeItem(key) {
    delete this.store[key];
  }

  get length() {
    return Object.keys(this.store).length;
  }

  key(index) {
    const keys = Object.keys(this.store);
    return keys[index] || null;
  }
}

global.localStorage = new LocalStorageMock();

// 模拟 window.confirm 和 window.alert
global.confirm = jest.fn(() => true);
global.alert = jest.fn();

// 每个测试前清理 localStorage
beforeEach(() => {
  global.localStorage.clear();
});