import type { Appointment } from '../types';
import './AppointmentCard.css';

interface AppointmentCardProps {
  appointment: Appointment;
  compact?: boolean;
}

// interface GeneralEvent {
//   id: string;
//   title: string;
//   event_type: string;
//   appointment_date: string;
//   start_time?: string;
//   end_time?: string;
//   location?: string;
//   description?: string;
//   all_day: boolean;
//   category_color: string;
//   created_timestamp: string;
// }

const AppointmentCard = ({ appointment, compact = false }: AppointmentCardProps) => {
  const formatTime = (timeStr: string | undefined, allDay: boolean) => {
    if (allDay) return 'All Day';
    if (!timeStr) return 'Time TBD';
    
    // Convert HHMM to HH:MM AM/PM
    if (timeStr.length === 4) {
      const hours = parseInt(timeStr.substring(0, 2));
      const minutes = timeStr.substring(2, 4);
      const ampm = hours >= 12 ? 'PM' : 'AM';
      const displayHours = hours === 0 ? 12 : (hours > 12 ? hours - 12 : hours);
      return `${displayHours}:${minutes} ${ampm}`;
    }
    return timeStr;
  };

  const formatTimeRange = () => {
    const start = formatTime(appointment.start_time, appointment.all_day);
    if (appointment.end_time) {
      const end = formatTime(appointment.end_time, appointment.all_day);
      return `${start} - ${end}`;
    }
    return appointment.all_day ? start : `${start}+`;
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow';
    } else {
      return date.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric'
      });
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'medical': return '🏥';
      case 'dental': return '🦷';
      case 'leave': return '🌴';
      case 'personal_business': return '📋';
      default: return '📅';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'medical': return 'medical';
      case 'dental': return 'dental';
      case 'leave': return 'leave';
      case 'personal_business': return 'personal';
      default: return 'other';
    }
  };

  if (compact) {
    return (
      <div className={`appointment-card compact ${getTypeColor(appointment.absence_type)}`}>
        <div className="appointment-compact-content">
          <span className="appointment-icon">{getTypeIcon(appointment.absence_type)}</span>
          <div className="appointment-compact-info">
            <span className="appointment-name">{appointment.personnel_name}</span>
            <span className="appointment-time">{formatTimeRange()}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`appointment-card ${getTypeColor(appointment.absence_type)}`}>
      <div className="appointment-header">
        <div className="appointment-person">
          <div className="appointment-avatar">
            {appointment.personnel_name.split(' ').map(n => n[0]).join('').substring(0, 2)}
          </div>
          <div className="appointment-person-info">
            <div className="appointment-name">{appointment.personnel_name}</div>
            {appointment.personnel_rank && (
              <div className="appointment-rank">{appointment.personnel_rank}</div>
            )}
          </div>
        </div>
        <div className="appointment-type">
          <span className="appointment-icon">{getTypeIcon(appointment.absence_type)}</span>
          <span className="appointment-type-text">
            {appointment.absence_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </span>
        </div>
      </div>
      
      <div className="appointment-details">
        <div className="appointment-timing">
          <div className="appointment-date">{formatDate(appointment.appointment_date)}</div>
          <div className="appointment-time">{formatTimeRange()}</div>
        </div>
        
        {appointment.duration_hours && (
          <div className="appointment-duration">
            Duration: {appointment.duration_hours}h
          </div>
        )}
      </div>
      
      {appointment.original_text && (
        <div className="appointment-message">
          <div className="appointment-message-label">Original Request:</div>
          <div className="appointment-message-text">"{appointment.original_text}"</div>
        </div>
      )}
      
      <div className="appointment-footer">
        <div className="appointment-created">
          Created: {appointment.created_timestamp ? new Date(appointment.created_timestamp).toLocaleDateString() : 'N/A'}
        </div>
        {appointment.category_color && (
          <div 
            className="appointment-color-indicator"
            style={{ backgroundColor: appointment.category_color }}
            title="Category color"
          />
        )}
      </div>
    </div>
  );
};

export default AppointmentCard;