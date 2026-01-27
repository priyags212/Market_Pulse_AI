import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Signup from './pages/Signup';
import ForgotPassword from './pages/ForgotPassword';
import Home from './pages/Home';
import { ThemeProvider } from './context/ThemeContext';
import DisclaimerModal from './components/DisclaimerModal';
import CategoryMenu from './pages/CategoryMenu';
import StockDetails from './pages/StockDetails';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = React.useState(
    localStorage.getItem('isAuthenticated') === 'true'
  );
  const [userName, setUserName] = React.useState(
    localStorage.getItem('userName') || ''
  );

  const handleLogout = () => {
    localStorage.removeItem('isAuthenticated');
    localStorage.removeItem('userName');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('userDob');
    // Clear session disclaimer so it shows again on next login/session
    sessionStorage.removeItem('hasSeenDisclaimer');
    setIsAuthenticated(false);
    setUserName('');
  };

  const handleLogin = () => {
    setIsAuthenticated(true);
    setUserName(localStorage.getItem('userName') || 'User');
  };

  // Disclaimer State (Session Based)
  const [showDisclaimer, setShowDisclaimer] = React.useState(false);

  React.useEffect(() => {
    // Check session storage so it resets when browser closes or on logout
    if (isAuthenticated) {
      const hasSeen = sessionStorage.getItem('hasSeenDisclaimer');
      if (!hasSeen) {
        setShowDisclaimer(true);
      }
    }
  }, [isAuthenticated]); // Check on login

  const handleCloseDisclaimer = () => {
    setShowDisclaimer(false);
    sessionStorage.setItem('hasSeenDisclaimer', 'true');
  };

  return (
    <ThemeProvider>
      <Router>
        <div className="app-container">
          {showDisclaimer && isAuthenticated && (
            <DisclaimerModal isOpen={true} onClose={handleCloseDisclaimer} />
          )}
          <Routes>
            <Route
              path="/"
              element={<Dashboard onLogout={handleLogout} isAuthenticated={isAuthenticated} userName={userName} />}
            />
            <Route
              path="/login"
              element={isAuthenticated ? <Navigate to="/" /> : <Login onLogin={handleLogin} />}
            />
            <Route
              path="/signup"
              element={isAuthenticated ? <Navigate to="/" /> : <Signup onLogin={handleLogin} />}
            />
            <Route
              path="/categories"
              element={isAuthenticated ? <CategoryMenu /> : <Navigate to="/login" />}
            />
            <Route path="/stock/:symbol" element={isAuthenticated ? <StockDetails /> : <Navigate to="/login" />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
          </Routes>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;
