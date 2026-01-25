import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./pages/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#60A5FA", // 예쁜 파란색 (blue-400)
          foreground: "#FFFFFF", // White
        },
        secondary: {
          DEFAULT: "#3B82F6", // 중간 파란색 (blue-500)
          foreground: "#FFFFFF", // White
        },
        accent: {
          DEFAULT: "#38BDF8", // 스카이 블루 (sky-400)
          foreground: "#FFFFFF", // White
        },
      },
      fontFamily: {
        display: ['"Black Han Sans"', "sans-serif"],
        body: ['"Noto Sans KR"', "sans-serif"],
      },
      boxShadow: {
        "brutal": "8px 8px 0 0 rgba(0, 0, 0, 1)",
        "brutal-sm": "4px 4px 0 0 rgba(0, 0, 0, 1)",
      },
    },
  },
  plugins: [],
};

export default config;

