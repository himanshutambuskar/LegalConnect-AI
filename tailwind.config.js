/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        trust: {
          DEFAULT: '#00327d',
          dark: '#002257',
          hover: '#002663',
          light: '#edf3fc',
          surface: '#f4f6fa',
          tint: '#d8e5f8',
        },
        emergency: {
          bg: '#fde8e8',
          border: '#fca5a5',
          text: '#7a0000',
          dark: '#540909',
          banner: '#4a1506'
        }
      },
      fontFamily: {
        serif: ['"Source Serif 4"', 'Georgia', 'serif'],
        sans: ['"Hanken Grotesk"', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'lg': '8px',
        'xl': '12px',
        '2xl': '16px',
        '3xl': '24px',
      }
    },
  },
  plugins: [],
}
