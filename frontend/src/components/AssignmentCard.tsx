import type { ReactNode } from 'react';
import type { Personnel } from '../types';
import PersonnelCard from './PersonnelCard';
import './AssignmentCard.css';

interface AssignmentCardProps {
  title: string;
  icon: ReactNode;
  count: number;
  personnel: Personnel[];
  variant: 'floor' | 'admin' | 'terminal' | 'float';
}

const AssignmentCard = ({ 
  title, 
  icon, 
  count, 
  personnel, 
  variant 
}: AssignmentCardProps) => {
  return (
    <div className={`assignment-card ${variant}`}>
      <div className="assignment-header">
        {icon}
        <span>{title}</span>
      </div>
      <div className="assignment-count">{count}</div>
      <div className="assignment-personnel">
        {personnel.length > 0 ? (
          personnel.map((person) => (
            <PersonnelCard 
              key={person.name} 
              person={person} 
              showStatus={false} 
            />
          ))
        ) : (
          <div className="no-personnel">No personnel assigned</div>
        )}
      </div>
    </div>
  );
};

export default AssignmentCard;