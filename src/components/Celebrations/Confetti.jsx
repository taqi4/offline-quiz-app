import { useEffect, useCallback } from 'react';
import confetti from 'canvas-confetti';

/**
 * Confetti celebration component
 */
export function useConfetti() {
  const fireConfetti = useCallback((options = {}) => {
    const defaults = {
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 },
      colors: ['#FFD700', '#FFA500', '#00A86B', '#FF69B4', '#00CED1', '#FF6B6B']
    };

    confetti({
      ...defaults,
      ...options
    });
  }, []);

  // Burst from sides
  const fireSideBurst = useCallback(() => {
    const end = Date.now() + 1000;

    const frame = () => {
      confetti({
        particleCount: 3,
        angle: 60,
        spread: 55,
        origin: { x: 0, y: 0.6 },
        colors: ['#FFD700', '#FFA500', '#00A86B']
      });
      confetti({
        particleCount: 3,
        angle: 120,
        spread: 55,
        origin: { x: 1, y: 0.6 },
        colors: ['#FFD700', '#FFA500', '#00A86B']
      });

      if (Date.now() < end) {
        requestAnimationFrame(frame);
      }
    };

    frame();
  }, []);

  // School pride style
  const fireSchoolPride = useCallback(() => {
    const end = Date.now() + 3000;
    const colors = ['#FFD700', '#00A86B', '#FFFFFF'];

    const frame = () => {
      confetti({
        particleCount: 2,
        angle: 60,
        spread: 55,
        origin: { x: 0 },
        colors: colors
      });
      confetti({
        particleCount: 2,
        angle: 120,
        spread: 55,
        origin: { x: 1 },
        colors: colors
      });

      if (Date.now() < end) {
        requestAnimationFrame(frame);
      }
    };

    frame();
  }, []);

  // Stars confetti
  const fireStars = useCallback(() => {
    const defaults = {
      spread: 360,
      ticks: 100,
      gravity: 0,
      decay: 0.94,
      startVelocity: 30,
      colors: ['#FFD700', '#FFA500', '#FFE4B5']
    };

    function shoot() {
      confetti({
        ...defaults,
        particleCount: 40,
        scalar: 1.2,
        shapes: ['star']
      });

      confetti({
        ...defaults,
        particleCount: 10,
        scalar: 0.75,
        shapes: ['circle']
      });
    }

    setTimeout(shoot, 0);
    setTimeout(shoot, 100);
    setTimeout(shoot, 200);
  }, []);

  // Celebration burst for correct answers
  const fireCorrectAnswer = useCallback(() => {
    confetti({
      particleCount: 30,
      spread: 60,
      origin: { y: 0.7 },
      colors: ['#4CAF50', '#8BC34A', '#CDDC39'],
      ticks: 60
    });
  }, []);

  // Big celebration for end of quiz
  const fireBigCelebration = useCallback(() => {
    const duration = 3000;
    const animationEnd = Date.now() + duration;

    const randomInRange = (min, max) => Math.random() * (max - min) + min;

    const interval = setInterval(() => {
      const timeLeft = animationEnd - Date.now();

      if (timeLeft <= 0) {
        clearInterval(interval);
        return;
      }

      const particleCount = 50 * (timeLeft / duration);

      confetti({
        particleCount,
        startVelocity: 30,
        spread: 360,
        origin: {
          x: randomInRange(0.1, 0.9),
          y: Math.random() - 0.2
        },
        colors: ['#FFD700', '#FFA500', '#00A86B', '#FF69B4', '#00CED1', '#9B59B6']
      });
    }, 250);

    return () => clearInterval(interval);
  }, []);

  // Mini fireworks for correct answers - Premium version
  const fireMiniFireworks = useCallback(() => {
    const colors = ['#FF6B6B', '#FFD700', '#FF69B4', '#00CED1', '#ffffff'];
    
    // Main burst
    confetti({
      particleCount: 40,
      spread: 60,
      startVelocity: 45,
      gravity: 0.8,
      origin: { y: 0.8 },
      colors: colors,
      shapes: ['circle', 'star'],
      scalar: 0.9,
      decay: 0.9,
      drift: 0,
      ticks: 100
    });
    
    // Secondary burst (sparkles)
    setTimeout(() => {
       confetti({
        particleCount: 20,
        spread: 100,
        startVelocity: 30,
        gravity: 0.6,
        origin: { y: 0.75 },
        colors: ['#FFD700', '#ffffff'],
        shapes: ['square'],
        scalar: 0.6,
        decay: 0.92,
        ticks: 80
      });
    }, 100);
  }, []);

  // Mini balloons effect for correct answers - Premium version
  const fireMiniBalloons = useCallback(() => {
    const balloonColors = ['#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3', '#A8D0E6', '#F7D794'];
    
    // Group 1: Fast floaters
    confetti({
      particleCount: 10,
      spread: 40,
      startVelocity: 35,
      gravity: -0.4, 
      origin: { y: 1 },
      colors: balloonColors,
      shapes: ['circle'],
      scalar: 1.8,
      ticks: 200,
      drift: 0.5
    });
    
    // Group 2: Slow drifters
    confetti({
      particleCount: 15,
      spread: 90,
      startVelocity: 25,
      gravity: -0.2,
      origin: { y: 1 },
      colors: balloonColors,
      shapes: ['circle'],
      scalar: 1.4,
      ticks: 200,
      drift: -0.5
    });
  }, []);

  return {
    fireConfetti,
    fireSideBurst,
    fireSchoolPride,
    fireStars,
    fireCorrectAnswer,
    fireBigCelebration,
    fireMiniFireworks,
    fireMiniBalloons
  };
}

/**
 * Confetti celebration on mount
 */
export function ConfettiCelebration({ autoFire = true, type = 'big' }) {
  const { fireBigCelebration, fireStars, fireSchoolPride } = useConfetti();

  useEffect(() => {
    if (autoFire) {
      switch (type) {
        case 'stars':
          fireStars();
          break;
        case 'pride':
          fireSchoolPride();
          break;
        case 'big':
        default:
          fireBigCelebration();
          break;
      }
    }
  }, [autoFire, type, fireBigCelebration, fireStars, fireSchoolPride]);

  return null; // This component just triggers the effect
}

export default ConfettiCelebration;
