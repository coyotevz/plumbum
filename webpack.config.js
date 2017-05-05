var path = require('path')
var webpack = require('webpack')
var CompressionPlugin = require('compression-webpack-plugin')
var ExtractTextPlugin = require('extract-text-webpack-plugin')
var AutoPrefixerPlugin = require('autoprefixer')
var ManifestRevisionPlugin = require('manifest-revision-webpack-plugin')

var ROOT_PATH = path.resolve(__dirname, '.')
var ROOT_ASSET_PATH = './plumbum/static'
var BUILD_OUT_PATH = path.resolve(ROOT_PATH, 'build/public')
var IS_PRODUCTION = process.env.NODE_ENV === 'production'
var IS_DEV_SERVER = process.argv[1].indexOf('webpack-dev-server') !== -1
var DEV_SERVER_HOST = process.env.DEV_SERVER_HOST || 'localhost'
var DEV_SERVER_PORT = parseInt(process.env.DEV_SERVER_PORT, 10) || 2992

var config = {
  entry: {
    vendor: [
      ROOT_ASSET_PATH + '/js/vendor/jquery-3.2.1.slim.js',
      ROOT_ASSET_PATH + '/js/vendor/tether.js',
      ROOT_ASSET_PATH + '/js/vendor/bootstrap.js',
      ROOT_ASSET_PATH + '/js/vendor/axios.js',
    ],
    script: [
      ROOT_ASSET_PATH + '/js/app/plumbum.js',
    ],
    style: [
      ROOT_ASSET_PATH + '/scss/plumbum.scss',
    ]
  },

  output: {
    path: BUILD_OUT_PATH,
    publicPath: '/assets/webpack',
    filename: '[name].[hash:7].js',
    chunkFilename: '[id].[hash:7].js',
  },

  devtool: 'cheap-module-source-map',

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

  plugins: [
    new ManifestRevisionPlugin(path.join('build', 'manifest.json'), {
      rootAssetPath: ROOT_ASSET_PATH,
      ignorePaths: ['/js', '/css', '/scss'],
    }),

    new ExtractTextPlugin('[name].[hash:7].css'),
  ],
}

if (IS_PRODUCTION) {
  console.log('PRODUCTION detected')
  config.devtool = 'source-map'
  config.plugins.push(
    new webpack.NoEmitOnErrorsPlugin(),
    new webpack.LoaderOptionsPlugin({
      minimize: true,
      debug: false,
    }),
    new webpack.optimize.UglifyJsPlugin({
      sourceMap: true
    }),
    new webpack.DefinePlugin({
      'process.env': { NODE_ENV: JSON.stringify('production') }
    }),
    new CompressionPlugin({
      asset: '[path].gz[query]',
    })
  )
}

if (IS_DEV_SERVER) {
  console.log('DEVSERVER detected')
  config.devtool = 'cheap-module-eval-source-map'
  config.devServer = {
    host: DEV_SERVER_HOST,
    port: DEV_SERVER_PORT,
    headers: { 'Access-Control-Allow-Origin': '*' },
    stats: 'errors-only',
  }
  config.output.publicPath = '//' + DEV_SERVER_HOST + ':' + DEV_SERVER_PORT + config.output.publicPath
}

module.exports = config
