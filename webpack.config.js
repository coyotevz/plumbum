var path = require('path')
var webpack = require('webpack')
var ExtractTextPlugin = require('extract-text-webpack-plugin')
var AutoPrefixerPlugin = require('autoprefixer')
var ManifestRevisionPlugin = require('manifest-revision-webpack-plugin')

// Environment detection
var node_env = process.env.NODE_ENV || 'development'

var rootAssetPath = './plumbum/static'
var buildOutPath = path.resolve(__dirname, 'build/public')

var plugins = [
  new webpack.NoEmitOnErrorsPlugin(),
  new webpack.optimize.CommonsChunkPlugin({ name: 'vendor', filename: 'vendor.js'}),
  new ExtractTextPlugin('[name].[hash:7].css'),
  new ManifestRevisionPlugin(path.join('build', 'manifest.json'), {
    rootAssetPath: rootAssetPath,
    ignorePaths: ['/js', '/css', '/scss'],
  })
]

if (node_env !== 'development') {
   plugins = (plugins || []).concat([
    new webpack.optimize.UglifyJsPlugin({compressor: { warnings: false }}),
  ])
}

module.exports = {
  entry: {
    vendor: [
      rootAssetPath + '/js/vendor/jquery-3.2.1.slim.js',
      rootAssetPath + '/js/vendor/tether.js',
      rootAssetPath + '/js/vendor/bootstrap.js',
      rootAssetPath + '/js/vendor/axios.js',
    ],
    script: [
      rootAssetPath + '/js/app/plumbum.js',
    ],
    style: [
      rootAssetPath + '/scss/plumbum.scss',
    ]
  },
  output: {
    path: buildOutPath,
    publicPath: 'http://localhost:2992/assets/',
    filename: '[name].[hash:7].js',
    chunkFilename: '[id].[hash:7].js',
  },
  resolve: {
    extensions: ['.js', '.css'],
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        loader: 'script-loader',
        exclude: /node_modules/,
      },
      {
        test: /\.css$/,
        loader: ExtractTextPlugin.extract({
          use: 'css-loader',
          fallback: 'style-loader'
        }),
      },
      {
        test: /\.scss$/,
        loader: ExtractTextPlugin.extract({
          use: ['css-loader', 'sass-loader'],
          fallback: 'style-loader',
        }),
      },
      {
        test: /\.(png|jpe?g|gif|svg)(\?.*)?$/,
        loader: 'url-loader',
        query: {
          limit: 100000,
          name: 'img/[name].[hash:7].[ext]',
        }
      },
      {
        test: /\.(woff2?|eot|ttf|otf)(\?.*)?$/,
        loader: 'url-loader',
        query: {
          limit: 100000,
          name: 'fonts/[name].[hash:7].[ext]',
        }
      },
    ]
  },
  plugins: plugins,
}
