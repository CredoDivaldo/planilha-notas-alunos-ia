module.exports = [
  {
    files: ["src/**/*.js", "tests/**/*.js"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "commonjs",
      globals: {
        process: "readonly",
        console: "readonly",
        module: "readonly",
        require: "readonly",
        __dirname: "readonly",
        fetch: "readonly",
        Buffer: "readonly",
      }
    },
    rules: {
      "no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      "no-undef": "error",
    },
  },
  {
    files: ["tests/**/*.js"],
    languageOptions: {
      globals: {
        describe: "readonly",
        it: "readonly",
        expect: "readonly",
        beforeEach: "readonly",
        afterEach: "readonly",
        jest: "readonly",
      },
    },
  },
  {
    // jsdom environment globals for accessibility tests (Story 4.1)
    files: ["tests/accessibility.test.js"],
    languageOptions: {
      globals: {
        document: "readonly",
        window: "readonly",
      },
    },
  },
  {
    // jsdom environment globals for form-validation and polling tests (Stories 4.2, 4.3)
    files: ["tests/form-validation.test.js", "tests/public/polling.test.js"],
    languageOptions: {
      globals: {
        document: "readonly",
        window: "readonly",
        File: "readonly",
        clearInterval: "readonly",
        setInterval: "readonly",
      },
    },
  },
  {
    // jsdom environment globals for confirmation-modal tests (Story 4.6)
    files: ["tests/public/confirmation-modal.test.js"],
    languageOptions: {
      globals: {
        document: "readonly",
        window: "readonly",
        Event: "readonly",
        MouseEvent: "readonly",
        KeyboardEvent: "readonly",
      },
    },
  },
  {
    // jsdom environment globals for state-gating tests (Story 4.7)
    files: ["tests/public/state-gating.test.js"],
    languageOptions: {
      globals: {
        document: "readonly",
        test: "readonly",
      },
    },
  },
];
