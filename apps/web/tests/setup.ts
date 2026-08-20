import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Remove rendered DOM and event handlers so tests cannot leak state into the next case.
afterEach(cleanup);
