import React, { useEffect, useState } from 'react';
import './Balloons.css';

/**
 * Balloon component
 */
const Balloon = ({ color, startLeft, delay, speed, scale }) => {
  return (
    <div 
      className={`balloon balloon-${color}`}
      style={{
        left: `${startLeft}%`,
        animationDuration: `${speed}s`,
        animationDelay: `${delay}s`,
        transform: `scale(${scale})`,
        borderBottomColor: 'inherit' // Ensures the knot gets the color
      }}
    >
      <div className="shine"></div>
    </div>
  );
};

/**
 * Balloons Celebration Component
 */
export function BalloonsCelebration({ autoFire = true, count = 30 }) {
  const [balloons, setBalloons] = useState([]);
  const colors = ['red', 'blue', 'yellow', 'green', 'purple', 'orange'];

  useEffect(() => {
    if (autoFire) {
      const newBalloons = Array.from({ length: count }).map((_, i) => ({
        id: i,
        color: colors[Math.floor(Math.random() * colors.length)],
        startLeft: Math.random() * 90 + 5, // 5% to 95% width
        delay: Math.random() * 2, // 0-2s start delay
        speed: 4 + Math.random() * 4, // 4-8s float duration
        scale: 0.8 + Math.random() * 0.4 // Size variation
      }));
      setBalloons(newBalloons);
    } else {
      setBalloons([]);
    }
  }, [autoFire, count]);

  if (!autoFire) return null;

  return (
    <div className="balloons-container">
      {balloons.map(b => (
        <Balloon 
          key={b.id}
          color={b.color}
          startLeft={b.startLeft}
          delay={b.delay}
          speed={b.speed}
          scale={b.scale}
        />
      ))}
    </div>
  );
}

export default BalloonsCelebration;
