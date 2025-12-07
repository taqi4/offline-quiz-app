import React, { useState } from 'react';
import { useSound } from '../../hooks/useSound';
import { createEmptyQuestionSet, getNextSetName, THEMES, CELEBRATION_TYPES } from '../../utils/helpers';
import QuestionSetEditor from './QuestionSetEditor';
import { ThemeBackground } from '../Themes/ThemeBackgrounds';
import { getThemeStyle } from '../Themes/ThemeProvider';
import './AgeGroupEditor.css';

/**
 * Age Group Editor Component
 * Allows editing of age group details, theme, celebration type, and question sets
 */
export function AgeGroupEditor({ ageGroup, onSave, onBack }) {
  const { playClick } = useSound();
  const [editedAgeGroup, setEditedAgeGroup] = useState({ ...ageGroup });
  const [editingSetId, setEditingSetId] = useState(null);
  const [errors, setErrors] = useState({});

  // Update field
  const updateField = (field, value) => {
    setEditedAgeGroup(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  // Add new question set
  const addQuestionSet = () => {
    playClick();
    const newSet = createEmptyQuestionSet(getNextSetName(editedAgeGroup.sets));
    setEditedAgeGroup(prev => ({
      ...prev,
      sets: [...prev.sets, newSet]
    }));
    setEditingSetId(newSet.id);
  };

  // Update question set
  const updateQuestionSet = (updatedSet) => {
    setEditedAgeGroup(prev => ({
      ...prev,
      sets: prev.sets.map(set =>
        set.id === updatedSet.id ? updatedSet : set
      )
    }));
  };

  // Delete question set
  const deleteQuestionSet = (setId) => {
    playClick();
    setEditedAgeGroup(prev => ({
      ...prev,
      sets: prev.sets.filter(set => set.id !== setId)
    }));
  };

  // Validate and save
  const handleSave = () => {
    const newErrors = {};
    
    if (!editedAgeGroup.name.trim()) {
      newErrors.name = 'Age group name is required';
    }
    
    if (editedAgeGroup.sets.length === 0) {
      newErrors.sets = 'Add at least one question set';
    }
    
    for (const set of editedAgeGroup.sets) {
      if (set.questions.length === 0) {
        newErrors.sets = `"${set.name}" needs at least one question`;
        break;
      }
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    playClick();
    onSave(editedAgeGroup);
  };

  // Render theme option
  const renderThemeOption = (themeId, theme) => {
    const isSelected = editedAgeGroup.theme === themeId;
    return (
      <button
        key={themeId}
        className={`theme-option ${isSelected ? 'selected' : ''}`}
        onClick={() => {
          playClick();
          updateField('theme', themeId);
        }}
        style={isSelected ? getThemeStyle(themeId) : {}}
      >
        <span className="theme-emoji">{theme.emoji}</span>
        <span className="theme-name">{theme.name}</span>
      </button>
    );
  };

  // Render celebration option
  const renderCelebrationOption = (celebId, celeb) => {
    const isSelected = editedAgeGroup.celebrationType === celebId;
    return (
      <button
        key={celebId}
        className={`celebration-option ${isSelected ? 'selected' : ''}`}
        onClick={() => {
          playClick();
          updateField('celebrationType', celebId);
        }}
      >
        <span className="celeb-emoji">{celeb.emoji}</span>
        <span className="celeb-name">{celeb.name}</span>
      </button>
    );
  };

  // If editing a question set, show the set editor
  if (editingSetId) {
    const questionSet = editedAgeGroup.sets.find(s => s.id === editingSetId);
    if (questionSet) {
      return (
        <QuestionSetEditor
          questionSet={questionSet}
          theme={editedAgeGroup.theme}
          onSave={(updated) => {
            updateQuestionSet(updated);
            setEditingSetId(null);
          }}
          onBack={() => setEditingSetId(null)}
        />
      );
    }
  }

  const themeStyle = getThemeStyle(editedAgeGroup.theme);

  return (
    <div className="age-group-editor" style={themeStyle}>
      <ThemeBackground themeId={editedAgeGroup.theme} />
      
      <div className="editor-container">
        {/* Header */}
        <header className="editor-header">
          <button className="back-button" onClick={onBack}>
            ← Back to Quiz
          </button>
          <h1>Edit Age Group</h1>
        </header>

        {/* Age Group Name */}
        <section className="editor-section">
          <h2>Age Group Name</h2>
          <div className="form-group">
            <input
              type="text"
              value={editedAgeGroup.name}
              onChange={(e) => updateField('name', e.target.value)}
              placeholder="e.g., 5-7 Years, Kids, Adults"
              className={errors.name ? 'error' : ''}
            />
            {errors.name && <span className="error-text">{errors.name}</span>}
          </div>
        </section>

        {/* Theme Selection */}
        <section className="editor-section">
          <h2>🎨 Choose Theme</h2>
          <p className="section-desc">Select a visual theme for this age group</p>
          <div className="themes-grid">
            {Object.entries(THEMES).map(([id, theme]) => renderThemeOption(id, theme))}
          </div>
        </section>

        {/* Celebration Type */}
        <section className="editor-section">
          <h2>🎉 Celebration Type</h2>
          <p className="section-desc">Choose how to celebrate correct answers</p>
          <div className="celebrations-grid">
            {Object.entries(CELEBRATION_TYPES).map(([id, celeb]) => 
              renderCelebrationOption(id, celeb)
            )}
          </div>
        </section>

        {/* Question Sets */}
        <section className="editor-section">
          <h2>📝 Question Sets</h2>
          <p className="section-desc">Create sets of questions (e.g., Set A, Set B)</p>
          
          {errors.sets && <div className="error-banner">{errors.sets}</div>}
          
          <div className="sets-list">
            {editedAgeGroup.sets.map((set) => (
              <div key={set.id} className="set-card">
                <div className="set-info">
                  <h3>{set.name}</h3>
                  <span className="set-count">{set.questions.length} questions</span>
                </div>
                <div className="set-actions">
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => {
                      playClick();
                      setEditingSetId(set.id);
                    }}
                  >
                    Edit
                  </button>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => deleteQuestionSet(set.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
            
            <button className="add-set-btn" onClick={addQuestionSet}>
              <span className="add-icon">+</span>
              <span>Add Question Set</span>
            </button>
          </div>
        </section>

        {/* Actions */}
        <div className="editor-actions">
          <button className="btn btn-secondary" onClick={onBack}>
            Cancel
          </button>
          <button className="btn btn-success btn-large" onClick={handleSave}>
            Save Age Group ✓
          </button>
        </div>
      </div>
    </div>
  );
}

export default AgeGroupEditor;
