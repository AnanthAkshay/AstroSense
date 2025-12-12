/** @type {import('next').NextConfig} */
const nextConfig = {
  // Use default Next.js configuration
  swcMinify: true,
  webpack: (config, { dev, isServer }) => {
    // Handle Cesium.js
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
      path: false,
    }
    
    return config
  },
}

module.exports = nextConfig