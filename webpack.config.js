// webpack.config.js
// Конфигурация для бандлинга JS и CSS файлов

const path = require('path');
const TerserPlugin = require('terser-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');

module.exports = (env, argv) => {
  const isProduction = argv.mode === 'production';
  
  return {
    mode: isProduction ? 'production' : 'development',
    
    entry: {
      // Основные бандлы
      common: './js/common.js',
      index: './js/index.js',
      auth: './js/auth.js',
      problem: './js/problem.js',
      solution: './js/solution.js',
      admin: './js/admin.js',
      
      // Утилиты
      utils: './js/utils/index.js',
    },
    
    output: {
      filename: isProduction ? 'js/[name].[contenthash].min.js' : 'js/[name].js',
      path: path.resolve(__dirname, 'dist'),
      publicPath: '/static/',
      clean: true,
    },
    
    module: {
      rules: [
        // JavaScript
        {
          test: /\.js$/,
          exclude: /node_modules/,
          use: {
            loader: 'babel-loader',
            options: {
              presets: [
                ['@babel/preset-env', {
                  modules: false,
                  useBuiltIns: 'usage',
                  corejs: 3,
                }],
              ],
              plugins: [
                '@babel/plugin-proposal-class-properties',
              ],
            },
          },
        },
        
        // CSS
        {
          test: /\.css$/,
          use: [
            isProduction ? MiniCssExtractPlugin.loader : 'style-loader',
            {
              loader: 'css-loader',
              options: {
                sourceMap: !isProduction,
                importLoaders: 1,
              },
            },
            {
              loader: 'postcss-loader',
              options: {
                postcssOptions: {
                  plugins: [
                    ['autoprefixer'],
                    isProduction && ['cssnano', {
                      preset: ['default', {
                        discardComments: {
                          removeAll: true,
                        },
                      }],
                    }],
                  ].filter(Boolean),
                },
              },
            },
          ],
        },
        
        // Images
        {
          test: /\.(png|jpg|jpeg|gif|svg)$/,
          type: 'asset',
          parser: {
            dataUrlCondition: {
              maxSize: 8 * 1024, // 8KB
            },
          },
          generator: {
            filename: 'images/[name].[hash][ext]',
          },
        },
        
        // Fonts
        {
          test: /\.(woff|woff2|eot|ttf|otf)$/,
          type: 'asset/resource',
          generator: {
            filename: 'fonts/[name].[hash][ext]',
          },
        },
      ],
    },
    
    plugins: [
      new MiniCssExtractPlugin({
        filename: isProduction ? 'css/[name].[contenthash].min.css' : 'css/[name].css',
      }),
    ],
    
    optimization: {
      minimize: isProduction,
      minimizer: [
        new TerserPlugin({
          terserOptions: {
            compress: {
              drop_console: isProduction,
            },
            output: {
              comments: false,
            },
          },
          extractComments: false,
        }),
        new CssMinimizerPlugin(),
      ],
      
      splitChunks: {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            priority: 10,
          },
          common: {
            minChunks: 2,
            priority: 5,
            reuseExistingChunk: true,
          },
        },
      },
      
      runtimeChunk: 'single',
    },
    
    resolve: {
      extensions: ['.js', '.json', '.css'],
      alias: {
        '@utils': path.resolve(__dirname, 'js/utils'),
        '@css': path.resolve(__dirname, 'css'),
      },
    },
    
    devtool: isProduction ? false : 'source-map',
    
    devServer: {
      port: 3000,
      hot: true,
      historyApiFallback: true,
      proxy: {
        '/api': {
          target: 'http://localhost:8080',
          pathRewrite: { '^/api': '/api' },
          changeOrigin: true,
        },
      },
    },
    
    performance: {
      hints: isProduction ? 'warning' : false,
      maxEntrypointSize: 512000,
      maxAssetSize: 512000,
    },
  };
};
