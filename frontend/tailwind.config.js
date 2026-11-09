/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Space Grotesk', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        ink: '#0a0a0a',
        'ink-2': '#111111',
        'ink-3': '#1a1a1a',
        wire: 'rgba(255,255,255,0.06)',
        'wire-2': 'rgba(255,255,255,0.12)',
        signal: '#e63946',
        'signal-dim': 'rgba(230,57,70,0.15)',
        chalk: '#f0f0f0',
        'chalk-2': '#a0a0a0',
        'chalk-3': '#505050',
      },
    },
  },
  plugins: [],
}
