import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, FileText, Monitor, ArrowRightLeft, Info, Bot } from 'lucide-react';
import { apiService } from '../services/api';
import type { PersonnelStatusResponse, Personnel } from '../types';
import StatsCard from '../components/StatsCard';
import AssignmentCard from '../components/AssignmentCard';
import PersonnelCard from '../components/PersonnelCard';
import './SectionLeadsPage.css';

const SectionLeadsPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [personnelStatus, setPersonnelStatus] = useState<PersonnelStatusResponse | null>(null);
  const [showUnavailableModal, setShowUnavailableModal] = useState(false);
  const [showRosterModal, setShowRosterModal] = useState(false);

  useEffect(() => {
    fetchPersonnelStatus();
    // Set up auto-refresh every 5 seconds for real-time updates
    const interval = setInterval(fetchPersonnelStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchPersonnelStatus = async () => {
    try {
      const response = await apiService.getPersonnelStatus();
      setPersonnelStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch personnel status:', error);
    } finally {
      setLoading(false);
    }
  };

  const getUnavailablePersonnel = (): Personnel[] => {
    if (!personnelStatus) return [];
    
    // Now we get unavailable personnel directly from the API response
    return personnelStatus.unavailable_personnel || [];
  };

  const getAllPersonnel = (): Personnel[] => {
    if (!personnelStatus) return [];
    const allPersonnel: Personnel[] = [];
    
    Object.values(personnelStatus.assignments).forEach(assignment => {
      allPersonnel.push(...assignment.personnel);
    });
    
    return allPersonnel.sort((a, b) => a.name.localeCompare(b.name));
  };

  const getSortedPersonnel = (): Personnel[] => {
    const allPersonnel = getAllPersonnel();
    
    // Define rank hierarchy (highest to lowest)
    const rankOrder = {
      'CMSgt': 1, 'SMSgt': 2, 'MSgt': 3, 'TSgt': 4, 'SSgt': 5, 'SrA': 6, 'A1C': 7, 'AB': 8,
      'Civilian': 9, 'GS': 9, 'Contractor': 9
    };
    
    return allPersonnel.sort((a, b) => {
      const aRankOrder = rankOrder[a.rank as keyof typeof rankOrder] || 10;
      const bRankOrder = rankOrder[b.rank as keyof typeof rankOrder] || 10;
      
      // First sort by rank
      if (aRankOrder !== bRankOrder) {
        return aRankOrder - bRankOrder;
      }
      
      // If same rank, sort alphabetically by last name
      const aLastName = a.name.split(' ').pop() || '';
      const bLastName = b.name.split(' ').pop() || '';
      return aLastName.localeCompare(bLastName);
    });
  };

  const getPersonAssignment = (personName: string): string => {
    if (!personnelStatus) return 'Unknown';
    
    for (const [assignmentKey, assignment] of Object.entries(personnelStatus.assignments)) {
      if (assignment.personnel.some(p => p.name === personName)) {
        switch (assignmentKey) {
          case 'floor': return 'Front Desk';
          case 'admin_room': return 'Admin Room';
          case 'terminal': return 'Terminal';
          case 'float': return 'Float';
          default: return assignmentKey;
        }
      }
    }
    
    return 'Unassigned';
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading section leads...</p>
      </div>
    );
  }

  if (!personnelStatus) {
    return (
      <div className="error-container">
        <p>Failed to load personnel status</p>
        <button onClick={fetchPersonnelStatus}>Retry</button>
      </div>
    );
  }

  return (
    <div className="section-leads-page">

      {/* Header */}
      <section className="section-leads-header">
        <div className="leads-header-container">
          <h1 className="leads-title">CS Section Leads</h1>
        </div>
      </section>

      {/* Staffing Dashboard */}
      <section className="staffing-dashboard">
        <div className="dashboard-container">
          <h2 className="dashboard-title">Current Staffing Status</h2>
          
          {/* Overall Stats */}
          <div className="stats-grid">
            <StatsCard
              number={personnelStatus.stats.working_count}
              label="Working"
              variant="available"
            />
            <StatsCard
              number={personnelStatus.stats.out_of_office_count}
              label="Out of Office"
              variant="unavailable"
              onClick={() => setShowUnavailableModal(true)}
              icon={<Info size={16} />}
              action="View Details"
            />
          </div>

          {/* Assignment Breakdown */}
          <div className="assignment-grid">
            <AssignmentCard
              title="Front Desk"
              icon={<Users size={20} />}
              count={personnelStatus.assignments.floor.count}
              personnel={personnelStatus.assignments.floor.personnel}
              variant="floor"
            />
            
            <AssignmentCard
              title="Admin Room"
              icon={<FileText size={20} />}
              count={personnelStatus.assignments.admin_room.count}
              personnel={personnelStatus.assignments.admin_room.personnel}
              variant="admin"
            />
            
            <AssignmentCard
              title="Terminals"
              icon={<Monitor size={20} />}
              count={personnelStatus.assignments.terminal.count}
              personnel={personnelStatus.assignments.terminal.personnel}
              variant="terminal"
            />

            <AssignmentCard
              title="Float"
              icon={<ArrowRightLeft size={20} />}
              count={personnelStatus.assignments.float.count}
              personnel={personnelStatus.assignments.float.personnel}
              variant="float"
            />
          </div>
        </div>
      </section>

      {/* Liquid Glass Action Buttons */}
      <div className="liquid-glass-buttons">
        <button
          className="liquid-glass-btn people-btn"
          onClick={() => setShowRosterModal(true)}
          aria-label="View all personnel"
        >
          <Users size={20} />
          <span>People</span>
        </button>
        
        <button
          className="liquid-glass-btn calendar-btn"
          onClick={() => navigate('/calendar')}
          aria-label="Go to calendar"
        >
          <ArrowRightLeft size={20} />
          <span>Calendar</span>
        </button>
        
        <button
          className="liquid-glass-btn vera-btn"
          onClick={() => window.dispatchEvent(new CustomEvent('toggleVera'))}
          aria-label="Toggle Vera chat"
        >
          <Bot size={20} />
          <span>Vera</span>
        </button>
      </div>

      {/* Unavailable Personnel Modal */}
      {showUnavailableModal && (
        <div className="modal-overlay" onClick={() => setShowUnavailableModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">
                <Users size={20} />
                Out of Office Personnel
              </h2>
              <button 
                className="modal-close"
                onClick={() => setShowUnavailableModal(false)}
                aria-label="Close modal"
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              {getUnavailablePersonnel().map((person) => (
                <PersonnelCard key={person.name} person={person} />
              ))}
              {getUnavailablePersonnel().length === 0 && (
                <div className="no-data">
                  <p>All personnel are currently available and working.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Personnel Roster Modal */}
      {showRosterModal && (
        <div className="modal-overlay roster-overlay" onClick={() => setShowRosterModal(false)}>
          <div className="modal-content roster-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">
                <Users size={20} />
                All Personnel Roster
              </h2>
              <button 
                className="modal-close"
                onClick={() => setShowRosterModal(false)}
                aria-label="Close modal"
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="roster-stats">
                Total: {personnelStatus.stats.total_personnel} Military: {personnelStatus.stats.military_count} Civilian: {personnelStatus.stats.civilian_count}
              </div>
              <div className="roster-personnel">
                {getSortedPersonnel().map((person) => (
                  <div key={person.name} className="roster-person-item">
                    {person.name} - {getPersonAssignment(person.name)}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SectionLeadsPage;