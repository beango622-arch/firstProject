/**
 * 针对实际源代码的集成测试
 * 测试 .idea 目录中的实际文件
 */

const fs = require('fs');
const path = require('path');

describe('实际源代码集成测试', () => {
  let jsCode;
  let htmlContent;

  beforeAll(() => {
    // 读取实际源代码文件
    const jsPath = path.join(__dirname, '..', '.idea', 'test.js');
    const htmlPath = path.join(__dirname, '..', '.idea', 'test.html');

    jsCode = fs.readFileSync(jsPath, 'utf8');
    htmlContent = fs.readFileSync(htmlPath, 'utf8');
  });

  test('JavaScript 文件应该存在且可读', () => {
    expect(jsCode).toBeTruthy();
    expect(jsCode.length).toBeGreaterThan(0);
  });

  test('HTML 文件应该存在且可读', () => {
    expect(htmlContent).toBeTruthy();
    expect(htmlContent.length).toBeGreaterThan(0);
  });

  test('JavaScript 代码应该包含关键函数', () => {
    // 检查是否包含关键函数定义
    expect(jsCode).toContain('loadTodos');
    expect(jsCode).toContain('deleteSelectedTodos');
    expect(jsCode).toContain('radioGroupSelected');
  });

  test('JavaScript 代码应该包含事件监听器', () => {
    // 检查是否包含关键事件监听器
    expect(jsCode).toContain('addEventListener');
    expect(jsCode).toContain('DOMContentLoaded');
  });

  test('JavaScript 代码应该包含 localStorage 操作', () => {
    // 检查是否包含 localStorage 操作
    expect(jsCode).toContain('localStorage');
    expect(jsCode).toContain('getItem');
    expect(jsCode).toContain('setItem');
  });

  test('HTML 文件应该包含必要的元素ID', () => {
    // 检查HTML是否包含必要的元素
    expect(htmlContent).toContain('id="input"');
    expect(htmlContent).toContain('id="submit"');
    expect(htmlContent).toContain('id="todolist"');
    expect(htmlContent).toContain('id="deleteSelected"');
  });

  test('HTML 文件应该链接到正确的JavaScript文件', () => {
    // 检查HTML是否链接到test.js
    expect(htmlContent).toContain('<script src="test.js"></script>');
  });

  test('CSS 文件应该存在且可读', () => {
    // 检查CSS文件
    const cssPath = path.join(__dirname, '..', '.idea', 'test.css');
    const cssContent = fs.readFileSync(cssPath, 'utf8');

    expect(cssContent).toBeTruthy();
    expect(cssContent.length).toBeGreaterThan(0);
    expect(cssContent).toContain('.container');
    expect(cssContent).toContain('.todolist-checkbox');
  });

  test('JavaScript 代码应该包含正确的正则表达式模式', () => {
    // 检查输入验证正则表达式是否存在
    expect(jsCode).toContain('/^[a-zA-Z0-9_]{1,100}$/');
  });
});
