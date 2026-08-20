import type { NextConfig } from "next";

const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

const nextConfig: NextConfig = {
  basePath,
  // Standalone output contains the minimal production server copied by the runtime image.
  output: "standalone",
  // Development double-invocation surfaces unsafe React side effects early.
  reactStrictMode: true,
};

export default nextConfig;
