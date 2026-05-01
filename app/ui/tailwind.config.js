/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        navy:  { 50: '#f0f4ff', 100: '#dce6ff', 500: '#1a3a6b', 600: '#10296b', 700: '#0c1f52', 900: '#070f2e' },
        gold:  { 300: '#fcd96a', 400: '#f5c842', 500: '#d4a017', 600: '#b8870b' },
        slate: { 50: '#f8fafc', 100: '#f1f5f9' },
      },
      backgroundImage: {
        'gradient-navy': 'linear-gradient(135deg, #1a3a6b 0%, #0c1f52 100%)',
        'gradient-gold': 'linear-gradient(135deg, #d4a017 0%, #f5c842 100%)',
      },
      boxShadow: {
        'glow-navy': '0 0 20px rgba(26,58,107,0.3)',
        'glow-gold': '0 0 20px rgba(212,160,23,0.3)',
      },
    },
  },
  plugins: [],
}
