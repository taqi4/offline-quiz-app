import React, { useMemo } from 'react';
import './ThemeBackgrounds.css';

/**
 * Enhanced Star Component
 */
const Star = ({ size, style }) => (
  <div className={`star star-${size}`} style={style} />
);

/**
 * Crescent Moon & Stars Theme Background - REVERTED TO PREVIOUS VERSION
 */
export function CrescentMoonBackground() {
  return (
    <div className="theme-bg crescent-moon-bg">
      {/* Nebula gradient overlay */}
      <div className="nebula-overlay"></div>
      
      {/* Crescent Moon with glow */}
      <div className="moon-container">
        <div className="moon-glow"></div>
        <div className="moon">
          <div className="moon-inner"></div>
          <div className="moon-crater crater-1"></div>
          <div className="moon-crater crater-2"></div>
          <div className="moon-crater crater-3"></div>
        </div>
      </div>
      
      {/* Stars - different sizes */}
      {[...Array(50)].map((_, i) => (
        <div
          key={i}
          className={`star star-${(i % 3) + 1}`}
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 80}%`,
            animationDelay: `${Math.random() * 4}s`,
            animationDuration: `${2 + Math.random() * 2}s`
          }}
        />
      ))}
      
      {/* Shooting stars */}
      {[...Array(3)].map((_, i) => (
        <div
          key={`shooting-${i}`}
          className="shooting-star"
          style={{
            top: `${10 + i * 25}%`,
            animationDelay: `${i * 3}s`
          }}
        />
      ))}
      
      {/* Floating particles */}
      {[...Array(20)].map((_, i) => (
        <div
          key={`particle-${i}`}
          className="cosmic-particle"
          style={{
            left: `${Math.random() * 100}%`,
            animationDelay: `${Math.random() * 5}s`,
            animationDuration: `${4 + Math.random() * 3}s`
          }}
        />
      ))}
    </div>
  );
}

/**
 * Masjid Theme Background - ARCHITECTURAL MASTERPIECE
 */
export function MasjidBackground() {
  const stars = useMemo(() => [...Array(40)].map((_, i) => ({
    style: {
      left: `${Math.random() * 100}%`,
      top: `${Math.random() * 60}%`, // Only in the sky area
      animationDelay: `${Math.random() * 3}s`,
      opacity: Math.random() * 0.7
    }
  })), []);

  return (
    <div className="theme-bg masjid-bg-premium">
      <div className="star-field">
        {stars.map((star, i) => (
          <div key={i} className="star star-small" style={star.style} />
        ))}
      </div>

      <div className="moon-large-backdrop"></div>

      <div className="city-silhouette-bg"></div>

      <div className="masjid-silhouette-layer">
        <svg viewBox="0 0 1200 600" preserveAspectRatio="xMidYMax slice" style={{ width: '100%', height: '100%' }}>
          <defs>
            <linearGradient id="masjidGradMain" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#1e293b" /> 
              <stop offset="100%" stopColor="#0f172a" />
            </linearGradient>
            <linearGradient id="domeGold" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#FCD34D" />
              <stop offset="50%" stopColor="#F59E0B" />
              <stop offset="100%" stopColor="#B45309" />
            </linearGradient>
          </defs>
          
          {/* Main Dome */}
          <path d="M400,350 Q600,100 800,350 Z" fill="url(#domeGold)" className="masjid-dome-glow" />
          <path d="M600,100 L600,60" stroke="#FCD34D" strokeWidth="4" />
          <path d="M600,60 L590,50 M600,60 L610,50 M600,60 L600,40" stroke="#FCD34D" strokeWidth="4" />

          {/* Structure Body */}
          <rect x="300" y="350" width="600" height="250" fill="url(#masjidGradMain)" />
          
          {/* Minarets */}
          <rect x="250" y="200" width="40" height="400" fill="url(#masjidGradMain)" />
          <path d="M240,200 L270,150 L300,200 Z" fill="url(#masjidGradMain)" />
          
          <rect x="910" y="200" width="40" height="400" fill="url(#masjidGradMain)" />
          <path d="M900,200 L930,150 L960,200 Z" fill="url(#masjidGradMain)" />

          {/* Windows (Lit) */}
          <rect x="450" y="400" width="30" height="50" rx="15" fill="#FEF3C7" className="masjid-window-light" style={{ animationDelay: '0s' }} />
          <rect x="550" y="400" width="30" height="50" rx="15" fill="#FEF3C7" className="masjid-window-light" style={{ animationDelay: '1s' }} />
          <rect x="650" y="400" width="30" height="50" rx="15" fill="#FEF3C7" className="masjid-window-light" style={{ animationDelay: '0.5s' }} />
          <rect x="750" y="400" width="30" height="50" rx="15" fill="#FEF3C7" className="masjid-window-light" style={{ animationDelay: '1.5s' }} />
        </svg>
      </div>
    </div>
  );
}

/**
 * Lantern Theme Background - MAGICAL NIGHT
 */
export function LanternBackground() {
  const particles = useMemo(() => [...Array(30)].map((_, i) => ({
    style: {
      left: `${Math.random() * 100}%`,
      animationDuration: `${5 + Math.random() * 10}s`,
      animationDelay: `${Math.random() * 5}s`
    }
  })), []);

  return (
    <div className="theme-bg lantern-bg-premium">
      <div className="lantern-glow-ambient"></div>
      <div className="lantern-light-beam"></div>

      <div className="lantern-string">
         <svg width="100%" height="40" preserveAspectRatio="none">
             <path d="M0,10 Q500,60 1000,10" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
         </svg>
      </div>

      <div className="hanging-lantern" style={{ left: '15%', height: '120px' }}>
         <svg viewBox="0 0 60 120" height="120">
           <path d="M30,0 L30,20 M10,30 L50,30 L60,60 L50,90 L10,90 L0,60 L10,30 Z" fill="rgba(255, 165, 0, 0.8)" stroke="#FFD700" strokeWidth="1" />
           <circle cx="30" cy="60" r="10" fill="#FFFFE0" filter="drop-shadow(0 0 5px #FFD700)" />
         </svg>
      </div>
      
      <div className="hanging-lantern" style={{ left: '50%', height: '150px', top: '-5px' }}>
         <svg viewBox="0 0 80 140" height="140">
           <path d="M40,0 L40,25 M20,35 L60,35 L70,70 L50,110 L30,110 L10,70 L20,35 Z" fill="rgba(255, 140, 0, 0.9)" stroke="#FFD700" strokeWidth="1.5" />
           <circle cx="40" cy="70" r="12" fill="#FFFFE0" filter="drop-shadow(0 0 8px #FF4500)" />
         </svg>
      </div>

      <div className="hanging-lantern" style={{ left: '85%', height: '120px' }}>
         <svg viewBox="0 0 60 120" height="120">
           <path d="M30,0 L30,20 M10,30 L50,30 L60,60 L50,90 L10,90 L0,60 L10,30 Z" fill="rgba(255, 165, 0, 0.8)" stroke="#FFD700" strokeWidth="1" />
           <circle cx="30" cy="60" r="10" fill="#FFFFE0" filter="drop-shadow(0 0 5px #FFD700)" />
         </svg>
      </div>

      {particles.map((p, i) => (
        <div key={i} className="particle-dust" style={p.style} />
      ))}
    </div>
  );
}

/**
 * Geometric Theme Background - KALEIDOSCOPE
 */
export function GeometricBackground() {
  const shapes = useMemo(() => [...Array(15)].map((_, i) => ({
    type: i % 3,
    style: {
      left: `${Math.random() * 100}%`,
      top: `${Math.random() * 100}%`,
      animationDelay: `${Math.random() * 5}s`,
      transform: `scale(${0.5 + Math.random()})`
    }
  })), []);

  return (
    <div className="theme-bg geometric-bg-premium">
      <div className="geometric-overlay"></div>
      
      <div className="rotating-mandala">
        <svg viewBox="0 0 200 200" style={{ width: '100%', height: '100%' }}>
            <circle cx="100" cy="100" r="90" fill="none" stroke="#10b981" strokeWidth="0.5" strokeDasharray="5,5" />
            <rect x="50" y="50" width="100" height="100" fill="none" stroke="#10b981" strokeWidth="0.5" transform="rotate(45, 100, 100)" />
            <rect x="50" y="50" width="100" height="100" fill="none" stroke="#10b981" strokeWidth="0.5" />
        </svg>
      </div>

      {shapes.map((shape, i) => (
        <div key={i} className="geometric-shape-premium" style={shape.style}>
            <svg width="40" height="40" viewBox="0 0 40 40">
                {shape.type === 0 && <rect x="10" y="10" width="20" height="20" transform="rotate(45, 20, 20)" fill="currentColor" />}
                {shape.type === 1 && <circle cx="20" cy="20" r="10" fill="currentColor" />}
                {shape.type === 2 && <polygon points="20,5 35,35 5,35" fill="currentColor" />}
            </svg>
        </div>
      ))}
    </div>
  );
}

/**
 * Garden Theme Background - PARADISE
 */
export function GardenBackground() {
  const flowers = useMemo(() => [...Array(20)].map((_, i) => ({
    char: ['🌸', '🌺', '🌷', '🌹', '🌻'][i % 5],
    style: {
      left: `${5 + Math.random() * 90}%`,
      animationDelay: `${Math.random() * 2}s`,
      fontSize: `${Math.random() * 1.5 + 1}rem`
    }
  })), []);
  
  const clouds = useMemo(() => [...Array(5)].map((_, i) => ({
      style: {
          top: `${10 + (i * 15)}%`,
          animationDuration: `${30 + Math.random() * 20}s`,
          animationDelay: `${i * -5}s`,
          opacity: 0.7
      }
  })), []);

  return (
    <div className="theme-bg garden-bg-premium">
      <div className="sun-shimmer"></div>
      
      {clouds.map((cloud, i) => (
          <div key={i} className="cloud-fluffy" style={{...cloud.style, fontSize: '4rem'}}>
              ☁️
          </div>
      ))}
      
      <div className="grass-layer"></div>
      
      {flowers.map((flower, i) => (
        <div key={i} className="flower-swaying" style={flower.style}>
          {flower.char}
        </div>
      ))}

      {/* Butterflies */}
      <div className="butterfly" style={{ top: '40%', left: '20%', fontSize: '1.5rem', animationDuration: '6s' }}>🦋</div>
      <div className="butterfly" style={{ top: '60%', left: '70%', fontSize: '1.2rem', animationDuration: '8s' }}>🦋</div>
    </div>
  );
}

/**
 * Calligraphy Theme Background - GOLDEN ERA
 */
export function CalligraphyBackground() {
  const letters = useMemo(() => [...Array(12)].map((_, i) => ({
    char: ['ا', 'ب', 'ج', 'د', 'ه', 'و', 'ز', 'ح', 'ط', 'ي'][i % 10],
    style: {
      left: `${Math.random() * 90}%`,
      top: `${Math.random() * 90}%`,
      fontSize: `${2 + Math.random() * 4}rem`,
      animationDelay: `${Math.random() * 5}s`
    }
  })), []);

  return (
    <div className="theme-bg calligraphy-bg-premium">
      <div className="parchment-overlay-premium"></div>
      
      <div className="corner-decoration corner-tl">
          <svg viewBox="0 0 100 100">
              <path d="M10,10 L40,10 Q20,20 10,40 Z" fill="currentColor" />
              <circle cx="15" cy="15" r="3" fill="currentColor" />
          </svg>
      </div>
      <div className="corner-decoration corner-tr">
          <svg viewBox="0 0 100 100">
              <path d="M10,10 L40,10 Q20,20 10,40 Z" fill="currentColor" />
              <circle cx="15" cy="15" r="3" fill="currentColor" />
          </svg>
      </div>
      <div className="corner-decoration corner-br">
          <svg viewBox="0 0 100 100">
              <path d="M10,10 L40,10 Q20,20 10,40 Z" fill="currentColor" />
              <circle cx="15" cy="15" r="3" fill="currentColor" />
          </svg>
      </div>
      <div className="corner-decoration corner-bl">
          <svg viewBox="0 0 100 100">
              <path d="M10,10 L40,10 Q20,20 10,40 Z" fill="currentColor" />
              <circle cx="15" cy="15" r="3" fill="currentColor" />
          </svg>
      </div>

      {letters.map((letter, i) => (
        <div key={i} className="arabic-letter-float" style={letter.style}>
          {letter.char}
        </div>
      ))}
      
      <div className="ink-flow-line" style={{ top: '30%', left: '10%' }}></div>
      <div className="ink-flow-line" style={{ top: '70%', left: '30%' }}></div>
    </div>
  );
}

/**
 * NEW THEME: Desert Journey
 * Sand dunes, camels, sunset
 */
export function DesertBackground() {
  const camels = useMemo(() => [...Array(2)].map((_, i) => ({
    style: {
      left: `${(i + 1) * 30}%`,
      animationDelay: `${i * 2}s`
    }
  })), []);

  return (
    <div className="theme-bg desert-bg">
      <div className="desert-sky"></div>
      <div className="desert-sun"></div>
      
      <div className="dune dune-back"></div>
      <div className="dune dune-mid"></div>
      
      {camels.map((camel, i) => (
        <div key={i} className="camel-silhouette" style={camel.style}>
          🐪
        </div>
      ))}
      
      <div className="dune dune-front"></div>
      
      <div className="palm-tree" style={{ left: '10%' }}>🌴</div>
      <div className="palm-tree" style={{ left: '85%', transform: 'scale(0.8)' }}>🌴</div>
    </div>
  );
}

/**
 * NEW THEME: Ocean Voyage
 * Waves, ship, stars reflection
 */
export function OceanBackground() {
  return (
    <div className="theme-bg ocean-bg">
      <div className="ocean-sky">
        {[...Array(20)].map((_, i) => (
          <div key={i} className="star-small" style={{ left: `${Math.random()*100}%`, top: `${Math.random()*100}%` }}></div>
        ))}
      </div>
      
      <div className="moon-reflection"></div>
      
      <div className="wave wave-back"></div>
      <div className="ship-silhouette" style={{ left: '40%' }}>⛵</div>
      <div className="wave wave-mid"></div>
      <div className="wave wave-front"></div>
      
      <div className="fish" style={{ top: '80%', left: '20%' }}>🐟</div>
      <div className="fish" style={{ top: '85%', left: '70%', animationDelay: '2s' }}>🐠</div>
    </div>
  );
}

/**
 * Main Theme Background Router
 */
export function ThemeBackground({ themeId }) {
  switch (themeId) {
    case 'crescent-moon':
      return <CrescentMoonBackground />;
    case 'masjid':
      return <MasjidBackground />;
    case 'lantern':
      return <LanternBackground />;
    case 'geometric':
      return <GeometricBackground />;
    case 'garden':
      return <GardenBackground />;
    case 'calligraphy':
      return <CalligraphyBackground />;
    case 'desert':
      return <DesertBackground />;
    case 'ocean':
      return <OceanBackground />;
    default:
      return <CrescentMoonBackground />;
  }
}

export default ThemeBackground;
