import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  output: 'standalone',
  compress: true,
  poweredByHeader: false,
  reactStrictMode: true,
  async redirects() {
    return [
      { source: '/offboarding', destination: '/login', permanent: false },
      { source: '/offboarding/employee', destination: '/employee/offboarding', permanent: true },
      { source: '/offboarding/employee/dashboard', destination: '/employee/offboarding', permanent: true },
      { source: '/offboarding/manager', destination: '/manager/dashboard', permanent: true },
      { source: '/offboarding/manager/dashboard', destination: '/manager/dashboard', permanent: true },
      { source: '/manager/offboarding', destination: '/manager/dashboard', permanent: true },
    ];
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: false,
  },
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      '@/professional-ui': path.resolve(__dirname, '../professional-ui'),
    };
    return config;
  },
};

export default nextConfig;
