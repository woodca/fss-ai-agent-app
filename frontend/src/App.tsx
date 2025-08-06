import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import SectionLeadsPage from './pages/SectionLeadsPage';
import CalendarPage from './pages/CalendarPage';
import VeraChat from './components/VeraChat';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/section-leads" element={<SectionLeadsPage />} />
        <Route path="/calendar" element={<CalendarPage />} />
      </Routes>
      <VeraChat />
    </Router>
  );
}

export default App;