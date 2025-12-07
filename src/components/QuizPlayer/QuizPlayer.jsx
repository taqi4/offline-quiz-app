import React, { useState, useEffect, useCallback } from 'react';
import { useQuiz } from '../../context/QuizContext';
import { useSound } from '../../hooks/useSound';
import { useConfetti, ConfettiCelebration } from '../Celebrations/Confetti';
import { FireworksCelebration } from '../Celebrations/Fireworks';
import { BalloonsCelebration } from '../Celebrations/Balloons';
import { ThemeBackground } from '../Themes/ThemeBackgrounds';
import { getThemeStyle } from '../Themes/ThemeProvider';
import { calculateScore, THEMES } from '../../utils/helpers';
import './QuizPlayer.css';

/**
 * Quiz Player Component
 * Main container for playing quizzes with focus mode
 */
export function QuizPlayer({ onBack }) {
  const { state, getNextSetForAgeGroup, advanceRoundRobin } = useQuiz();
  const { playClick, playStart, playCorrect, playWrong, playTick, playWarningTick, playCelebration } = useSound();
  const { fireCorrectAnswer, fireBigCelebration, fireMiniFireworks, fireMiniBalloons } = useConfetti();
  
  // Game states
  const [selectedQuiz, setSelectedQuiz] = useState(null);
  const [selectedAgeGroup, setSelectedAgeGroup] = useState(null);
  const [selectedSet, setSelectedSet] = useState(null);
  const [suggestedSet, setSuggestedSet] = useState(null);
  
  // Play state
  const [gameState, setGameState] = useState('select-quiz'); // select-quiz, select-age-group, select-set, playing, results
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [showFeedback, setShowFeedback] = useState(false);
  const [lastAnswerCorrect, setLastAnswerCorrect] = useState(null);
  const [timeLeft, setTimeLeft] = useState(0);
  const [showCelebration, setShowCelebration] = useState(false);

  // Timer effect
  useEffect(() => {
    if (gameState !== 'playing' || !selectedQuiz?.hasTimer || showFeedback) return;
    
    if (timeLeft <= 0) {
      // Time's up - mark as wrong
      handleAnswer(-1);
      return;
    }

    const timer = setInterval(() => {
      setTimeLeft(prev => {
        const newTime = prev - 1;
        if (newTime <= 5 && newTime > 0) {
          playWarningTick();
        } else if (newTime > 5) {
          playTick();
        }
        return newTime;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [gameState, timeLeft, showFeedback, selectedQuiz, playTick, playWarningTick]);

  // Select quiz
  const handleSelectQuiz = (quiz) => {
    playClick();
    setSelectedQuiz(quiz);
    setGameState('select-age-group');
  };

  // Select age group
  const handleSelectAgeGroup = (ageGroup) => {
    playClick();
    setSelectedAgeGroup(ageGroup);
    
    // Get suggested set based on round robin
    const suggested = getNextSetForAgeGroup(selectedQuiz.id, ageGroup.id);
    setSuggestedSet(suggested);
    setSelectedSet(suggested?.set || ageGroup.sets[0]);
    setGameState('select-set');
  };

  // Start playing
  const startPlaying = (set = selectedSet) => {
    playStart();
    setSelectedSet(set);
    setCurrentQuestionIndex(0);
    setAnswers([]);
    setShowFeedback(false);
    setLastAnswerCorrect(null);
    
    if (selectedQuiz.hasTimer) {
      setTimeLeft(selectedQuiz.timerSeconds);
    }
    
    setGameState('playing');
  };

  // Handle answer selection
  const handleAnswer = useCallback((selectedIndex) => {
    if (showFeedback) return;
    
    const currentQuestion = selectedSet.questions[currentQuestionIndex];
    const isCorrect = selectedIndex === currentQuestion.correctIndex;
    
    setLastAnswerCorrect(isCorrect);
    setShowFeedback(true);
    setAnswers(prev => [...prev, selectedIndex]);
    
    if (isCorrect) {
      playCorrect();
      // Fire mini celebration based on age group setting
      const celebType = selectedAgeGroup.celebrationType || 'confetti';
      if (celebType === 'confetti') {
        fireCorrectAnswer();
      } else if (celebType === 'fireworks') {
        fireMiniFireworks();
      } else if (celebType === 'balloons') {
        fireMiniBalloons();
      }
    } else {
      playWrong();
    }
    
    // Move to next question after delay
    setTimeout(() => {
      if (currentQuestionIndex < selectedSet.questions.length - 1) {
        setCurrentQuestionIndex(prev => prev + 1);
        setShowFeedback(false);
        setLastAnswerCorrect(null);
        if (selectedQuiz.hasTimer) {
          setTimeLeft(selectedQuiz.timerSeconds);
        }
      } else {
        // Quiz complete
        advanceRoundRobin(selectedQuiz.id, selectedAgeGroup.id);
        playCelebration();
        setShowCelebration(true);
        setGameState('results');
      }
    }, 1500);
  }, [showFeedback, selectedSet, currentQuestionIndex, selectedQuiz, selectedAgeGroup, playCorrect, playWrong, fireCorrectAnswer, advanceRoundRobin, playCelebration]);

  // Restart quiz
  const restartQuiz = () => {
    playClick();
    setShowCelebration(false);
    startPlaying();
  };

  // Go back to selection
  const goToSelection = () => {
    playClick();
    setShowCelebration(false);
    setGameState('select-age-group');
    setSelectedAgeGroup(null);
    setSelectedSet(null);
  };

  // Go home
  const goHome = () => {
    playClick();
    setShowCelebration(false);
    onBack();
  };

  // Get theme styles
  const themeStyle = selectedAgeGroup ? getThemeStyle(selectedAgeGroup.theme) : {};
  const themeId = selectedAgeGroup?.theme || 'crescent-moon';

  // Render quiz selection
  if (gameState === 'select-quiz') {
    return (
      <div className="quiz-player select-mode">
        <ThemeBackground themeId="crescent-moon" />
        <div className="player-container">
          <header className="player-header">
            <button className="back-button" onClick={onBack}>
              ← Home
            </button>
            <h1>Select a Quiz</h1>
          </header>
          
          {state.quizzes.length === 0 ? (
            <div className="empty-state">
              <span className="empty-icon">📚</span>
              <h2>No Quizzes Yet</h2>
              <p>Create or import a quiz first!</p>
              <button className="btn btn-primary" onClick={onBack}>
                Go Back
              </button>
            </div>
          ) : (
            <div className="quiz-grid">
              {state.quizzes.map(quiz => (
                <button
                  key={quiz.id}
                  className="quiz-card"
                  onClick={() => handleSelectQuiz(quiz)}
                >
                  <div className="quiz-card-icon">📝</div>
                  <h3>{quiz.name}</h3>
                  <div className="quiz-card-stats">
                    <span>{quiz.ageGroups.length} Age Groups</span>
                    {quiz.hasTimer && <span>⏱️ {quiz.timerSeconds}s</span>}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Render age group selection
  if (gameState === 'select-age-group') {
    return (
      <div className="quiz-player select-mode">
        <ThemeBackground themeId="crescent-moon" />
        <div className="player-container">
          <header className="player-header">
            <button className="back-button" onClick={() => setGameState('select-quiz')}>
              ← Back
            </button>
            <h1>{selectedQuiz.name}</h1>
          </header>
          
          <h2 className="section-title">Select Age Group</h2>
          
          <div className="age-group-grid">
            {selectedQuiz.ageGroups.map(ageGroup => {
              const theme = THEMES[ageGroup.theme];
              const totalQuestions = ageGroup.sets.reduce((sum, set) => sum + set.questions.length, 0);
              
              return (
                <button
                  key={ageGroup.id}
                  className="age-group-card"
                  onClick={() => handleSelectAgeGroup(ageGroup)}
                  style={getThemeStyle(ageGroup.theme)}
                >
                  <span className="ag-theme-emoji">{theme?.emoji}</span>
                  <h3>{ageGroup.name}</h3>
                  <div className="ag-stats">
                    <span>{ageGroup.sets.length} Sets</span>
                    <span>•</span>
                    <span>{totalQuestions} Questions</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  // Render set selection
  if (gameState === 'select-set') {
    return (
      <div className="quiz-player select-mode" style={themeStyle}>
        <ThemeBackground themeId={themeId} />
        <div className="player-container">
          <header className="player-header">
            <button className="back-button" onClick={() => setGameState('select-age-group')}>
              ← Back
            </button>
            <h1>{selectedAgeGroup.name}</h1>
          </header>
          
          <div className="set-selection">
            <h2 className="section-title">Select Question Set</h2>
            
            {suggestedSet && (
              <div className="suggested-set">
                <p>🎯 Suggested (Round Robin):</p>
                <button
                  className="btn btn-primary btn-large"
                  onClick={() => startPlaying(suggestedSet.set)}
                >
                  Play {suggestedSet.set.name} ({suggestedSet.set.questions.length} questions)
                </button>
              </div>
            )}
            
            <p className="or-divider">— or choose another —</p>
            
            <div className="set-grid">
              {selectedAgeGroup.sets.map(set => (
                <button
                  key={set.id}
                  className="set-card"
                  onClick={() => startPlaying(set)}
                >
                  <h3>{set.name}</h3>
                  <span>{set.questions.length} questions</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Render playing mode
  if (gameState === 'playing') {
    const currentQuestion = selectedSet.questions[currentQuestionIndex];
    const progress = ((currentQuestionIndex + 1) / selectedSet.questions.length) * 100;
    
    return (
      <div className="quiz-player focus-mode" style={themeStyle}>
        <ThemeBackground themeId={themeId} />
        
        <div className="focus-container">
          {/* Progress Bar */}
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
          
          {/* Header */}
          <div className="focus-header">
            <span className="question-counter">
              Question {currentQuestionIndex + 1} of {selectedSet.questions.length}
            </span>
            {selectedQuiz.hasTimer && (
              <span className={`timer ${timeLeft <= 5 ? 'warning' : ''}`}>
                ⏱️ {timeLeft}s
              </span>
            )}
          </div>
          
          {/* Question */}
          <div className="question-container animate-fade-in">
            <h2 className="question-text">{currentQuestion.text}</h2>
            
            <div className="options-container">
              {currentQuestion.options.map((option, index) => {
                const isSelected = answers[currentQuestionIndex] === index;
                const isCorrect = index === currentQuestion.correctIndex;
                const showResult = showFeedback;
                
                let optionClass = 'option-button';
                if (showResult) {
                  if (isCorrect) optionClass += ' correct';
                  else if (isSelected) optionClass += ' wrong';
                }
                
                return (
                  <button
                    key={index}
                    className={optionClass}
                    onClick={() => handleAnswer(index)}
                    disabled={showFeedback}
                  >
                    <span className="option-letter">
                      {['A', 'B', 'C', 'D'][index]}
                    </span>
                    <span className="option-text">{option}</span>
                    {showResult && isCorrect && <span className="result-icon">✓</span>}
                    {showResult && isSelected && !isCorrect && <span className="result-icon">✗</span>}
                  </button>
                );
              })}
            </div>
          </div>
          
          {/* Feedback */}
          {showFeedback && (
            <div className={`feedback ${lastAnswerCorrect ? 'correct' : 'wrong'} animate-scale-in`}>
              {lastAnswerCorrect ? '🎉 Correct!' : '😢 Oops! Wrong answer'}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Render results
  if (gameState === 'results') {
    const score = calculateScore(selectedSet.questions, answers);
    const celebrationType = selectedAgeGroup.celebrationType;
    
    return (
      <div className="quiz-player results-mode" style={themeStyle}>
        <ThemeBackground themeId={themeId} />
        
        {showCelebration && (celebrationType === 'confetti' || !celebrationType) && (
          <ConfettiCelebration autoFire={true} type="big" />
        )}

        {showCelebration && celebrationType === 'fireworks' && (
          <FireworksCelebration autoFire={true} duration={4000} />
        )}
        
        {showCelebration && celebrationType === 'balloons' && (
          <BalloonsCelebration autoFire={true} count={40} />
        )}
        
        <div className="results-container animate-scale-in">
          <div className="results-card">
            <h1 className="results-title">🎉 Quiz Complete!</h1>
            
            <div className="score-display">
              <div className="score-circle animate-pulse">
                <span className="score-number">{score.correct}</span>
                <span className="score-divider">/</span>
                <span className="score-total">{score.total}</span>
              </div>
              <p className="score-percentage">{score.percentage}%</p>
            </div>
            
            <div className="results-message">
              {score.percentage === 100 && <p>🌟 Perfect Score! Amazing!</p>}
              {score.percentage >= 80 && score.percentage < 100 && <p>👏 Great job!</p>}
              {score.percentage >= 50 && score.percentage < 80 && <p>👍 Good effort!</p>}
              {score.percentage < 50 && <p>📚 Keep practicing!</p>}
            </div>
            
            <div className="results-actions">
              <button className="btn btn-primary btn-large" onClick={restartQuiz}>
                🔄 Play Again
              </button>
              <button className="btn btn-secondary" onClick={goToSelection}>
                🎯 Choose Another Set
              </button>
              <button className="btn btn-secondary" onClick={goHome}>
                🏠 Home
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
}

export default QuizPlayer;
