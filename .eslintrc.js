export default {
  env: {
    browser: true,
    es2022: true,
  },
  extends: ['eslint:recommended'],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  rules: {
    'no-unused-vars': 'warn',
    'no-console': 'warn',
    'prefer-const': 'error',
    'no-var': 'error',
    'prefer-template': 'error',
    'quotes': ['error', 'single'],
    'semi': ['error', 'always'],
  },
  globals: {
    // Flask template variables
    'window': 'readonly',
    'document': 'readonly',
    'fetch': 'readonly',
    'navigator': 'readonly',
    'alert': 'readonly',
    'setTimeout': 'readonly',
    'clearTimeout': 'readonly',
  },
};