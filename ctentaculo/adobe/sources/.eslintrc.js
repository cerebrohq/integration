module.exports = {
  root: true,
  env: {
    node: true,
  },
  extends: ['plugin:vue/essential', '@vue/prettier', '@vue/typescript'],
  rules: {
    'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    'require-atomic-updates': 'off',
    quotes: ['error', 'single'],
    'vue/no-parsing-error': [2, { 'x-invalid-end-tag': false }],
    'prettier/prettier': [
      'error',
      {
        trailingComma: 'all',
        singleQuote: true,
        bracketSpacing: true,
        jsxBracketSameLine: true,
      },
    ],
  },
  parser: 'vue-eslint-parser',
  parserOptions: {
    sourceType: 'module',
    ecmaVersion: 2018,
    ecmaFeatures: {
      globalReturn: false,
      impliedStrict: true,
      jsx: false,
    },
  },
  // root: true,
  // env: {
  //   node: true
  // },
  // extends: [
  //   'plugin:vue/recommended',
  //   'plugin:vue/essential',
  //   '@vue/prettier',
  //   '@vue/typescript'
  // ],
  // rules: {
  //   'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'off',
  //   'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off',
  //   quotes: ['error', 'single'],
  //   'prettier/prettier': [
  //     'error',
  //     {
  //       trailingComma: 'all',
  //       singleQuote: true,
  //       bracketSpacing: true,
  //       jsxBracketSameLine: true
  //     }
  //   ]
  // },
  // parser: '@typescript-eslint/parser',
  // parserOptions: {
  //   ecmaVersion: 2019,
  //   sourceType: 'module',
  //   ecmaFeatures: {
  //     jsx: true // Allows for the parsing of JSX
  //   }
  // }
}
