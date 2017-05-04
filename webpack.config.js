var path = require('path');

var ExtractTextPlugin = require('extract-text-webpack-plugin');
var ManifestRevisionPlugin = require('manifest-revision-webpack-plugin');

var rootAssetPath = './assets';

module.exports = {
  entry: {
    app_js: [
      'plumbum/static/js/tether.js',
      //rootAssetPath + '/scripts/entry.js'
    ],
    app_css: [
      'plumbum/static/css/plumbum.css'
      //rootAssetPath + '/styles/main.css'
    ]
  },
  output: {
    path: path.resolve(__dirname, './build/public'),
    publicPath: 'http://localhost:2992/assets/',
    filename: '[name].[chunkhash].js',
    chunkFilename: '[id].[chunkhash].js'
  },
  resolve: {
    extensions: ['.js', '.css']
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
        loader: ExtractTextPlugin.extract({ fallback: 'style-loader', use: 'css-loader'})
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
