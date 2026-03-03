const open = require('open').default;

(async () => {
  try {
    await open('.idea/test.html', { app: { name: 'chrome' } });
    console.log('Opening in Chrome...');
  } catch (error) {
    console.error('Failed to open in Chrome:', error);
    process.exit(1);
  }
})();