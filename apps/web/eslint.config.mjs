import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTypeScript from "eslint-config-next/typescript";

export default defineConfig([
  ...nextVitals,
  ...nextTypeScript,
  // Generated output and framework-owned declarations are not maintainable source inputs.
  globalIgnores([".next/**", "coverage/**", "next-env.d.ts"]),
]);
