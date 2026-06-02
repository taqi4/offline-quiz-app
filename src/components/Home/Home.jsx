import React from 'react';
import { useSound } from '../../hooks/useSound';
import { CrescentMoonBackground } from '../Themes/ThemeBackgrounds';
import './Home.css';

/**
 * Home Screen Component
 * Welcome screen with navigation to Create, Play, and Manage quizzes
 */
export function Home({ onNavigate }) {
  const { playClick } = useSound();

  const handleNavigation = (page) => {
    playClick();
    onNavigate(page);
  };

  return (
    <div className="home-container">
      <CrescentMoonBackground />
      
      <div className="home-content">
        {/* Header with Logo */}
        <header className="home-header animate-fade-in-down">
          <div className="logo-container">
            <span className="logo-icon">🌙</span>
            <h1 className="logo-text">Jashn-e-Ghadeer</h1>
            <span className="logo-subtitle">Quiz</span>
          </div>
          <p className="tagline">Test Your Knowledge with Joy!</p>
        </header>

        {/* Main Navigation Cards */}
        <div className="home-nav-grid">
          {/* Create Quiz Card */}
          <button 
            className="nav-card create-card animate-fade-in-up stagger-1"
            onClick={() => handleNavigation('create')}
          >
            <div className="card-icon">✨</div>
            <h2 className="card-title">Create Quiz</h2>
            <p className="card-desc">Design your own quiz with age groups and sets</p>
            <div className="card-arrow">→</div>
          </button>

          {/* Play Quiz Card */}
          <button 
            className="nav-card play-card animate-fade-in-up stagger-2"
            onClick={() => handleNavigation('play')}
          >
            <div className="card-icon">🎮</div>
            <h2 className="card-title">Play Quiz</h2>
            <p className="card-desc">Enter focus mode and test your knowledge</p>
            <div className="card-arrow">→</div>
          </button>

          {/* Manage Quizzes Card */}
          <button 
            className="nav-card manage-card animate-fade-in-up stagger-3"
            onClick={() => handleNavigation('manage')}
          >
            <div className="card-icon">📚</div>
            <h2 className="card-title">Manage Quizzes</h2>
            <p className="card-desc">Import, export, edit, or delete quizzes</p>
            <div className="card-arrow">→</div>
          </button>
        </div>

        {/* Footer */}
        <footer className="home-footer animate-fade-in">
          <p></p>
        </footer>
      </div>
    </div>
  );
}

export default Home;
