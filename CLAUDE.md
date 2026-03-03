# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Todo List web application built with vanilla HTML/CSS/JavaScript. The application features:
- Add, edit, delete todo items
- Check/uncheck individual items
- Select all/unselect all functionality
- Filter items by: all, selected, unselected
- Data persistence using localStorage
- Input validation with regex pattern: `/^[a-zA-Z0-9_]{1,100}$/`

## Project Structure

```
todoList/
├── .idea/                    # Primary source code (unconventional location)
│   ├── test.html           # Main HTML structure
│   ├── test.js            # Core application logic (~350 lines)
│   └── test.css           # Styling
├── tests/                  # Test suite
│   ├── index.test.js      # Main functional tests (27 tests)
│   └── integration.test.js # Source code validation tests (9 tests)
├── jest.config.js         # Jest configuration for jsdom environment
├── jest.setup.js          # Test environment setup (localStorage mocking)
├── babel.config.js        # Babel configuration for Jest
├── package.json           # npm scripts and dependencies
└── TEST_REPORT.md         # Detailed test report
```

**Important**: The source code lives in `.idea/` directory, not a conventional `src/` folder.

## Development Commands

### Running the Application
```bash
npm start                  # Open application in Chrome
```

### Testing
```bash
npm test                   # Run all tests (36 total)
npm run test:watch         # Run tests in watch mode
npm run test:coverage      # Run tests with coverage report
npm test -- tests/index.test.js      # Run specific test file
```

### Test Configuration
- **Environment**: jsdom (browser-like environment)
- **Mocking**: localStorage, confirm(), alert()
- **Test location**: All tests in `tests/**/*.test.js`
- **Setup**: `jest.setup.js` provides polyfills and mocks

## Code Architecture

### Core Functions
The application logic in `.idea/test.js` centers around these key functions:

1. **`getTodos(key = STORAGE_KEY)`** - Retrieves todos from localStorage
2. **`saveTodos(todos, key = STORAGE_KEY)`** - Saves todos to localStorage
3. **`loadTodos(todolist)`** - Renders todos to the DOM
4. **`deleteSelectedTodos()`** - Deletes all checked items
5. **`radioGroupSelected()`** - Handles filter radio button clicks

### Design Patterns
- **Event Delegation**: Uses `list.addEventListener("click", ...)` with class checks (`target.classList.contains()`) for dynamic elements (delete, edit, checkbox)
- **Data Flow Pattern**: All operations follow `getTodos() → modify → saveTodos() → loadTodos()` pattern
- **Filter Implementation**: Uses temporary storage keys (`tempList`, `unSelectList`) for filtered views, not in-memory filtering

### Data Flow
1. **Initialization**: `DOMContentLoaded` → `loadTodos()`
2. **Add Todo**: Input validation → `getTodos()` → Check duplicates → `saveTodos()` → `loadTodos()`
3. **Edit Todo**: Click edit → Replace label with input → Validate on Enter → `getTodos()` → Update → `saveTodos()` → `loadTodos()`
4. **Delete Todo**: Confirm dialog → `getTodos()` → Filter → `saveTodos()` → `loadTodos()`
5. **Check/Uncheck**: Update `completed` property → `saveTodos()`
6. **Filter**: Radio button click → Filter todos → Save to temp key → `loadTodos(tempKey)`

### Validation Rules
- **Empty input**: Shows "输入内容不能为空" (Chinese: "Input cannot be empty")
- **Format validation**: Must match `/^[a-zA-Z0-9_]{1,100}$/` (alphanumeric + underscore, 1-100 chars)
- **Duplicate prevention**: Checks for existing todo with same text, shows "该待办事项已存在" ("Todo already exists")
- **Edit validation**: Same rules as add, but excludes current item from duplicate check

**Note**: All validation error messages are in Chinese. The regex pattern is defined in `.idea/test.js` (search for `/^[a-zA-Z0-9_]{1,100}$/`).

### Storage Keys
Defined in `.idea/test.js:19-21`:
- `STORAGE_KEY = 'todoList'`: Main todos storage
- `STORAGE_TMP_KEY = 'tempList'`: Temporary storage for "selected" filter
- `STORAGE_UNSELECT_KEY = 'unSelectList'`: Temporary storage for "unselected" filter

### DOM Element IDs and Selectors (test.html)
- `input`: Text input for new todos
- `submit`: Add button
- `todolist`: UL element for todo items
- `deleteSelected`: Delete selected items button
- `radioGroup`: Container for filter radio buttons

**Important selectors without IDs:**
- "Select all" checkbox: `input[name="checkbox"][value="1"]` (no ID in source, tests add `id="selectAll"`)
- Filter radio buttons: `.radioAll`, `.radioSelected`, `.radioUnselect` (note: `radioUnselect` not `radioUnselected`)

## Testing Patterns

### Functional Tests (`tests/index.test.js`)
**Important**: Tests cannot import the vanilla JavaScript source as modules. Instead, they:
1. Create a clean DOM with the application structure
2. Attach the same event listeners found in `.idea/test.js`
3. Simulate user actions (clicks, typing)
4. Assert DOM changes and localStorage updates

Each test recreates the DOM and attaches handlers to isolate test state.

### Integration Tests (`tests/integration.test.js`)
Validates that source files exist and contain expected patterns.

### Test Environment
- Uses Jest's jsdom environment with custom polyfills in `jest.setup.js`
- Mocks `localStorage` with `LocalStorageMock` class
- Mocks `confirm()` and `alert()` functions
- Clears localStorage before each test

### Troubleshooting Common Test Issues
- **Polyfill errors** (TextDecoder, ReadableStream, etc.): Already handled in `jest.setup.js`
- **LocalStorage not working in tests**: Mocked via `LocalStorageMock` class
- **Confirm/alert dialogs**: Mocked to return `true` by default
- **Transform errors**: `transformIgnorePatterns` in `jest.config.js` handles `jsdom` and `@exodus` modules
- **Running specific tests**: Use `npm test -- -t "test name"` to run a test by its description

## Common Development Tasks

### Adding New Features
1. Update `.idea/test.js` with new functionality
2. Add corresponding tests in `tests/` directory
3. Run `npm test` to ensure existing tests still pass
4. Add new test cases for the feature

### Modifying Validation Rules
Update the regex pattern (search for `/^[a-zA-Z0-9_]{1,100}$/` in `.idea/test.js`) and ensure tests reflect the changes. Update both add and edit validation sections.

### Changing Storage Structure
Update `getTodos()` and `saveTodos()` helper functions, then update all callers.

## Notes for Future Development

- The application has no build step - it's pure HTML/CSS/JS
- All business logic is in `.idea/test.js` (~350 lines)
- CSS styles are in `.idea/test.css`, including `.error-message` and `.edit-input-field`
- Tests are comprehensive (36 tests covering all functionality)
- The code has been refactored to use helper functions (`getTodos`, `saveTodos`) to reduce duplication (eliminates 8+ repetitions of `JSON.parse(localStorage.getItem(...))`)
- Console.log statements have been removed from production code (18 instances removed)
- Inline styles moved to CSS classes (`.error-message`, `.edit-input-field`) for better maintainability

- **Browser opening**: Uses `open` package (`npm start`) to open application in Chrome (cross-platform)

When making changes, ensure all 36 tests pass by running `npm test`. The test suite provides 100% functional coverage of the application.