/**
 * LocalStorage utility with chunking support
 * Handles large data by splitting into multiple keys to avoid 5MB limit
 */

const CHUNK_SIZE = 1024 * 1024 * 2; // 2MB per chunk (safe margin)
const STORAGE_PREFIX = 'jashn_quiz_';
const CHUNK_PREFIX = `${STORAGE_PREFIX}chunk_`;
const META_KEY = `${STORAGE_PREFIX}meta`;

/**
 * Get metadata about stored chunks
 */
function getMeta() {
  try {
    const meta = localStorage.getItem(META_KEY);
    return meta ? JSON.parse(meta) : { chunkCount: 0, keys: [] };
  } catch {
    return { chunkCount: 0, keys: [] };
  }
}

/**
 * Save metadata
 */
function saveMeta(meta) {
  localStorage.setItem(META_KEY, JSON.stringify(meta));
}

/**
 * Clear all quiz-related data from localStorage
 */
export function clearAllData() {
  const meta = getMeta();
  meta.keys.forEach(key => {
    localStorage.removeItem(key);
  });
  localStorage.removeItem(META_KEY);
}

/**
 * Save data to localStorage with automatic chunking
 * @param {string} key - The key to save under
 * @param {any} data - The data to save (will be JSON stringified)
 */
export function saveData(key, data) {
  try {
    const jsonString = JSON.stringify(data);
    const fullKey = `${STORAGE_PREFIX}${key}`;
    
    // If data is small enough, save directly
    if (jsonString.length < CHUNK_SIZE) {
      localStorage.setItem(fullKey, jsonString);
      
      // Update meta
      const meta = getMeta();
      if (!meta.keys.includes(fullKey)) {
        meta.keys.push(fullKey);
        saveMeta(meta);
      }
      return true;
    }
    
    // Data is large, need to chunk
    const chunks = [];
    for (let i = 0; i < jsonString.length; i += CHUNK_SIZE) {
      chunks.push(jsonString.slice(i, i + CHUNK_SIZE));
    }
    
    // Save each chunk
    const chunkKeys = [];
    chunks.forEach((chunk, index) => {
      const chunkKey = `${CHUNK_PREFIX}${key}_${index}`;
      localStorage.setItem(chunkKey, chunk);
      chunkKeys.push(chunkKey);
    });
    
    // Save chunk metadata for this key
    const chunkMeta = {
      isChunked: true,
      chunkCount: chunks.length,
      chunkKeys: chunkKeys
    };
    localStorage.setItem(fullKey, JSON.stringify(chunkMeta));
    
    // Update global meta
    const meta = getMeta();
    const allKeys = [fullKey, ...chunkKeys];
    allKeys.forEach(k => {
      if (!meta.keys.includes(k)) {
        meta.keys.push(k);
      }
    });
    saveMeta(meta);
    
    return true;
  } catch (error) {
    console.error('Error saving data to localStorage:', error);
    return false;
  }
}

/**
 * Load data from localStorage, handling chunks automatically
 * @param {string} key - The key to load
 * @param {any} defaultValue - Default value if key doesn't exist
 * @returns {any} The parsed data or default value
 */
export function loadData(key, defaultValue = null) {
  try {
    const fullKey = `${STORAGE_PREFIX}${key}`;
    const stored = localStorage.getItem(fullKey);
    
    if (!stored) {
      return defaultValue;
    }
    
    const parsed = JSON.parse(stored);
    
    // Check if this is chunked data
    if (parsed && parsed.isChunked) {
      // Reconstruct from chunks
      let fullString = '';
      for (const chunkKey of parsed.chunkKeys) {
        const chunk = localStorage.getItem(chunkKey);
        if (chunk) {
          fullString += chunk;
        } else {
          console.error('Missing chunk:', chunkKey);
          return defaultValue;
        }
      }
      return JSON.parse(fullString);
    }
    
    // Not chunked, return directly
    return parsed;
  } catch (error) {
    console.error('Error loading data from localStorage:', error);
    return defaultValue;
  }
}

/**
 * Remove data from localStorage
 * @param {string} key - The key to remove
 */
export function removeData(key) {
  try {
    const fullKey = `${STORAGE_PREFIX}${key}`;
    const stored = localStorage.getItem(fullKey);
    
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        // If chunked, remove all chunks
        if (parsed && parsed.isChunked) {
          parsed.chunkKeys.forEach(chunkKey => {
            localStorage.removeItem(chunkKey);
          });
        }
      } catch {
        // Not JSON, just remove the key
      }
      localStorage.removeItem(fullKey);
    }
    
    // Update meta
    const meta = getMeta();
    meta.keys = meta.keys.filter(k => !k.startsWith(fullKey));
    saveMeta(meta);
    
    return true;
  } catch (error) {
    console.error('Error removing data from localStorage:', error);
    return false;
  }
}

/**
 * Check available localStorage space (approximate)
 * @returns {object} { used, total, available } in bytes
 */
export function getStorageInfo() {
  let used = 0;
  
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    const value = localStorage.getItem(key);
    used += (key.length + value.length) * 2; // UTF-16 = 2 bytes per char
  }
  
  // Most browsers allow 5-10MB
  const total = 5 * 1024 * 1024; // Assume 5MB
  
  return {
    used,
    total,
    available: total - used,
    usedMB: (used / (1024 * 1024)).toFixed(2),
    percentUsed: ((used / total) * 100).toFixed(1)
  };
}

/**
 * Save quizzes to localStorage
 * @param {Array} quizzes - Array of quiz objects
 */
export function saveQuizzes(quizzes) {
  return saveData('quizzes', quizzes);
}

/**
 * Load quizzes from localStorage
 * @returns {Array} Array of quiz objects
 */
export function loadQuizzes() {
  return loadData('quizzes', []);
}

/**
 * Save round-robin state
 * @param {object} state - Round robin state { quizId: { ageGroupId: nextSetIndex } }
 */
export function saveRoundRobinState(state) {
  return saveData('roundRobin', state);
}

/**
 * Load round-robin state
 * @returns {object} Round robin state
 */
export function loadRoundRobinState() {
  return loadData('roundRobin', {});
}
