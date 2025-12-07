import { useCallback, useRef } from 'react';

/**
 * Sound URLs - using royalty-free sounds from online sources
 * These are base64 encoded short sounds for reliability
 */

// Simple beep sounds generated with Web Audio API
const createAudioContext = () => {
  return new (window.AudioContext || window.webkitAudioContext)();
};

/**
 * Custom hook for playing sounds
 */
export function useSound() {
  const audioContextRef = useRef(null);
  const gainNodeRef = useRef(null);

  const getAudioContext = useCallback(() => {
    if (!audioContextRef.current) {
      audioContextRef.current = createAudioContext();
      gainNodeRef.current = audioContextRef.current.createGain();
      gainNodeRef.current.connect(audioContextRef.current.destination);
    }
    
    // Resume if suspended (needed due to browser autoplay policies)
    if (audioContextRef.current.state === 'suspended') {
      audioContextRef.current.resume();
    }
    
    return audioContextRef.current;
  }, []);

  // Play a tone with given frequency and duration
  const playTone = useCallback((frequency, duration, type = 'sine', volume = 0.3) => {
    try {
      const ctx = getAudioContext();
      const oscillator = ctx.createOscillator();
      const gainNode = ctx.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(ctx.destination);
      
      oscillator.type = type;
      oscillator.frequency.setValueAtTime(frequency, ctx.currentTime);
      
      gainNode.gain.setValueAtTime(volume, ctx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration);
      
      oscillator.start(ctx.currentTime);
      oscillator.stop(ctx.currentTime + duration);
    } catch (error) {
      console.warn('Sound playback failed:', error);
    }
  }, [getAudioContext]);

  // Play a chord (multiple frequencies)
  const playChord = useCallback((frequencies, duration, type = 'sine', volume = 0.2) => {
    frequencies.forEach((freq, i) => {
      setTimeout(() => playTone(freq, duration, type, volume), i * 50);
    });
  }, [playTone]);

  // Correct answer sound - Islamic phrases with fallback
  const playCorrect = useCallback(() => {
    const islamicSounds = ['mashallah.mp3', 'subhanallah.mp3'];
    const randomSound = islamicSounds[Math.floor(Math.random() * islamicSounds.length)];
    const audio = new Audio(`/sounds/${randomSound}`);
    
    // Perform standard play attempt
    const playPromise = audio.play();
    
    if (playPromise !== undefined) {
      playPromise.catch(error => {
        // Fallback to synthetic tones if file not found or playback failed
        const ctx = getAudioContext();
        [523.25, 659.25, 783.99].forEach((freq, i) => {
          setTimeout(() => {
            playTone(freq, 0.15, 'sine', 0.4);
          }, i * 100);
        });
      });
    }
  }, [getAudioContext, playTone]);

  // Wrong answer sound - descending tones
  const playWrong = useCallback(() => {
    playTone(300, 0.3, 'square', 0.2);
    setTimeout(() => playTone(200, 0.3, 'square', 0.2), 150);
  }, [playTone]);

  // Click sound - short blip
  const playClick = useCallback(() => {
    playTone(800, 0.05, 'sine', 0.2);
  }, [playTone]);

  // Tick sound for timer
  const playTick = useCallback(() => {
    playTone(1000, 0.05, 'sine', 0.15);
  }, [playTone]);

  // Warning tick (last seconds)
  const playWarningTick = useCallback(() => {
    playTone(600, 0.1, 'square', 0.25);
  }, [playTone]);

  // Celebration fanfare
  const playCelebration = useCallback(() => {
    const notes = [
      { freq: 523.25, delay: 0 },    // C5
      { freq: 659.25, delay: 150 },  // E5
      { freq: 783.99, delay: 300 },  // G5
      { freq: 1046.50, delay: 450 }, // C6
      { freq: 783.99, delay: 600 },  // G5
      { freq: 1046.50, delay: 750 }, // C6
    ];
    
    notes.forEach(({ freq, delay }) => {
      setTimeout(() => playTone(freq, 0.2, 'sine', 0.3), delay);
    });
  }, [playTone]);

  // Start game sound
  const playStart = useCallback(() => {
    const notes = [392, 523.25, 659.25]; // G4, C5, E5
    notes.forEach((freq, i) => {
      setTimeout(() => playTone(freq, 0.15, 'sine', 0.3), i * 150);
    });
  }, [playTone]);

  // Hover sound - subtle
  const playHover = useCallback(() => {
    playTone(600, 0.03, 'sine', 0.1);
  }, [playTone]);

  // Time running out warning
  const playTimeWarning = useCallback(() => {
    playChord([400, 500], 0.2, 'sawtooth', 0.15);
  }, [playChord]);

  return {
    playCorrect,
    playWrong,
    playClick,
    playTick,
    playWarningTick,
    playCelebration,
    playStart,
    playHover,
    playTimeWarning
  };
}

export default useSound;
