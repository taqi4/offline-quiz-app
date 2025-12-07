import React, { useState } from 'react';
import { QuizProvider } from './context/QuizContext';
import Home from './components/Home/Home';
import QuizCreator from './components/QuizCreator/QuizCreator';
import QuizPlayer from './components/QuizPlayer/QuizPlayer';
import QuizManager from './components/QuizManager/QuizManager';
import './App.css';

/**
 * Main App Component
 * Handles routing between different screens
 */
function App() {
  const [currentPage, setCurrentPage] = useState('home');
  const [editQuizId, setEditQuizId] = useState(null);

  // Navigate to a page
  const navigateTo = (page) => {
    setCurrentPage(page);
    setEditQuizId(null);
  };

  // Navigate to edit a specific quiz
  const navigateToEdit = (quizId) => {
    setEditQuizId(quizId);
    setCurrentPage('create');
  };

  // Render current page
  const renderPage = () => {
    switch (currentPage) {
      case 'home':
        return <Home onNavigate={navigateTo} />;
      
      case 'create':
        return (
          <QuizCreator 
            onBack={() => navigateTo('home')}
            editQuizId={editQuizId}
          />
        );
      
      case 'play':
        return (
          <QuizPlayer 
            onBack={() => navigateTo('home')}
          />
        );
      
      case 'manage':
        return (
          <QuizManager 
            onBack={() => navigateTo('home')}
            onEditQuiz={navigateToEdit}
          />
        );
      
      default:
        return <Home onNavigate={navigateTo} />;
    }
  };

  return (
    <QuizProvider>
      <div className="app">
        {renderPage()}
      </div>
    </QuizProvider>
  );
}

export default App;
