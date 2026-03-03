/**
 * TodoList 应用集成测试
 * 测试待办事项列表的所有核心功能
 */

// DOM 将由 Jest 的 jsdom 环境提供
const { screen, fireEvent } = require('@testing-library/dom');

describe('待办事项列表测试', () => {
  let container;
  let input;
  let button;
  let list;
  let errorMessage;

  beforeEach(() => {
    // 清空之前的 DOM
    document.body.innerHTML = '';

    // 创建测试用的HTML结构
    container = document.createElement('div');
    container.innerHTML = `
      <div class="container" id="container">
        <h1 id="title">待办事项列表</h1>
        <div class="container-content">
          <div class="content" id="input-content">
            <input type="text" id="input" placeholder="请输入新增内容" autocomplete="off">
            <button id="submit">新增</button>
          </div>
          <div class="control-group">
            <label><input type="checkbox" value="1" name="checkbox" id="selectAll">全选</label>
            <div class="radio-group" id="radioGroup">
              <label><input type="radio" value="all" name="radio" class="radioAll" checked>全部</label>
              <label><input type="radio" value="select" name="radio" class="radioSelected">已选中</label>
              <label><input type="radio" value="unselect" name="radio" class="radioUnselect">未选中</label>
            </div>
            <button id="deleteSelected">删除已选中</button>
          </div>
          <div>
            <ul class="todolist-checkbox" id="todolist"></ul>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(container);

    // 获取DOM元素
    input = document.getElementById('input');
    button = document.getElementById('submit');
    list = document.getElementById('todolist');
    const contentContainer = document.getElementById('input-content');

    // 创建错误消息元素
    errorMessage = document.createElement('div');
    errorMessage.className = 'error-message';
    errorMessage.style.color = 'red';
    errorMessage.style.padding = '10px';
    contentContainer.parentNode.insertBefore(errorMessage, contentContainer.nextSibling);

    // localStorage的键名
    const STORAGE_KEY = 'todoList';
    const STORAGE_TMP_KEY = 'tempList';
    const STORAGE_UNSELECT_KEY = 'unSelectList';

    const selectAllCheckbox = document.getElementById('selectAll');
    const deleteSelectedButton = document.getElementById('deleteSelected');
    const radioGroup = document.getElementById('radioGroup');

    // 定义函数
    window.loadTodos = function(todolist) {
      if (todolist == undefined) {
        todolist = STORAGE_KEY;
      }
      let todos = JSON.parse(localStorage.getItem(todolist)) || [];
      list.innerHTML = '';
      todos.forEach(todo => {
        const todoContainer = document.createElement('div');
        todoContainer.innerHTML = `
          <li data-id="${todo.id}">
            <label><input type="checkbox" class="todo-checkbox" value=${todo.id} name="checkbox" ${todo.completed ? 'checked' : ''}>${todo.text}</label>
            <div class="edit-input">
              <button class="edit-button">编辑</button>
              <button class="delete-button">删除</button>
            </div>
          </li>
        `;
        list.appendChild(todoContainer);
      });

      const allTodosCheckboxes = document.querySelectorAll('input[name="checkbox"]:not([value="1"])');
      allTodosCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
          const allChecked = Array.from(allTodosCheckboxes).every(checkbox => checkbox.checked);
          selectAllCheckbox.checked = allChecked;
        });
      });
    };

    button.addEventListener("click", function() {
      const trimmedInput = input.value.trim();

      if (trimmedInput === '') {
        errorMessage.textContent = '输入内容不能为空';
        return;
      }

      const regex = /^[a-zA-Z0-9_]{1,100}$/;
      if (!regex.test(trimmedInput)) {
        errorMessage.textContent = '输入内容只能包含字母、数字、下划线，且最大长度为 100 个字符';
        return;
      }

      const todos = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
      const isDuplicate = todos.some(todo => todo.text === trimmedInput);
      if (isDuplicate) {
        errorMessage.textContent = '该待办事项已存在';
        return;
      }
      errorMessage.textContent = '';

      const id = Date.now();
      const newTodo = {
        id: id,
        text: input.value,
        completed: false
      };
      todos.push(newTodo);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(todos));
      window.loadTodos();
      input.value = '';
    });

    list.addEventListener("click", function(event) {
      const target = event.target;

      if (target.classList.contains("delete-button")) {
        const todoItem = target.closest('li');
        const checkbox = todoItem.querySelector('input[type="checkbox"]');
        const todoId = parseInt(checkbox.value, 10);
        const todos = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
        const newTodos = todos.filter(todo => todo.id !== todoId);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(newTodos));
        window.loadTodos();
      }

      if (target.classList.contains("edit-button")) {
        const todoItem = target.closest('li');
        const todoText = todoItem.querySelector('label');
        const checkbox = todoText.querySelector('input[type="checkbox"]');

        const inputElement = document.createElement('input');
        inputElement.type = 'text';
        inputElement.value = todoText.textContent;
        inputElement.style.height = '30px';
        inputElement.style.width = '400px';
        inputElement.classList.add('edit-input-field');

        todoText.innerHTML = '';
        todoText.style.display = 'flex';
        todoText.style.alignItems = 'center';
        todoText.appendChild(checkbox);
        todoText.appendChild(inputElement);
        inputElement.focus();

        inputElement.addEventListener('keypress', function(event) {
          if (event.key === 'Enter') {
            const newText = inputElement.value.trim();
            errorMessage.textContent = '';
            const todos = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
            const updatedTodos = todos.map(todo => {
              if (todo.id === parseInt(checkbox.value, 10)) {
                todo.text = newText;
              }
              return todo;
            });
            localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedTodos));
            window.loadTodos();
          }
        });
      }

      if (target.classList.contains('todo-checkbox')) {
        const todos = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
        if (target.checked) {
          todos.forEach(todo => {
            if (target.value == todo.id) {
              todo.completed = true;
            }
          });
        } else {
          todos.forEach(todo => {
            if (target.value == todo.id) {
              todo.completed = false;
            }
          });
        }
        localStorage.setItem(STORAGE_KEY, JSON.stringify(todos));
      }
    });

    selectAllCheckbox.addEventListener('change', function() {
      const isChecked = selectAllCheckbox.checked;
      const allTodosCheckboxes = document.querySelectorAll('input[name="checkbox"]:not([value="1"])');
      allTodosCheckboxes.forEach(checkbox => {
        checkbox.checked = isChecked;
      });
      const todos = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
      const updatedTodos = todos.map(todo => {
        todo.completed = isChecked;
        return todo;
      });
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedTodos));
    });

    deleteSelectedButton.addEventListener('click', function() {
      let todos = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
      todos = todos.filter((todo) => {
        const checkbox = document.querySelector(`input[name="checkbox"].todo-checkbox[value="${todo.id}"]`);
        return !checkbox || !checkbox.checked;
      });
      localStorage.setItem(STORAGE_KEY, JSON.stringify(todos));
      window.loadTodos();
    });

    radioGroup.addEventListener('click', function() {
      const radioSelected = document.querySelector('input[name="radio"].radioSelected');
      const radioSelectedAll = document.querySelector('input[name="radio"].radioAll');
      const radioUnselected = document.querySelector('input[name="radio"].radioUnselect');

      if (radioSelected.checked) {
        let todos = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
        let todosSelected = todos.filter((todo) => todo.completed);
        localStorage.setItem(STORAGE_TMP_KEY, JSON.stringify(todosSelected));
        window.loadTodos(STORAGE_TMP_KEY);
      }

      if (radioSelectedAll.checked) {
        window.loadTodos();
      }

      if (radioUnselected.checked) {
        let todos = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
        let todosUnselected = todos.filter((todo) => !todo.completed);
        localStorage.setItem(STORAGE_UNSELECT_KEY, JSON.stringify(todosUnselected));
        window.loadTodos(STORAGE_UNSELECT_KEY);
      }
    });
  });

  afterEach(() => {
    // 清理
    document.body.innerHTML = '';
  });

  describe('新增待办事项', () => {
    test('应该成功添加新的待办事项', () => {
      input.value = 'Task1';
      button.click();

      const listItems = list.querySelectorAll('li');
      expect(listItems.length).toBe(1);
      expect(listItems[0].textContent).toContain('Task1');
    });

    test('不应该添加空内容', () => {
      input.value = '';
      button.click();

      expect(errorMessage.textContent).toBe('输入内容不能为空');

      const listItems = list.querySelectorAll('li');
      expect(listItems.length).toBe(0);
    });

    test('不应该添加不符合格式的内容', () => {
      input.value = 'Task@#$';
      button.click();

      expect(errorMessage.textContent).toBe('输入内容只能包含字母、数字、下划线，且最大长度为 100 个字符');
    });

    test('不应该添加重复的待办事项', () => {
      input.value = 'Task1';
      button.click();

      input.value = 'Task1';
      button.click();

      const listItems = list.querySelectorAll('li');
      expect(listItems.length).toBe(1);
      expect(errorMessage.textContent).toBe('该待办事项已存在');
    });

    test('成功添加后应该清空输入框', () => {
      input.value = 'Task1';
      button.click();

      expect(input.value).toBe('');
    });
  });

  describe('删除待办事项', () => {
    beforeEach(() => {
      input.value = 'Task1';
      button.click();
      input.value = 'Task2';
      button.click();
    });

    test('应该能够删除单个待办事项', () => {
      const deleteButton = list.querySelector('.delete-button');
      deleteButton.click();

      const listItems = list.querySelectorAll('li');
      expect(listItems.length).toBe(1);
    });

    test('应该能够删除多个选中的待办事项', () => {
      const checkboxes = list.querySelectorAll('.todo-checkbox');
      checkboxes.forEach(cb => cb.checked = true);

      const deleteSelectedButton = document.getElementById('deleteSelected');
      deleteSelectedButton.click();

      const listItems = list.querySelectorAll('li');
      expect(listItems.length).toBe(0);
    });

    test('不应该删除未选中的待办事项', () => {
      const checkboxes = list.querySelectorAll('.todo-checkbox');
      checkboxes[0].checked = true;

      const deleteSelectedButton = document.getElementById('deleteSelected');
      deleteSelectedButton.click();

      const listItems = list.querySelectorAll('li');
      expect(listItems.length).toBe(1);
    });
  });

  describe('编辑待办事项', () => {
    beforeEach(() => {
      input.value = 'Task1';
      button.click();
    });

    test('应该能够编辑待办事项内容', () => {
      const editButton = list.querySelector('.edit-button');
      editButton.click();

      const editInput = list.querySelector('.edit-input-field');
      expect(editInput).not.toBeNull();

      editInput.value = 'UpdatedTask1';
      editInput.dispatchEvent(new KeyboardEvent('keypress', { key: 'Enter' }));

      const listItems = list.querySelectorAll('li');
      expect(listItems[0].textContent).toContain('UpdatedTask1');
    });
  });

  describe('复选框功能', () => {
    beforeEach(() => {
      input.value = 'Task1';
      button.click();
      input.value = 'Task2';
      button.click();
    });

    test('应该能够选中单个待办事项', () => {
      const checkbox = list.querySelector('.todo-checkbox');
      checkbox.click();

      expect(checkbox.checked).toBe(true);
      const todos = JSON.parse(localStorage.getItem('todoList'));
      expect(todos[0].completed).toBe(true);
    });

    test('应该能够取消选中的待办事项', () => {
      const checkbox = list.querySelector('.todo-checkbox');
      checkbox.click();
      checkbox.click();

      expect(checkbox.checked).toBe(false);
      const todos = JSON.parse(localStorage.getItem('todoList'));
      expect(todos[0].completed).toBe(false);
    });

    test('全选应该选中所有待办事项', () => {
      const selectAllCheckbox = document.getElementById('selectAll');
      selectAllCheckbox.click();

      const checkboxes = list.querySelectorAll('.todo-checkbox');
      checkboxes.forEach(cb => {
        expect(cb.checked).toBe(true);
      });
    });

    test('全选取消应该取消所有待办事项', () => {
      const selectAllCheckbox = document.getElementById('selectAll');
      selectAllCheckbox.click();
      selectAllCheckbox.click();

      const checkboxes = list.querySelectorAll('.todo-checkbox');
      checkboxes.forEach(cb => {
        expect(cb.checked).toBe(false);
      });
    });
  });

  describe('筛选功能', () => {
    beforeEach(() => {
      input.value = 'Task1';
      button.click();
      input.value = 'Task2';
      button.click();
      input.value = 'Task3';
      button.click();

      // 选中第二个任务
      const checkboxes = list.querySelectorAll('.todo-checkbox');
      if (checkboxes.length > 1) {
        checkboxes[1].click();
      }
    });

    test('应该显示全部待办事项', () => {
      const radioAll = document.querySelector('.radioAll');
      radioAll.click();

      const listItems = list.querySelectorAll('li');
      expect(listItems.length).toBe(3);
    });

    test('应该只显示已选中的待办事项', () => {
      const radioSelected = document.querySelector('.radioSelected');
      radioSelected.click();

      const listItems = list.querySelectorAll('li');
      expect(listItems.length).toBe(1);
    });

    test('应该只显示未选中的待办事项', () => {
      const radioUnselected = document.querySelector('.radioUnselect');
      radioUnselected.click();

      const listItems = list.querySelectorAll('li');
      expect(listItems.length).toBe(2);
    });
  });

  describe('localStorage 数据持久化', () => {
    test('应该能够从localStorage加载数据', () => {
      // 设置测试数据
      const testData = [
        { id: 123456, text: 'TestTask1', completed: false },
        { id: 123457, text: 'TestTask2', completed: true }
      ];
      localStorage.setItem('todoList', JSON.stringify(testData));

      window.loadTodos();

      const listItems = list.querySelectorAll('li');
      expect(listItems.length).toBe(2);
      expect(listItems[0].textContent).toContain('TestTask1');
      expect(listItems[1].textContent).toContain('TestTask2');
    });

    test('新增后应该保存到localStorage', () => {
      input.value = 'SavedTask';
      button.click();

      const todos = JSON.parse(localStorage.getItem('todoList'));
      expect(todos.length).toBe(1);
      expect(todos[0].text).toBe('SavedTask');
      expect(todos[0].completed).toBe(false);
    });

    test('删除后应该更新localStorage', () => {
      input.value = 'Task1';
      button.click();

      const deleteButton = list.querySelector('.delete-button');
      deleteButton.click();

      const todos = JSON.parse(localStorage.getItem('todoList'));
      expect(todos.length).toBe(0);
    });
  });

  describe('边界情况', () => {
    test('应该处理超过100个字符的输入', () => {
      input.value = 'a'.repeat(101);
      button.click();

      expect(errorMessage.textContent).toBe('输入内容只能包含字母、数字、下划线，且最大长度为 100 个字符');
    });

    test('应该处理只有下划线的输入', () => {
      input.value = '___';
      button.click();

      const listItems = list.querySelectorAll('li');
      expect(listItems.length).toBe(1);
    });

    test('应该处理只有数字的输入', () => {
      input.value = '12345';
      button.click();

      const listItems = list.querySelectorAll('li');
      expect(listItems.length).toBe(1);
    });

    test('应该处理只有字母的输入', () => {
      input.value = 'HelloWorld';
      button.click();

      const listItems = list.querySelectorAll('li');
      expect(listItems.length).toBe(1);
    });

    test('应该处理混合输入', () => {
      input.value = 'Task_123_ABC';
      button.click();

      const listItems = list.querySelectorAll('li');
      expect(listItems.length).toBe(1);
    });

    test('应该处理中文输入（应该被拒绝）', () => {
      input.value = '中文任务';
      button.click();

      expect(errorMessage.textContent).toBe('输入内容只能包含字母、数字、下划线，且最大长度为 100 个字符');
    });

    test('应该处理特殊字符输入（应该被拒绝）', () => {
      input.value = 'Task@#';
      button.click();

      expect(errorMessage.textContent).toBe('输入内容只能包含字母、数字、下划线，且最大长度为 100 个字符');
    });

    test('应该处理空格输入（应该被拒绝）', () => {
      input.value = '   ';
      button.click();

      expect(errorMessage.textContent).toBe('输入内容不能为空');
    });
  });
});
