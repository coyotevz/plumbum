var path = require('path');
var webpack = require('webpack');
var ExtractTextPlugin = require('extract-text-webpack-plugin');

var extractSass = new ExtractTextPlugin({
  filename: "[name].[contenthash].css",
  disable: process.env.NODE_ENV === "devlopment",
});

module.exports = {
  entry: {
    app_js: [
      './plumbum/static/js/jquery-3.2.1.slim.js',
    ],
    app_css: './plumbum/static/scss/plumbum.scss',
  },
  output: {
    path: path.resolve(__dirname, 'dist'),
    publicPath: '/static/',
    filename: '[name].[chunkhash].js',
  },
  resolve: {
    extensions: ['.js', '.css'],
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        loader: 'script-loader',
        exclude: /node_modules/
      },
      {
        test: /\.scss$/,
        use: extractSass.extract({
          use: [
            { loader: "css-loader" },
            { loader: "sass-loader" },
          ],
          fallback: "style-loader",
        })
      },
    ]
  },
  plugins: [
    extractSass,
  ]
};
