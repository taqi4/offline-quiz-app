import React, { useState, useEffect } from 'react';
import { useQuiz } from '../../context/QuizContext';
import { useSound } from '../../hooks/useSound';
import { createEmptyQuiz, createEmptyAgeGroup, THEMES, CELEBRATION_TYPES } from '../../utils/helpers';
import AgeGroupEditor from './AgeGroupEditor';
import { CrescentMoonBackground } from '../Themes/ThemeBackgrounds';
import './QuizCreator.css';

/**
 * Quiz Creator Component
 * Multi-step wizard for creating quizzes
 */
export function QuizCreator({ onBack, editQuizId = null }) {
  const { state, addQuiz, updateQuiz, getQuizById } = useQuiz();
  const { playClick, playCorrect } = useSound();
  
  const [step, setStep] = useState(1);
  const [quiz, setQuiz] = useState(createEmptyQuiz());
  const [editingAgeGroupId, setEditingAgeGroupId] = useState(null);
  const [errors, setErrors] = useState({});

  // Load existing quiz for editing
  useEffect(() => {
    if (editQuizId) {
      const existingQuiz = getQuizById(editQuizId);
      if (existingQuiz) {
        setQuiz(existingQuiz);
      }
    }
  }, [editQuizId, getQuizById]);

  // Update quiz field
  const updateField = (field, value) => {
    setQuiz(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  // Add new age group
  const addAgeGroup = () => {
    playClick();
    const newAgeGroup = createEmptyAgeGroup(`Age Group ${quiz.ageGroups.length + 1}`);
    setQuiz(prev => ({
      ...prev,
      ageGroups: [...prev.ageGroups, newAgeGroup]
    }));
    setEditingAgeGroupId(newAgeGroup.id);
  };

  // Update age group
  const updateAgeGroup = (updatedAgeGroup) => {
    setQuiz(prev => ({
      ...prev,
      ageGroups: prev.ageGroups.map(ag =>
        ag.id === updatedAgeGroup.id ? updatedAgeGroup : ag
      )
    }));
  };

  // Delete age group
  const deleteAgeGroup = (ageGroupId) => {
    playClick();
    setQuiz(prev => ({
      ...prev,
      ageGroups: prev.ageGroups.filter(ag => ag.id !== ageGroupId)
    }));
    if (editingAgeGroupId === ageGroupId) {
      setEditingAgeGroupId(null);
    }
  };

  // Validate step 1
  const validateStep1 = () => {
    const newErrors = {};
    if (!quiz.name.trim()) {
      newErrors.name = 'Quiz name is required';
    }
    if (quiz.hasTimer && (!quiz.timerSeconds || quiz.timerSeconds < 5)) {
      newErrors.timerSeconds = 'Timer must be at least 5 seconds';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Validate step 2
  const validateStep2 = () => {
    if (quiz.ageGroups.length === 0) {
      setErrors({ ageGroups: 'Add at least one age group' });
      return false;
    }
    
    for (const ag of quiz.ageGroups) {
      if (!ag.name.trim()) {
        setErrors({ ageGroups: `Age group name is required` });
        return false;
      }
      if (ag.sets.length === 0) {
        setErrors({ ageGroups: `"${ag.name}" needs at least one question set` });
        return false;
      }
      for (const set of ag.sets) {
        if (set.questions.length === 0) {
          setErrors({ ageGroups: `"${ag.name}" > "${set.name}" needs at least one question` });
          return false;
        }
      }
    }
    
    setErrors({});
    return true;
  };

  // Move to next step
  const nextStep = () => {
    playClick();
    if (step === 1 && validateStep1()) {
      setStep(2);
    }
  };

  // Move to previous step
  const prevStep = () => {
    playClick();
    if (step > 1) {
      setStep(step - 1);
    } else {
      onBack();
    }
  };

  // Save quiz
  const saveQuiz = () => {
    if (!validateStep2()) return;
    
    playCorrect();
    
    if (editQuizId) {
      updateQuiz(quiz);
    } else {
      addQuiz(quiz);
    }
    
    onBack();
  };

  // Render age group card
  const renderAgeGroupCard = (ageGroup) => {
    const theme = THEMES[ageGroup.theme];
    const celebration = CELEBRATION_TYPES[ageGroup.celebrationType];
    const questionCount = ageGroup.sets.reduce((sum, set) => sum + set.questions.length, 0);
    
    return (
      <div key={ageGroup.id} className="age-group-card">
        <div className="ag-card-header">
          <span className="ag-theme-icon">{theme?.emoji}</span>
          <h3 className="ag-name">{ageGroup.name || 'Unnamed Group'}</h3>
        </div>
        <div className="ag-card-stats">
          <span>{ageGroup.sets.length} Sets</span>
          <span>•</span>
          <span>{questionCount} Questions</span>
          <span>•</span>
          <span>{celebration?.emoji} {celebration?.name}</span>
        </div>
        <div className="ag-card-actions">
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => {
              playClick();
              setEditingAgeGroupId(ageGroup.id);
            }}
          >
            Edit
          </button>
          <button
            className="btn btn-danger btn-sm"
            onClick={() => deleteAgeGroup(ageGroup.id)}
          >
            Delete
          </button>
        </div>
      </div>
    );
  };

  // If editing an age group, show the editor
  if (editingAgeGroupId) {
    const ageGroup = quiz.ageGroups.find(ag => ag.id === editingAgeGroupId);
    if (ageGroup) {
      return (
        <AgeGroupEditor
          ageGroup={ageGroup}
          onSave={(updated) => {
            updateAgeGroup(updated);
            setEditingAgeGroupId(null);
          }}
          onBack={() => setEditingAgeGroupId(null)}
        />
      );
    }
  }

  return (
    <div className="quiz-creator">
      <CrescentMoonBackground />
      
      <div className="creator-container">
        {/* Header */}
        <header className="creator-header">
          <button className="back-button" onClick={prevStep}>
            ← {step === 1 ? 'Home' : 'Back'}
          </button>
          <h1>{editQuizId ? 'Edit Quiz' : 'Create Quiz'}</h1>
          <div className="step-indicator">
            <span className={`step ${step >= 1 ? 'active' : ''}`}>1</span>
            <span className="step-line"></span>
            <span className={`step ${step >= 2 ? 'active' : ''}`}>2</span>
          </div>
        </header>

        {/* Step 1: Basic Info */}
        {step === 1 && (
          <div className="creator-step animate-fade-in">
            <h2>Quiz Details</h2>
            <p className="step-desc">Set up the basic information for your quiz</p>
            
            <div className="form-group">
              <label htmlFor="quiz-name">Quiz Name *</label>
              <input
                id="quiz-name"
                type="text"
                value={quiz.name}
                onChange={(e) => updateField('name', e.target.value)}
                placeholder="e.g., Islamic History Quiz"
                className={errors.name ? 'error' : ''}
              />
              {errors.name && <span className="error-text">{errors.name}</span>}
            </div>

            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={quiz.hasTimer}
                  onChange={(e) => updateField('hasTimer', e.target.checked)}
                />
                <span className="checkbox-custom"></span>
                Enable Timer ⏱️
              </label>
            </div>

            {quiz.hasTimer && (
              <div className="form-group animate-fade-in">
                <label htmlFor="timer-seconds">Time per Question (seconds)</label>
                <input
                  id="timer-seconds"
                  type="number"
                  value={quiz.timerSeconds || 30}
                  onChange={(e) => updateField('timerSeconds', parseInt(e.target.value) || 30)}
                  min="5"
                  max="300"
                  className={errors.timerSeconds ? 'error' : ''}
                />
                {errors.timerSeconds && <span className="error-text">{errors.timerSeconds}</span>}
              </div>
            )}

            <div className="step-actions">
              <button className="btn btn-primary btn-large" onClick={nextStep}>
                Next: Add Age Groups →
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Age Groups */}
        {step === 2 && (
          <div className="creator-step animate-fade-in">
            <h2>Age Groups</h2>
            <p className="step-desc">
              Create age groups with their own themes and question sets
            </p>
            
            {errors.ageGroups && (
              <div className="error-banner">{errors.ageGroups}</div>
            )}

            <div className="age-groups-list">
              {quiz.ageGroups.map(renderAgeGroupCard)}
              
              <button className="add-age-group-btn" onClick={addAgeGroup}>
                <span className="add-icon">+</span>
                <span>Add Age Group</span>
              </button>
            </div>

            <div className="step-actions">
              <button className="btn btn-secondary" onClick={prevStep}>
                ← Back
              </button>
              <button 
                className="btn btn-success btn-large" 
                onClick={saveQuiz}
                disabled={quiz.ageGroups.length === 0}
              >
                {editQuizId ? 'Save Changes' : 'Create Quiz'} ✓
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default QuizCreator;
