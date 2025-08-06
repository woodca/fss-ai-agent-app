import type { Personnel } from '../types';
import './PersonnelCard.css';

interface PersonnelCardProps {
  person: Personnel;
  showStatus?: boolean;
}

const PersonnelCard = ({ person, showStatus = true }: PersonnelCardProps) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'front_desk':
      case 'admin_room':
      case 'terminal':
      case 'float':
        return 'available';
      case 'leave':
        return 'leave';
      case 'appointment':
        return 'appointment';
      default:
        return 'unknown';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'front_desk':
        return 'Front Desk';
      case 'admin_room':
        return 'Admin Room';
      case 'terminal':
        return 'Terminal';
      case 'float':
        return 'Float';
      case 'leave':
        return 'On Leave';
      case 'appointment':
        return 'Appointment';
      default:
        return status;
    }
  };

  return (
    <div className={`personnel-card ${getStatusColor(person.status)}`}>
      <div className="personnel-info">
        <span className="personnel-rank">{person.rank}</span>
        <span className="personnel-name">{person.name}</span>
      </div>
      {showStatus && (
        <div className="personnel-status">
          <span className={`status-badge ${getStatusColor(person.status)}`}>
            {getStatusLabel(person.status)}
          </span>
        </div>
      )}
    </div>
  );
};

export default PersonnelCard;