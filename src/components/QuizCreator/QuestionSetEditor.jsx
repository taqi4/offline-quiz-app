import React, { useState } from 'react';
import { useSound } from '../../hooks/useSound';
import { createEmptyQuestion, deepClone } from '../../utils/helpers';
import QuestionEditor from './QuestionEditor';
import { ThemeBackground } from '../Themes/ThemeBackgrounds';
import { getThemeStyle } from '../Themes/ThemeProvider';
import './QuestionSetEditor.css';

/**
 * Question Set Editor Component
 * Manages a set of MCQ questions
 */
export function QuestionSetEditor({ questionSet, theme, onSave, onBack }) {
  const { playClick } = useSound();
  const [editedSet, setEditedSet] = useState(deepClone(questionSet));
  const [editingQuestionIndex, setEditingQuestionIndex] = useState(null);
  const [errors, setErrors] = useState({});

  // Update set name
  const updateName = (name) => {
    setEditedSet(prev => ({ ...prev, name }));
  };

  // Add new question
  const addQuestion = () => {
    playClick();
    const newQuestion = createEmptyQuestion();
    setEditedSet(prev => ({
      ...prev,
      questions: [...prev.questions, newQuestion]
    }));
    setEditingQuestionIndex(editedSet.questions.length);
  };

  // Update question
  const updateQuestion = (index, updatedQuestion) => {
    setEditedSet(prev => ({
      ...prev,
      questions: prev.questions.map((q, i) =>
        i === index ? updatedQuestion : q
      )
    }));
  };

  // Delete question
  const deleteQuestion = (index) => {
    playClick();
    setEditedSet(prev => ({
      ...prev,
      questions: prev.questions.filter((_, i) => i !== index)
    }));
    if (editingQuestionIndex === index) {
      setEditingQuestionIndex(null);
    } else if (editingQuestionIndex > index) {
      setEditingQuestionIndex(editingQuestionIndex - 1);
    }
  };

  // Move question up
  const moveQuestionUp = (index) => {
    if (index === 0) return;
    playClick();
    setEditedSet(prev => {
      const questions = [...prev.questions];
      [questions[index - 1], questions[index]] = [questions[index], questions[index - 1]];
      return { ...prev, questions };
    });
  };

  // Move question down
  const moveQuestionDown = (index) => {
    if (index === editedSet.questions.length - 1) return;
    playClick();
    setEditedSet(prev => {
      const questions = [...prev.questions];
      [questions[index], questions[index + 1]] = [questions[index + 1], questions[index]];
      return { ...prev, questions };
    });
  };

  // Validate and save
  const handleSave = () => {
    const newErrors = {};
    
    if (!editedSet.name.trim()) {
      newErrors.name = 'Set name is required';
    }
    
    if (editedSet.questions.length === 0) {
      newErrors.questions = 'Add at least one question';
    }
    
    // Validate each question
    for (let i = 0; i < editedSet.questions.length; i++) {
      const q = editedSet.questions[i];
      if (!q.text.trim()) {
        newErrors.questions = `Question ${i + 1}: Question text is required`;
        break;
      }
      const filledOptions = q.options.filter(o => o.trim() !== '');
      if (filledOptions.length < 2) {
        newErrors.questions = `Question ${i + 1}: At least 2 options are required`;
        break;
      }
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    playClick();
    onSave(editedSet);
  };

  const themeStyle = getThemeStyle(theme);

  // If editing a question, show the question editor
  if (editingQuestionIndex !== null) {
    const question = editedSet.questions[editingQuestionIndex];
    if (question) {
      return (
        <QuestionEditor
          question={question}
          questionNumber={editingQuestionIndex + 1}
          theme={theme}
          onSave={(updated) => {
            updateQuestion(editingQuestionIndex, updated);
            setEditingQuestionIndex(null);
          }}
          onBack={() => setEditingQuestionIndex(null)}
        />
      );
    }
  }

  return (
    <div className="question-set-editor" style={themeStyle}>
      <ThemeBackground themeId={theme} />
      
      <div className="set-editor-container">
        {/* Header */}
        <header className="set-editor-header">
          <button className="back-button" onClick={onBack}>
            ← Back to Age Group
          </button>
          <h1>Edit Question Set</h1>
        </header>

        {/* Set Name */}
        <section className="set-editor-section">
          <h2>Set Name</h2>
          <div className="form-group">
            <input
              type="text"
              value={editedSet.name}
              onChange={(e) => updateName(e.target.value)}
              placeholder="e.g., Set A, Easy Questions, Round 1"
              className={errors.name ? 'error' : ''}
            />
            {errors.name && <span className="error-text">{errors.name}</span>}
          </div>
        </section>

        {/* Questions List */}
        <section className="set-editor-section">
          <div className="questions-header">
            <h2>📝 Questions ({editedSet.questions.length})</h2>
          </div>
          
          {errors.questions && <div className="error-banner">{errors.questions}</div>}
          
          <div className="questions-list">
            {editedSet.questions.map((question, index) => (
              <div key={question.id} className="question-card">
                <div className="question-number">Q{index + 1}</div>
                <div className="question-content">
                  <p className="question-text">
                    {question.text || <em>No question text</em>}
                  </p>
                  <div className="question-meta">
                    <span>{question.options.filter(o => o.trim()).length} options</span>
                    <span>•</span>
                    <span>Answer: {['A', 'B', 'C', 'D'][question.correctIndex]}</span>
                  </div>
                </div>
                <div className="question-actions">
                  <button
                    className="btn-icon-sm"
                    onClick={() => moveQuestionUp(index)}
                    disabled={index === 0}
                    title="Move up"
                  >
                    ↑
                  </button>
                  <button
                    className="btn-icon-sm"
                    onClick={() => moveQuestionDown(index)}
                    disabled={index === editedSet.questions.length - 1}
                    title="Move down"
                  >
                    ↓
                  </button>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => {
                      playClick();
                      setEditingQuestionIndex(index);
                    }}
                  >
                    Edit
                  </button>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => deleteQuestion(index)}
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))}
            
            <button className="add-question-btn" onClick={addQuestion}>
              <span className="add-icon">+</span>
              <span>Add Question</span>
            </button>
          </div>
        </section>

        {/* Actions */}
        <div className="set-editor-actions">
          <button className="btn btn-secondary" onClick={onBack}>
            Cancel
          </button>
          <button className="btn btn-success btn-large" onClick={handleSave}>
            Save Question Set ✓
          </button>
        </div>
      </div>
    </div>
  );
}

export default QuestionSetEditor;
