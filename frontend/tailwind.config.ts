import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        surface: "hsl(var(--surface))",
        "surface-muted": "hsl(var(--surface-muted))",
        "surface-contrast": "hsl(var(--surface-contrast))",
        border: "hsl(var(--border))",
        muted: "hsl(var(--muted))",
        accent: {
          DEFAULT: "hsl(var(--accent))",
          soft: "hsl(var(--accent-soft))",
          glow: "hsl(var(--accent-glow))",
        },
        success: "hsl(var(--success))",
        danger: "hsl(var(--danger))",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Inter", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "Geist Mono", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        glow: "0 0 80px rgba(16, 185, 129, 0.25)",
        card: "0 20px 60px rgba(4, 120, 87, 0.15)",
      },
      borderRadius: {
        lg: "var(--radius-lg)",
        xl: "var(--radius-xl)",
        full: "9999px",
      },
      backgroundImage: {
        "grid-radial": "radial-gradient(circle at center, rgba(16, 185, 129, 0.12), transparent 55%)",
        "ampere-beam":
          "conic-gradient(from 180deg at 50% 50%, rgba(16, 185, 129, 0.35), transparent, rgba(59, 130, 246, 0.15), transparent)",
      },
      keyframes: {
        "shine-sweep": {
          "0%": { transform: "translate3d(-100%, 0, 0)" },
          "100%": { transform: "translate3d(100%, 0, 0)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-8px)" },
        },
        pulseGlow: {
          "0%, 100%": { opacity: "0.35", filter: "blur(50px)" },
          "50%": { opacity: "0.65", filter: "blur(60px)" },
        },
      },
      animation: {
        "shine-sweep": "shine-sweep 2.5s linear infinite",
        float: "float 6s ease-in-out infinite",
        "pulse-glow": "pulseGlow 8s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
export default config;
