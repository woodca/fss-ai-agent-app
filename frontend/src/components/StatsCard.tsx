import type { ReactNode } from 'react';
import './StatsCard.css';

interface StatsCardProps {
  number: number | string;
  label: string;
  variant?: 'available' | 'unavailable' | 'default';
  onClick?: () => void;
  icon?: ReactNode;
  action?: string;
}

const StatsCard = ({ 
  number, 
  label, 
  variant = 'default', 
  onClick, 
  icon,
  action 
}: StatsCardProps) => {
  const isClickable = !!onClick;
  
  return (
    <div 
      className={`stat-card ${variant} ${isClickable ? 'clickable' : ''}`}
      onClick={onClick}
      role={isClickable ? 'button' : undefined}
      tabIndex={isClickable ? 0 : undefined}
      onKeyDown={(e) => {
        if (isClickable && (e.key === 'Enter' || e.key === ' ')) {
          onClick();
        }
      }}
      aria-label={`${label}: ${number}${action ? '. Click to ' + action : ''}`}
    >
      <div className="stat-number">{number}</div>
      <div className="stat-label">{label}</div>
      {action && (
        <div className="stat-action">
          {icon}
          <span>{action}</span>
        </div>
      )}
    </div>
  );
};

export default StatsCard;