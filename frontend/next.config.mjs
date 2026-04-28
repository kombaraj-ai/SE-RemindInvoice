/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Required for the Docker multi-stage build — produces .next/standalone
  output: 'standalone',
};

export default nextConfig;
