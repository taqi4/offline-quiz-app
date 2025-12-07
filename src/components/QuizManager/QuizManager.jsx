import React, { useState, useRef } from 'react';
import { useQuiz } from '../../context/QuizContext';
import { useSound } from '../../hooks/useSound';
import { downloadQuizAsExcel, importQuizFromExcel, validateQuiz } from '../../utils/excelHandler';
import { CrescentMoonBackground } from '../Themes/ThemeBackgrounds';
import { THEMES } from '../../utils/helpers';
import './QuizManager.css';

/**
 * Quiz Manager Component
 * List, import, export, and delete quizzes
 */
export function QuizManager({ onBack, onEditQuiz }) {
  const { state, deleteQuiz, importQuiz } = useQuiz();
  const { playClick, playCorrect, playWrong } = useSound();
  const fileInputRef = useRef(null);
  
  const [importing, setImporting] = useState(false);
  const [importError, setImportError] = useState(null);
  const [importSuccess, setImportSuccess] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);

  // Handle file import
  const handleFileSelect = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    setImporting(true);
    setImportError(null);
    setImportSuccess(null);
    
    try {
      const quiz = await importQuizFromExcel(file);
      
      // Validate the imported quiz
      const validation = validateQuiz(quiz);
      if (!validation.valid) {
        setImportError(`Validation failed: ${validation.errors[0]}`);
        playWrong();
        return;
      }
      
      // Import the quiz
      const imported = importQuiz(quiz);
      playCorrect();
      setImportSuccess(`Successfully imported "${imported.name}"!`);
      
      // Clear success message after 3 seconds
      setTimeout(() => setImportSuccess(null), 3000);
    } catch (error) {
      setImportError(error.message || 'Failed to import quiz');
      playWrong();
    } finally {
      setImporting(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // Handle export
  const handleExport = (quiz) => {
    playClick();
    try {
      downloadQuizAsExcel(quiz);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  // Handle delete confirmation
  const handleDeleteClick = (quiz) => {
    playClick();
    setConfirmDelete(quiz);
  };

  // Confirm delete
  const confirmDeleteQuiz = () => {
    if (confirmDelete) {
      playClick();
      deleteQuiz(confirmDelete.id);
      setConfirmDelete(null);
    }
  };

  // Cancel delete
  const cancelDelete = () => {
    playClick();
    setConfirmDelete(null);
  };

  // Render quiz card
  const renderQuizCard = (quiz) => {
    const totalQuestions = quiz.ageGroups.reduce((sum, ag) => 
      sum + ag.sets.reduce((setSum, set) => setSum + set.questions.length, 0), 0
    );
    
    return (
      <div key={quiz.id} className="manager-quiz-card">
        <div className="quiz-card-main">
          <div className="quiz-card-header">
            <h3>{quiz.name}</h3>
            <div className="quiz-badges">
              {quiz.hasTimer && (
                <span className="badge timer-badge">⏱️ {quiz.timerSeconds}s</span>
              )}
            </div>
          </div>
          
          <div className="quiz-card-stats">
            <span>{quiz.ageGroups.length} Age Groups</span>
            <span>•</span>
            <span>{totalQuestions} Questions</span>
          </div>
          
          <div className="age-group-tags">
            {quiz.ageGroups.slice(0, 3).map(ag => {
              const theme = THEMES[ag.theme];
              return (
                <span key={ag.id} className="ag-tag">
                  {theme?.emoji} {ag.name}
                </span>
              );
            })}
            {quiz.ageGroups.length > 3 && (
              <span className="ag-tag more">+{quiz.ageGroups.length - 3} more</span>
            )}
          </div>
        </div>
        
        <div className="quiz-card-actions">
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => {
              playClick();
              onEditQuiz(quiz.id);
            }}
          >
            ✏️ Edit
          </button>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => handleExport(quiz)}
          >
            📤 Export
          </button>
          <button
            className="btn btn-danger btn-sm"
            onClick={() => handleDeleteClick(quiz)}
          >
            🗑️ Delete
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="quiz-manager">
      <CrescentMoonBackground />
      
      <div className="manager-container">
        {/* Header */}
        <header className="manager-header">
          <button className="back-button" onClick={onBack}>
            ← Home
          </button>
          <h1>Manage Quizzes</h1>
        </header>

        {/* Import Section */}
        <section className="import-section">
          <div className="import-card">
            <div className="import-icon">📥</div>
            <div className="import-content">
              <h3>Import Quiz from Excel</h3>
              <p>Import a quiz file (.xlsx) that was exported from this app</p>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls"
              onChange={handleFileSelect}
              className="file-input"
              id="file-import"
              disabled={importing}
            />
            <label htmlFor="file-import" className="btn btn-primary">
              {importing ? 'Importing...' : 'Choose File'}
            </label>
          </div>
          
          {importError && (
            <div className="import-message error animate-fade-in">
              ❌ {importError}
            </div>
          )}
          
          {importSuccess && (
            <div className="import-message success animate-fade-in">
              ✅ {importSuccess}
            </div>
          )}
        </section>

        {/* Quiz List */}
        <section className="quizzes-section">
          <h2>Your Quizzes ({state.quizzes.length})</h2>
          
          {state.quizzes.length === 0 ? (
            <div className="empty-state">
              <span className="empty-icon">📚</span>
              <h3>No Quizzes Yet</h3>
              <p>Create a new quiz or import one from Excel</p>
            </div>
          ) : (
            <div className="quizzes-list">
              {state.quizzes.map(renderQuizCard)}
            </div>
          )}
        </section>
      </div>

      {/* Delete Confirmation Modal */}
      {confirmDelete && (
        <div className="modal-overlay animate-fade-in">
          <div className="modal animate-scale-in">
            <h2>Delete Quiz?</h2>
            <p>Are you sure you want to delete <strong>"{confirmDelete.name}"</strong>?</p>
            <p className="modal-warning">This action cannot be undone.</p>
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={cancelDelete}>
                Cancel
              </button>
              <button className="btn btn-danger" onClick={confirmDeleteQuiz}>
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default QuizManager;
