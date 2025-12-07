import React, { useState } from 'react';
import { useSound } from '../../hooks/useSound';
import { deepClone } from '../../utils/helpers';
import { ThemeBackground } from '../Themes/ThemeBackgrounds';
import { getThemeStyle } from '../Themes/ThemeProvider';
import './QuestionEditor.css';

/**
 * Question Editor Component
 * Edit a single MCQ question with 4 options
 */
export function QuestionEditor({ question, questionNumber, theme, onSave, onBack }) {
  const { playClick, playCorrect } = useSound();
  const [editedQuestion, setEditedQuestion] = useState(deepClone(question));
  const [errors, setErrors] = useState({});

  // Update question text
  const updateText = (text) => {
    setEditedQuestion(prev => ({ ...prev, text }));
    if (errors.text) {
      setErrors(prev => ({ ...prev, text: null }));
    }
  };

  // Update option
  const updateOption = (index, value) => {
    setEditedQuestion(prev => ({
      ...prev,
      options: prev.options.map((opt, i) => i === index ? value : opt)
    }));
    if (errors.options) {
      setErrors(prev => ({ ...prev, options: null }));
    }
  };

  // Set correct answer
  const setCorrectAnswer = (index) => {
    playClick();
    setEditedQuestion(prev => ({ ...prev, correctIndex: index }));
  };

  // Validate and save
  const handleSave = () => {
    const newErrors = {};
    
    if (!editedQuestion.text.trim()) {
      newErrors.text = 'Question text is required';
    }
    
    const filledOptions = editedQuestion.options.filter(o => o.trim() !== '');
    if (filledOptions.length < 2) {
      newErrors.options = 'At least 2 options are required';
    }
    
    // Check if correct answer has text
    if (!editedQuestion.options[editedQuestion.correctIndex]?.trim()) {
      newErrors.options = 'The correct answer option must have text';
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    playCorrect();
    onSave(editedQuestion);
  };

  const themeStyle = getThemeStyle(theme);
  const optionLabels = ['A', 'B', 'C', 'D'];

  return (
    <div className="question-editor" style={themeStyle}>
      <ThemeBackground themeId={theme} />
      
      <div className="q-editor-container">
        {/* Header */}
        <header className="q-editor-header">
          <button className="back-button" onClick={onBack}>
            ← Back to Set
          </button>
          <h1>Question {questionNumber}</h1>
        </header>

        {/* Question Text */}
        <section className="q-editor-section">
          <h2>Question</h2>
          <div className="form-group">
            <textarea
              value={editedQuestion.text}
              onChange={(e) => updateText(e.target.value)}
              placeholder="Enter your question here..."
              rows={3}
              className={errors.text ? 'error' : ''}
            />
            {errors.text && <span className="error-text">{errors.text}</span>}
          </div>
        </section>

        {/* Options */}
        <section className="q-editor-section">
          <h2>Answer Options</h2>
          <p className="section-desc">Enter 4 options and select the correct one</p>
          
          {errors.options && <div className="error-banner">{errors.options}</div>}
          
          <div className="options-list">
            {editedQuestion.options.map((option, index) => (
              <div 
                key={index} 
                className={`option-row ${editedQuestion.correctIndex === index ? 'correct' : ''}`}
              >
                <button
                  className={`option-selector ${editedQuestion.correctIndex === index ? 'selected' : ''}`}
                  onClick={() => setCorrectAnswer(index)}
                  title={editedQuestion.correctIndex === index ? 'Correct answer' : 'Click to mark as correct'}
                >
                  <span className="option-label">{optionLabels[index]}</span>
                  {editedQuestion.correctIndex === index && (
                    <span className="correct-badge">✓</span>
                  )}
                </button>
                <input
                  type="text"
                  value={option}
                  onChange={(e) => updateOption(index, e.target.value)}
                  placeholder={`Option ${optionLabels[index]}`}
                  className="option-input"
                />
              </div>
            ))}
          </div>
          
          <p className="options-hint">
            💡 Click the letter button to mark it as the correct answer
          </p>
        </section>

        {/* Preview */}
        <section className="q-editor-section preview-section">
          <h2>Preview</h2>
          <div className="question-preview">
            <div className="preview-question">
              {editedQuestion.text || 'Your question will appear here...'}
            </div>
            <div className="preview-options">
              {editedQuestion.options.map((option, index) => (
                <div 
                  key={index}
                  className={`preview-option ${editedQuestion.correctIndex === index ? 'correct' : ''}`}
                >
                  <span className="preview-label">{optionLabels[index]}</span>
                  <span className="preview-text">
                    {option || `Option ${optionLabels[index]}`}
                  </span>
                  {editedQuestion.correctIndex === index && (
                    <span className="preview-correct">✓</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Actions */}
        <div className="q-editor-actions">
          <button className="btn btn-secondary" onClick={onBack}>
            Cancel
          </button>
          <button className="btn btn-success btn-large" onClick={handleSave}>
            Save Question ✓
          </button>
        </div>
      </div>
    </div>
  );
}

export default QuestionEditor;
