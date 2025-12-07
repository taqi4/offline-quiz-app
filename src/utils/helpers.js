import { v4 as uuidv4 } from 'uuid';

/**
 * Generate a unique ID
 */
export function generateId() {
  return uuidv4();
}

/**
 * Create a new empty quiz
 */
export function createEmptyQuiz() {
  return {
    id: generateId(),
    name: '',
    hasTimer: false,
    timerSeconds: 30,
    createdAt: new Date().toISOString(),
    ageGroups: []
  };
}

/**
 * Create a new empty age group
 */
export function createEmptyAgeGroup(name = '') {
  return {
    id: generateId(),
    name: name,
    theme: 'crescent-moon',
    celebrationType: 'confetti',
    sets: [],
    roundRobinIndex: 0
  };
}

/**
 * Create a new empty question set
 */
export function createEmptyQuestionSet(name = '') {
  return {
    id: generateId(),
    name: name || 'Set A',
    questions: []
  };
}

/**
 * Create a new empty question
 */
export function createEmptyQuestion() {
  return {
    id: generateId(),
    text: '',
    options: ['', '', '', ''],
    correctIndex: 0
  };
}

/**
 * Get the next set name (A, B, C, ...)
 */
export function getNextSetName(existingSets) {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  const usedNames = new Set(existingSets.map(s => s.name));
  
  for (let i = 0; i < alphabet.length; i++) {
    const name = `Set ${alphabet[i]}`;
    if (!usedNames.has(name)) {
      return name;
    }
  }
  
  return `Set ${existingSets.length + 1}`;
}

/**
 * Format time in MM:SS
 */
export function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Shuffle an array (Fisher-Yates)
 */
export function shuffleArray(array) {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
}

/**
 * Calculate score from answers
 */
export function calculateScore(questions, answers) {
  let correct = 0;
  questions.forEach((q, index) => {
    if (answers[index] === q.correctIndex) {
      correct++;
    }
  });
  return {
    correct,
    total: questions.length,
    percentage: Math.round((correct / questions.length) * 100)
  };
}

/**
 * Get theme display info
 */
export const THEMES = {
  'crescent-moon': {
    id: 'crescent-moon',
    name: 'Crescent Moon & Stars',
    emoji: '🌙',
    colors: {
      primary: '#1a1a2e',
      secondary: '#FFD700',
      accent: '#4a4a8a'
    }
  },
  'masjid': {
    id: 'masjid',
    name: 'Masjid',
    emoji: '🕌',
    colors: {
      primary: '#0d5c3d',
      secondary: '#FFFFFF',
      accent: '#FFD700'
    }
  },
  'lantern': {
    id: 'lantern',
    name: 'Islamic Lanterns',
    emoji: '🏮',
    colors: {
      primary: '#2d1b2e',
      secondary: '#FFB347',
      accent: '#8B4513'
    }
  },
  'geometric': {
    id: 'geometric',
    name: 'Geometric Patterns',
    emoji: '✨',
    colors: {
      primary: '#0a3d62',
      secondary: '#00d2d3',
      accent: '#FFD700'
    }
  },
  'garden': {
    id: 'garden',
    name: 'Paradise Garden',
    emoji: '🌺',
    colors: {
      primary: '#1a472a',
      secondary: '#90EE90',
      accent: '#FF69B4'
    }
  },
  'calligraphy': {
    id: 'calligraphy',
    name: 'Arabic Calligraphy',
    emoji: '✒️',
    colors: {
      primary: '#2C1810',
      secondary: '#F5E6D3',
      accent: '#8B4513'
    }
  },
  'desert': {
    id: 'desert',
    name: 'Desert Journey',
    emoji: '🐪',
    colors: {
      primary: '#87CEEB',
      secondary: '#FDB813',
      accent: '#DAA520'
    }
  },

};

/**
 * Get celebration types
 */
export const CELEBRATION_TYPES = {
  'confetti': {
    id: 'confetti',
    name: 'Confetti',
    emoji: '🎊'
  },
  'fireworks': {
    id: 'fireworks',
    name: 'Fireworks',
    emoji: '🎆'
  },
  'balloons': {
    id: 'balloons',
    name: 'Balloons',
    emoji: '🎈'
  }
};

/**
 * Deep clone an object
 */
export function deepClone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

/**
 * Debounce function
 */
export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}
