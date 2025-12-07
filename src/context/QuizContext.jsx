import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { saveQuizzes, loadQuizzes, saveRoundRobinState, loadRoundRobinState } from '../utils/storage';
import { generateId } from '../utils/helpers';

// Initial state
const initialState = {
  quizzes: [],
  roundRobinState: {},
  loading: true,
  error: null
};

// Action types
const ACTIONS = {
  SET_QUIZZES: 'SET_QUIZZES',
  ADD_QUIZ: 'ADD_QUIZ',
  UPDATE_QUIZ: 'UPDATE_QUIZ',
  DELETE_QUIZ: 'DELETE_QUIZ',
  SET_ROUND_ROBIN: 'SET_ROUND_ROBIN',
  UPDATE_ROUND_ROBIN: 'UPDATE_ROUND_ROBIN',
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR'
};

// Reducer
function quizReducer(state, action) {
  switch (action.type) {
    case ACTIONS.SET_QUIZZES:
      return { ...state, quizzes: action.payload, loading: false };
    
    case ACTIONS.ADD_QUIZ:
      return { ...state, quizzes: [...state.quizzes, action.payload] };
    
    case ACTIONS.UPDATE_QUIZ:
      return {
        ...state,
        quizzes: state.quizzes.map(q =>
          q.id === action.payload.id ? action.payload : q
        )
      };
    
    case ACTIONS.DELETE_QUIZ:
      return {
        ...state,
        quizzes: state.quizzes.filter(q => q.id !== action.payload)
      };
    
    case ACTIONS.SET_ROUND_ROBIN:
      return { ...state, roundRobinState: action.payload };
    
    case ACTIONS.UPDATE_ROUND_ROBIN:
      return {
        ...state,
        roundRobinState: {
          ...state.roundRobinState,
          ...action.payload
        }
      };
    
    case ACTIONS.SET_LOADING:
      return { ...state, loading: action.payload };
    
    case ACTIONS.SET_ERROR:
      return { ...state, error: action.payload, loading: false };
    
    default:
      return state;
  }
}

// Context
const QuizContext = createContext(null);

// Provider component
export function QuizProvider({ children }) {
  const [state, dispatch] = useReducer(quizReducer, initialState);

  // Load data on mount
  useEffect(() => {
    try {
      const quizzes = loadQuizzes();
      const roundRobin = loadRoundRobinState();
      dispatch({ type: ACTIONS.SET_QUIZZES, payload: quizzes });
      dispatch({ type: ACTIONS.SET_ROUND_ROBIN, payload: roundRobin });
    } catch (error) {
      dispatch({ type: ACTIONS.SET_ERROR, payload: 'Failed to load data' });
    }
  }, []);

  // Save quizzes whenever they change
  useEffect(() => {
    if (!state.loading) {
      saveQuizzes(state.quizzes);
    }
  }, [state.quizzes, state.loading]);

  // Save round robin state whenever it changes
  useEffect(() => {
    if (!state.loading) {
      saveRoundRobinState(state.roundRobinState);
    }
  }, [state.roundRobinState, state.loading]);

  // Actions
  const actions = {
    addQuiz: (quiz) => {
      const newQuiz = {
        ...quiz,
        id: quiz.id || generateId(),
        createdAt: quiz.createdAt || new Date().toISOString()
      };
      dispatch({ type: ACTIONS.ADD_QUIZ, payload: newQuiz });
      return newQuiz;
    },

    updateQuiz: (quiz) => {
      dispatch({ type: ACTIONS.UPDATE_QUIZ, payload: quiz });
    },

    deleteQuiz: (quizId) => {
      dispatch({ type: ACTIONS.DELETE_QUIZ, payload: quizId });
    },

    getQuizById: (quizId) => {
      return state.quizzes.find(q => q.id === quizId);
    },

    getNextSetForAgeGroup: (quizId, ageGroupId) => {
      const quiz = state.quizzes.find(q => q.id === quizId);
      if (!quiz) return null;

      const ageGroup = quiz.ageGroups.find(ag => ag.id === ageGroupId);
      if (!ageGroup || ageGroup.sets.length === 0) return null;

      // Get current round robin index
      const key = `${quizId}_${ageGroupId}`;
      const currentIndex = state.roundRobinState[key] || 0;
      const setIndex = currentIndex % ageGroup.sets.length;

      return {
        set: ageGroup.sets[setIndex],
        setIndex,
        nextIndex: (currentIndex + 1) % ageGroup.sets.length
      };
    },

    advanceRoundRobin: (quizId, ageGroupId) => {
      const key = `${quizId}_${ageGroupId}`;
      const quiz = state.quizzes.find(q => q.id === quizId);
      if (!quiz) return;

      const ageGroup = quiz.ageGroups.find(ag => ag.id === ageGroupId);
      if (!ageGroup) return;

      const currentIndex = state.roundRobinState[key] || 0;
      const nextIndex = (currentIndex + 1) % ageGroup.sets.length;

      dispatch({
        type: ACTIONS.UPDATE_ROUND_ROBIN,
        payload: { [key]: nextIndex }
      });
    },

    importQuiz: (quiz) => {
      // Generate new ID to avoid conflicts
      const newQuiz = {
        ...quiz,
        id: generateId(),
        createdAt: new Date().toISOString()
      };
      dispatch({ type: ACTIONS.ADD_QUIZ, payload: newQuiz });
      return newQuiz;
    }
  };

  return (
    <QuizContext.Provider value={{ state, ...actions }}>
      {children}
    </QuizContext.Provider>
  );
}

// Hook to use quiz context
export function useQuiz() {
  const context = useContext(QuizContext);
  if (!context) {
    throw new Error('useQuiz must be used within a QuizProvider');
  }
  return context;
}
