/** @type {import('tailwindcss').Config} */
// Color tokens are the single source of truth from tech-stack.md §2.5.
// Do NOT hard-code hex values in component files — extend tokens here first.
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: "#FFD100", hover: "#F6C400", light: "#FFF3C4" },
        page: "#FAF8F2",
        card: "#FFFFFF",
        surface: "#F6F7F9",
        ink: { DEFAULT: "#111111", secondary: "#555555", muted: "#8A8A8A" },
        line: "#E6E6E6",
        ai: { purple: "#7C5CFF", blue: "#28A8FF", wash: "#F4F0FF" },
        success: "#16A34A",
        warning: "#F97316",
        danger: "#EF4444",
        info: "#3B82F6",
      },
    },
  },
  plugins: [],
};
