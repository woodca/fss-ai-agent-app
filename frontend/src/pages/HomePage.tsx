import { useNavigate } from 'react-router-dom';
import { Users, Calendar } from 'lucide-react';
import './HomePage.css';

const HomePage = () => {
  const navigate = useNavigate();


  return (
    <section className="hero">
      <div className="hero-container">
        <div className="hero-content">
          <h1 className="hero-title">Vera</h1>
          <p className="hero-subtitle">All knowing sentient agent, here to simplify existence itself</p>
          
          
          {/* Main Action Buttons */}
          <div className="action-section">
            <button 
              className="start-button"
              onClick={() => navigate('/section-leads')}
            >
              <Users size={20} />
              <span>Section Leads</span>
            </button>
            <button 
              className="start-button secondary"
              onClick={() => navigate('/calendar')}
            >
              <Calendar size={20} />
              <span>Calendar</span>
            </button>
          </div>
        </div>
      </div>

    </section>
  );
};

export default HomePage;