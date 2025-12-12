/** @type {import('next').NextConfig} */
const nextConfig = {
  // Completely disable SWC to avoid Windows binary issues
  swcMinify: false,
  // Force Babel usage
  experimental: {
    forceSwcTransforms: false,
  },
  webpack: (config, { dev, isServer }) => {
    // Force Babel for all JS/TS files
    config.module.rules.push({
      test: /\.(js|jsx|ts|tsx)$/,
      exclude: /node_modules/,
      use: {
        loader: 'babel-loader',
        options: {
          presets: ['next/babel'],
          cacheDirectory: true,
        },
      },
    })

    // Handle Cesium.js
    config.module.rules.push({
      test: /\.js$/,
      use: {
        loader: 'babel-loader',
        options: {
          presets: ['next/babel'],
        },
      },
      include: /node_modules\/cesium/,
    })
    
    return config
  },
}

module.exports = nextConfig