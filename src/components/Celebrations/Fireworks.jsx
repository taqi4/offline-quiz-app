import React, { useEffect, useRef, useCallback } from 'react';
import './Fireworks.css';

/**
 * Fireworks celebration using canvas
 */
export function useFireworks() {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const particlesRef = useRef([]);

  const createParticle = useCallback((x, y, color) => {
    const angle = Math.random() * Math.PI * 2;
    const speed = Math.random() * 5 + 2;
    return {
      x,
      y,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      life: 1,
      color,
      size: Math.random() * 3 + 1
    };
  }, []);

  const createFirework = useCallback((canvas) => {
    const colors = ['#FFD700', '#FF6B6B', '#4ECDC4', '#9B59B6', '#00A86B', '#FF69B4'];
    const x = Math.random() * canvas.width;
    const y = Math.random() * canvas.height * 0.5 + 50;
    const color = colors[Math.floor(Math.random() * colors.length)];

    const particles = [];
    for (let i = 0; i < 50; i++) {
      particles.push(createParticle(x, y, color));
    }
    return particles;
  }, [createParticle]);

  const startFireworks = useCallback((duration = 3000) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const startTime = Date.now();
    let lastFirework = 0;

    const animate = () => {
      const elapsed = Date.now() - startTime;
      
      if (elapsed > duration) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particlesRef.current = [];
        return;
      }

      // Add new firework periodically
      if (Date.now() - lastFirework > 300) {
        particlesRef.current.push(...createFirework(canvas));
        lastFirework = Date.now();
      }

      // Clear with fade effect
      ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Update and draw particles
      particlesRef.current = particlesRef.current.filter(p => {
        p.x += p.vx;
        p.y += p.vy;
        p.vx *= 0.96; // air resistance
        p.vy *= 0.96; // air resistance
        p.vy += 0.08; // gravity
        p.life -= 0.012;

        if (p.life <= 0) return false;

        ctx.beginPath();
        // Sparkle effect
        if (Math.random() < 0.05) {
          ctx.arc(p.x, p.y, p.size * 1.5, 0, Math.PI * 2);
          ctx.fillStyle = '#ffffff';
        } else {
          ctx.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2);
          ctx.fillStyle = p.color;
        }
        
        ctx.globalAlpha = p.life;
        ctx.fill();
        ctx.globalAlpha = 1;

        return true;
      });

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [createFirework]);

  const stopFireworks = useCallback(() => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
    particlesRef.current = [];
    if (canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d');
      ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    }
  }, []);

  return { canvasRef, startFireworks, stopFireworks };
}

/**
 * Fireworks canvas component
 */
export function FireworksCanvas({ show = false, duration = 3000 }) {
  const { canvasRef, startFireworks, stopFireworks } = useFireworks();

  useEffect(() => {
    if (show) {
      startFireworks(duration);
    } else {
      stopFireworks();
    }

    return () => stopFireworks();
  }, [show, duration, startFireworks, stopFireworks]);

  if (!show) return null;

  return (
    <canvas
      ref={canvasRef}
      className="fireworks-canvas"
    />
  );
}

/**
 * CSS-based fireworks (backup for performance)
 */
export function CSSFireworks({ show = false }) {
  if (!show) return null;

  return (
    <div className="css-fireworks">
      {[...Array(10)].map((_, i) => (
        <div
          key={i}
          className="firework"
          style={{
            left: `${10 + Math.random() * 80}%`,
            top: `${10 + Math.random() * 40}%`,
            animationDelay: `${Math.random() * 2}s`
          }}
        >
          {[...Array(12)].map((_, j) => (
            <div
              key={j}
              className="spark"
              style={{
                transform: `rotate(${j * 30}deg)`,
                '--spark-color': ['#FFD700', '#FF6B6B', '#4ECDC4', '#9B59B6'][j % 4]
              }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

/**
 * Combined fireworks celebration component
 */
export function FireworksCelebration({ autoFire = true, duration = 3000 }) {
  return (
    <>
      <FireworksCanvas show={autoFire} duration={duration} />
      <CSSFireworks show={autoFire} />
    </>
  );
}

export default FireworksCelebration;
