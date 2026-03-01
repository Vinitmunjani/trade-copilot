import React from "react";

type AmpereLogoProps = {
  className?: string;
};

export function AmpereLogo({ className }: AmpereLogoProps) {
  return (
    <svg
      viewBox="0 0 96 96"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
      focusable="false"
    >
      <defs>
        <linearGradient id="ampereGradient" x1="14" y1="8" x2="78" y2="86" gradientUnits="userSpaceOnUse">
          <stop stopColor="hsl(var(--accent-glow))" />
          <stop offset="0.45" stopColor="hsl(var(--accent))" />
          <stop offset="1" stopColor="hsl(var(--accent-soft))" />
        </linearGradient>
        <mask id="ampereCutout" maskUnits="userSpaceOnUse" x="8" y="6" width="80" height="84">
          <rect x="8" y="6" width="80" height="84" fill="white" />
          <path
            d="M26 55C33 47 45 43 58 43C66 43 73 45 80 49C71 64 57 74 39 76C31 76 24 74 18 70C20 64 22 59 26 55Z"
            fill="black"
          />
        </mask>
      </defs>

      <path
        mask="url(#ampereCutout)"
        d="M46 8C32 8 20 16 14 30C11 36 9 42 9 49C9 69 25 86 45 88C56 89 67 85 75 77C82 71 87 62 87 52C87 40 80 30 69 26C62 23 56 20 52 15C50 12 48 10 46 8Z"
        fill="url(#ampereGradient)"
      />

      <path
        d="M49 18C42 18 35 22 31 29C29 33 27 37 27 42C27 45 28 47 30 49C33 52 38 53 44 53C50 53 56 52 63 54C54 62 42 66 31 66C24 66 18 64 14 60C10 56 8 51 8 44C8 34 12 25 19 18C27 10 38 6 49 6C59 6 67 9 74 15C68 16 62 18 58 22C56 20 53 18 49 18Z"
        fill="url(#ampereGradient)"
      />
    </svg>
  );
}
