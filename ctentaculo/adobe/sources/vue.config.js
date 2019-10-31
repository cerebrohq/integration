module.exports = {
  pages: {
    Actions: 'src/pages/Actions/main.ts',
    Browser: 'src/pages/Browser/main.ts',
  },
  publicPath: process.env.NODE_ENV === 'production' ? './' : '/',
  configureWebpack: {
    target: 'node-webkit',
    node: {
      dns: 'mock',
      fs: 'empty',
      path: true,
      url: false,
    },
  },
  transpileDependencies: ['copy-text-to-clipboard'],
}
