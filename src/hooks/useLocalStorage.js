import { useState, useEffect, useCallback } from 'react';
import { loadData, saveData } from '../utils/storage';

/**
 * Custom hook for localStorage with automatic sync
 * @param {string} key - Storage key
 * @param {any} initialValue - Default value
 */
export function useLocalStorage(key, initialValue) {
  // State to store our value
  const [storedValue, setStoredValue] = useState(() => {
    try {
      return loadData(key, initialValue);
    } catch (error) {
      console.error('Error reading localStorage:', error);
      return initialValue;
    }
  });

  // Return a wrapped version of useState's setter function that persists the new value
  const setValue = useCallback((value) => {
    try {
      // Allow value to be a function so we have same API as useState
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      
      setStoredValue(valueToStore);
      saveData(key, valueToStore);
    } catch (error) {
      console.error('Error saving to localStorage:', error);
    }
  }, [key, storedValue]);

  // Listen for changes in other tabs/windows
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === `jashn_quiz_${key}`) {
        try {
          setStoredValue(JSON.parse(e.newValue));
        } catch {
          // Ignore parse errors
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [key]);

  return [storedValue, setValue];
}

export default useLocalStorage;
