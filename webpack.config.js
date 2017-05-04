var path = require('path');

var ExtractTextPlugin = require('extract-text-webpack-plugin');

var rootAssetPath = './assets';

module.exports = {
  entry: {
    app_js: [
      rootAssetPath + '/scripts/entry.js'
    ],
    app_css: [
      rootAssetPath + '/styles/main.css'
    ]
  },
  output: {
    path: './build/public',
    publicPath: 'http://localhost:2992/assets/',
    filename: '[name].[chunkhash].js'
    chunkFilename: '[id].[chunkhash].js'
  },
  resolve: {
    extensions: ['', '.js', '.css']
  },
  module: {
    loaders: [
      {
        test: /\.js$/i,
        loader: 'script-loader',
        exclude: /node_modules/,
      },
      {
        test: /\.css$/i,
        loader: ExtractTextPlugin.extract('style-loader', 'css-loader')
      }
    ]
  },
  plugins: [
    new ExtractTextPlugin('[name].[chunkhash].css'),
    new ManifestRevisionPlugin(path.join('build', 'manifest.json'), {
      rootAssetPath: rootAssetPath,
      ignorePaths: ['/styles', '/scripts']
    })
  ]
};
