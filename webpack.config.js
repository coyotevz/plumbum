const path = require('path');
const webpack = require('webpack');
const merge = require('webpack-merge');
const ExtractTextPlugin = require('extract-text-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const BabiliPlugin = require('babili-webpack-plugin');
const CompressionPlugin = require('compression-webpack-plugin');
const ManifestRevisionPlugin = require('manifest-revision-webpack-plugin');

const extractCss = new ExtractTextPlugin({
  filename: '[name].[chunkhash:8].css',
});

const vendorPath = (name) => {
  return path.resolve(__dirname, 'plumbum/static/js/vendor/' + name);
};

const PATHS = {
  app: path.resolve(__dirname, 'plumbum/static/js/app/main.js'),
  build: path.resolve(__dirname, 'build'),
};

const config = {
  entry: {
    app: PATHS.app,
    vendor: [
      vendorPath('jquery-3.2.1.slim.js'),
      vendorPath('tether.js'),
      vendorPath('bootstrap.js'),
      vendorPath('axios.js'),
    ],
  },
  output: {
    path: PATHS.build,
    filename: '[name].[chunkhash:8].js',
  },
  plugins: [
    extractCss,
    new webpack.optimize.CommonsChunkPlugin({
      name: 'vendor',
    }),
    new ManifestRevisionPlugin(path.join(PATHS.build, 'manifest.json'), {
      rootAssetPath: './plumbum/static',
      ignorePaths: ['/fonts', '/scss'],
    }),
  ],
};

const prodConfig = () => {
  console.log('env PRODUCTION detected');
  return merge(config, {
    plugins: [
      new CleanWebpackPlugin([PATHS.build]),
      new BabiliPlugin(),
      new CompressionPlugin({
        asset: '[path].gz[query]',
      }),
    ],
  });
};

const devConfig = () => {
  console.log('env DEVELOPMENT detected');
  return merge(config, {
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
      host: process.env.HOST, // Defaults to 'localhost'
      port: process.env.PORT, // Defaults to 8080

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
