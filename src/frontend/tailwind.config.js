/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,html}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f4ff',
          100: '#e0e9ff',
          200: '#c7d5fe',
          300: '#a5b9fc',
          400: '#8094f7',
          500: '#667eea',
          600: '#5865de',
          700: '#4f52c4',
          800: '#41449e',
          900: '#383d7d',
          950: '#24264a',
          DEFAULT: '#667eea',
          dark: '#5865de',
        },
      },
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          '"Microsoft JhengHei"',
          '"PingFang TC"',
          '"Noto Sans TC"',
          'sans-serif',
        ],
      },
    },
  },
  plugins: [],
};
