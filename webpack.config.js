const fs = require('fs');
const path = require('path');
const webpack = require('webpack');
const merge = require('webpack-merge');
const autoprefixer = require('autoprefixer');
const cssnano = require('cssnano');

const ExtractTextPlugin = require('extract-text-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const BabiliPlugin = require('babili-webpack-plugin');
const OptimizeCSSAssetsPlugin = require('optimize-css-assets-webpack-plugin');
const ManifestRevisionPlugin = require('manifest-revision-webpack-plugin');

const extractCss = new ExtractTextPlugin({
  filename: '[name].[chunkhash:8].css',
});

const JQUERY = 'jquery-3.2.1.slim.js';

const vendorPath = (name) => {
  return path.resolve(__dirname, 'plumbum/static/js/vendor/' + name);
};

const PATHS = {
  app: path.resolve(__dirname, 'plumbum/static/js/app/main.js'),
  style: path.resolve(__dirname, 'plumbum/static/scss/plumbum.scss'),
  build: path.resolve(__dirname, 'plumbum/static/webpack'),
};

const config = {
  entry: {
    app: PATHS.app,
    vendor: [
      vendorPath(JQUERY),
      vendorPath('tether.js'),
      vendorPath('bootstrap.js'),
      vendorPath('axios.js'),
    ],
    style: PATHS.style,
  },
  output: {
    path: PATHS.build,
    filename: '[name].[chunkhash:8].js',
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        loader: 'babel-loader',
        exclude: /vendor/,
        options: {
          cacheDirectory: true,
        },
      },
      {
        test: /\.css$/,
        use: extractCss.extract({
          use: [
            'css-loader',
            {
              loader: 'postcss-loader',
              options: {
                plugins: () => ([ autoprefixer ]),
              },
            },
          ],
          fallback: 'style-loader',
        }),
      },
      {
        test: /\.scss$/,
        use: extractCss.extract({
          use: [
            'css-loader',
            {
              loader: 'postcss-loader',
              options: {
                plugins: () => ([ autoprefixer ]),
              },
            },
            'sass-loader',
          ],
          fallback: 'style-loader',
        }),
      },
      {
        test: /\.(eot|ttf|woff|woff2|svg)(\?v=\d+\.\d+\.\d+)?$/,
        use: {
          loader: 'file-loader',
          options: {
            name: './font/[name].[hash:8].[ext]',
          },
        },
      },
    ],
  },
  resolve: {
    extensions: ['.js'],
    alias: {
      'jquery': vendorPath(JQUERY),
      'axios': vendorPath('axios.js'),
    },
  },
  plugins: [
    extractCss,
    new webpack.ProvidePlugin({
      $: vendorPath(JQUERY),
      jQuery: vendorPath(JQUERY),
      Tether: vendorPath('tether.js'),
      axios: vendorPath('axios.js'),
    }),
    new webpack.optimize.CommonsChunkPlugin({
      name: 'vendor',
    }),
    new webpack.optimize.CommonsChunkPlugin({
      name: 'manifest',
    }),
    new ManifestRevisionPlugin(path.join('./plumbum/static/webpack', 'manifest.json'), {
      rootAssetPath: './plumbum/static/',
      ignorePaths: ['/webpack', '/fonts', '/scss'],
    }),
  ],
};

const prodConfig = () => {
  console.log('env PRODUCTION detected');
  return merge(config, {
    output: {
      publicPath: '/static/plumbum/webpack/', // Exposed by flask
    },
    plugins: [
      new CleanWebpackPlugin([PATHS.build]),
      new BabiliPlugin(),
      new OptimizeCSSAssetsPlugin({
        cssProcessor: cssnano,
        cssProcessorOptions: {
          removeAll: true,
        },
        // run cssnanon in safe mode to avoid potentially unsafe
        // transformations
        safe: true,
      }),
    ],
  });
};

const devConfig = () => {
  console.log('env DEVELOPMENT detected');
  // Ensure PATHS.build directory exists to put manifest.json file
  if (!fs.existsSync(PATHS.build)) {
    fs.mkdirSync(PATHS.build);
  }
  const host = process.env.HOST ? process.env.HOST : 'localhost';
  const port = process.env.PORT ? process.env.PORT : 2992;
  return merge(config, {
    output: {
      publicPath: 'http://' + host + ':' + port + '/',
    },
    module: {
      rules: [
        {
          test: /\.js$/,
          exclude: /vendor/,
          enforce: 'pre',
          loader: 'eslint-loader',
          options: {
            emitWarnings: true,
          },
        },
      ],
    },
    devServer: {
      // Enable history API fallback so HTML5 History API based routing works.
      // Good for complex setups.
      historyApiFallback: true,

      // Display only errors to reducte the amount of output
      stats: 'errors-only',

      // Parse host and port from env to allow customization
      host: host, // Defaults to 'localhost'
      port: port, // Defaults to 8080

      // Allow CORS
      headers: { 'Access-Control-Allow-Origin': '*' },

      // overlay: true captures only errors
      overlay: {
        errors: true,
        warnings: true,
      },
    },
  });
};

module.exports = (env) => {
  if (env === 'production') {
    return prodConfig();
  }

  return devConfig();
};
