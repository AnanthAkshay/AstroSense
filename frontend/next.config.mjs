/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  webpack: (config) => {
    // Cesium configuration
    config.module.rules.push({
      test: /\.js$/,
      include: /cesium/,
      use: {
        loader: 'babel-loader',
        options: {
          presets: ['@babel/preset-env'],
        },
      },
    });
    return config;
  },
};

export default nextConfig;
