import React, { createContext, useContext } from 'react';
import { THEMES } from '../../utils/helpers';

const ThemeContext = createContext(null);

/**
 * Enhanced Theme CSS variables for each theme
 * More vibrant and premium color palettes
 */
const themeStyles = {
  'crescent-moon': {
    '--theme-bg-primary': '#0a0a1a',
    '--theme-bg-secondary': '#12122e',
    '--theme-bg-gradient': 'linear-gradient(135deg, #0a0a1a 0%, #12122e 30%, #1a1a3e 60%, #202050 100%)',
    '--theme-accent': '#FFD700',
    '--theme-accent-secondary': '#FFA500',
    '--theme-accent-glow': 'rgba(255, 215, 0, 0.4)',
    '--theme-text': '#FFFFFF',
    '--theme-text-muted': 'rgba(255, 255, 255, 0.75)',
    '--theme-card-bg': 'rgba(255, 215, 0, 0.08)',
    '--theme-card-border': 'rgba(255, 215, 0, 0.2)',
    '--theme-button-bg': 'linear-gradient(135deg, #FFE066 0%, #FFD700 50%, #FFA500 100%)',
    '--theme-button-text': '#1a1a2e',
    '--theme-success-glow': '0 0 30px rgba(255, 215, 0, 0.5)',
  },
  'masjid': {
    '--theme-bg-primary': '#041f1a',
    '--theme-bg-secondary': '#0a4d3c',
    '--theme-bg-gradient': 'linear-gradient(135deg, #041f1a 0%, #0a4d3c 30%, #0d6b4f 60%, #0f8560 100%)',
    '--theme-accent': '#FFD700',
    '--theme-accent-secondary': '#50C878',
    '--theme-accent-glow': 'rgba(255, 215, 0, 0.4)',
    '--theme-text': '#FFFFFF',
    '--theme-text-muted': 'rgba(255, 255, 255, 0.85)',
    '--theme-card-bg': 'rgba(255, 255, 255, 0.08)',
    '--theme-card-border': 'rgba(255, 215, 0, 0.25)',
    '--theme-button-bg': 'linear-gradient(135deg, #FFE066 0%, #FFD700 50%, #DAA520 100%)',
    '--theme-button-text': '#041f1a',
    '--theme-success-glow': '0 0 30px rgba(80, 200, 120, 0.5)',
  },
  'lantern': {
    '--theme-bg-primary': '#0d0510',
    '--theme-bg-secondary': '#2d1524',
    '--theme-bg-gradient': 'linear-gradient(135deg, #0d0510 0%, #1a0d1a 20%, #2d1524 50%, #4a2339 100%)',
    '--theme-accent': '#FFB347',
    '--theme-accent-secondary': '#FF6B35',
    '--theme-accent-glow': 'rgba(255, 179, 71, 0.5)',
    '--theme-text': '#FFF8E7',
    '--theme-text-muted': 'rgba(255, 248, 231, 0.75)',
    '--theme-card-bg': 'rgba(255, 179, 71, 0.12)',
    '--theme-card-border': 'rgba(255, 179, 71, 0.3)',
    '--theme-button-bg': 'linear-gradient(135deg, #FFD07F 0%, #FFB347 50%, #FF6B35 100%)',
    '--theme-button-text': '#1a0f1a',
    '--theme-success-glow': '0 0 30px rgba(255, 179, 71, 0.6)',
  },
  'geometric': {
    '--theme-bg-primary': '#051525',
    '--theme-bg-secondary': '#0a3d62',
    '--theme-bg-gradient': 'linear-gradient(135deg, #051525 0%, #0a3d62 30%, #1a5276 60%, #1e6f8e 100%)',
    '--theme-accent': '#00d2d3',
    '--theme-accent-secondary': '#5DFDCB',
    '--theme-accent-glow': 'rgba(0, 210, 211, 0.4)',
    '--theme-text': '#FFFFFF',
    '--theme-text-muted': 'rgba(255, 255, 255, 0.75)',
    '--theme-card-bg': 'rgba(0, 210, 211, 0.1)',
    '--theme-card-border': 'rgba(0, 210, 211, 0.3)',
    '--theme-button-bg': 'linear-gradient(135deg, #5DFDCB 0%, #00d2d3 50%, #00b3b4 100%)',
    '--theme-button-text': '#051525',
    '--theme-success-glow': '0 0 30px rgba(0, 210, 211, 0.5)',
  },
  'garden': {
    '--theme-bg-primary': '#0f2e1a',
    '--theme-bg-secondary': '#1a5c38',
    '--theme-bg-gradient': 'linear-gradient(180deg, #87CEEB 0%, #7EC8A0 25%, #4CAF7A 50%, #2E8B57 75%, #1a5c38 100%)',
    '--theme-accent': '#90EE90',
    '--theme-accent-secondary': '#FF69B4',
    '--theme-accent-glow': 'rgba(144, 238, 144, 0.4)',
    '--theme-text': '#FFFFFF',
    '--theme-text-muted': 'rgba(255, 255, 255, 0.85)',
    '--theme-card-bg': 'rgba(144, 238, 144, 0.1)',
    '--theme-card-border': 'rgba(144, 238, 144, 0.3)',
    '--theme-button-bg': 'linear-gradient(135deg, #B8F4B8 0%, #90EE90 50%, #7CCD7C 100%)',
    '--theme-button-text': '#0d2818',
    '--theme-success-glow': '0 0 30px rgba(144, 238, 144, 0.5)',
  },
  'calligraphy': {
    '--theme-bg-primary': '#1a1008',
    '--theme-bg-secondary': '#2C1810',
    '--theme-bg-gradient': 'linear-gradient(135deg, #1a1008 0%, #2C1810 30%, #3d2317 60%, #4a2c1e 100%)',
    '--theme-accent': '#D4AF37',
    '--theme-accent-secondary': '#F5E6D3',
    '--theme-accent-glow': 'rgba(212, 175, 55, 0.4)',
    '--theme-text': '#F5E6D3',
    '--theme-text-muted': 'rgba(245, 230, 211, 0.75)',
    '--theme-card-bg': 'rgba(212, 175, 55, 0.1)',
    '--theme-card-border': 'rgba(212, 175, 55, 0.3)',
    '--theme-button-bg': 'linear-gradient(135deg, #E8C872 0%, #D4AF37 50%, #B8962E 100%)',
    '--theme-button-text': '#1C1208',
    '--theme-success-glow': '0 0 30px rgba(212, 175, 55, 0.5)',
  },
  'desert': {
    '--theme-bg-primary': '#87CEEB',
    '--theme-bg-secondary': '#E0F6FF',
    '--theme-bg-gradient': 'linear-gradient(180deg, #87CEEB 0%, #E0F6FF 50%, #FFD700 100%)',
    '--theme-accent': '#DAA520',
    '--theme-accent-secondary': '#FDB813',
    '--theme-accent-glow': 'rgba(218, 165, 32, 0.4)',
    '--theme-text': '#4A3728', /* Dark brown text for contrast against bright desert */
    '--theme-text-muted': 'rgba(74, 55, 40, 0.75)',
    '--theme-card-bg': 'rgba(218, 165, 32, 0.1)',
    '--theme-card-border': 'rgba(218, 165, 32, 0.3)',
    '--theme-button-bg': 'linear-gradient(135deg, #FDB813 0%, #DAA520 50%, #CD853F 100%)',
    '--theme-button-text': '#FFFFFF',
    '--theme-success-glow': '0 0 30px rgba(218, 165, 32, 0.5)',
  },
  'ocean': {
    '--theme-bg-primary': '#1e3a8a',
    '--theme-bg-secondary': '#3b82f6',
    '--theme-bg-gradient': 'linear-gradient(180deg, #1e3a8a 0%, #3b82f6 50%, #60a5fa 100%)',
    '--theme-accent': '#ffffff',
    '--theme-accent-secondary': '#bae6fd',
    '--theme-accent-glow': 'rgba(255, 255, 255, 0.4)',
    '--theme-text': '#f0f9ff',
    '--theme-text-muted': 'rgba(240, 249, 255, 0.75)',
    '--theme-card-bg': 'rgba(59, 130, 246, 0.1)',
    '--theme-card-border': 'rgba(255, 255, 255, 0.3)',
    '--theme-button-bg': 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 50%, #1e3a8a 100%)',
    '--theme-button-text': '#FFFFFF',
    '--theme-success-glow': '0 0 30px rgba(255, 255, 255, 0.5)',
  }
};

/**
 * Apply theme CSS variables to element style
 */
export function getThemeStyle(themeId) {
  return themeStyles[themeId] || themeStyles['crescent-moon'];
}

/**
 * Get a specific theme color
 */
export function getThemeColor(themeId, colorKey) {
  const style = themeStyles[themeId] || themeStyles['crescent-moon'];
  return style[colorKey] || null;
}

/**
 * Theme Provider Component
 */
export function ThemeProvider({ themeId = 'crescent-moon', children }) {
  const style = getThemeStyle(themeId);
  
  return (
    <ThemeContext.Provider value={{ themeId, theme: THEMES[themeId], style }}>
      <div className="theme-wrapper" style={style}>
        {children}
      </div>
    </ThemeContext.Provider>
  );
}

/**
 * Hook to access current theme
 */
export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    return { 
      themeId: 'crescent-moon', 
      theme: THEMES['crescent-moon'],
      style: themeStyles['crescent-moon']
    };
  }
  return context;
}

export default ThemeProvider;
