import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Calendar, CalendarDays, RefreshCw, ChevronLeft, ChevronRight, CalendarCheck } from 'lucide-react';
import { apiService } from '../services/api';
import type { Appointment } from '../types';
import { useCalendar } from '../hooks/useCalendar';
import AppointmentCard from '../components/AppointmentCard';
import './CalendarPage.css';

const CalendarPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  
  const {
    currentDate,
    view,
    setView,
    navigateDate,
    filteredAppointments,
    dateDisplay,
  } = useCalendar(appointments);

  useEffect(() => {
    fetchAppointments();
    
    // Auto-refresh every 10 seconds for real-time updates
    const interval = setInterval(fetchAppointments, 10 * 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchAppointments = async () => {
    try {
      setLoading(prev => prev === undefined ? true : prev);
      setRefreshing(true);
      const response = await apiService.getAppointments();
      setAppointments(response.data.appointments || []);
    } catch (error) {
      console.error('Failed to fetch appointments:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    if (!refreshing) {
      fetchAppointments();
    }
  };

  const getViewIcon = (viewType: typeof view) => {
    switch (viewType) {
      case 'daily': return <CalendarDays size={18} />;
      case 'weekly': return <Calendar size={18} />;
      case 'monthly': return <Calendar size={18} />;
    }
  };

  const getAppointmentStats = () => {
    const uniquePersonnel = new Set(filteredAppointments.map(apt => apt.personnel_name)).size;
    return {
      total: filteredAppointments.length,
      personnel: uniquePersonnel,
      types: filteredAppointments.reduce((acc, apt) => {
        acc[apt.absence_type] = (acc[apt.absence_type] || 0) + 1;
        return acc;
      }, {} as Record<string, number>)
    };
  };

  const stats = getAppointmentStats();

  const renderDailyView = () => (
    <div className="calendar-daily-view">
      <div className="daily-header">
        <div className="daily-date-info">
          <h3 className="daily-title">
            {currentDate.toDateString() === new Date().toDateString() 
              ? "Today's Schedule" 
              : `Schedule for ${dateDisplay}`}
          </h3>
          <p className="daily-subtitle">{dateDisplay}</p>
        </div>
        <div className="daily-stats">
          <div className="stat-item">
            <span className="stat-number">{stats.total}</span>
            <span className="stat-label">Events</span>
          </div>
          <div className="stat-item">
            <span className="stat-number">{stats.personnel}</span>
            <span className="stat-label">Personnel</span>
          </div>
        </div>
      </div>
      
      <div className="daily-appointments">
        {filteredAppointments.length === 0 ? (
          <div className="no-appointments">
            <Calendar size={48} className="no-appointments-icon" />
            <h3>No appointments scheduled</h3>
            <p>There are no appointments for this day.</p>
          </div>
        ) : (
          filteredAppointments
            .sort((a, b) => {
              const timeA = a.start_time || '0000';
              const timeB = b.start_time || '0000';
              return timeA.localeCompare(timeB);
            })
            .map((appointment) => (
              <AppointmentCard key={appointment.id} appointment={appointment} />
            ))
        )}
      </div>
    </div>
  );

  const renderWeeklyView = () => {
    const startOfWeek = new Date(currentDate);
    startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
    
    const weekDays = [];
    for (let i = 0; i < 7; i++) {
      const day = new Date(startOfWeek);
      day.setDate(startOfWeek.getDate() + i);
      weekDays.push(day);
    }

    return (
      <div className="calendar-weekly-view">
        <div className="weekly-header">
          {weekDays.map((day, index) => {
            const dayAppointments = filteredAppointments.filter(apt => 
              new Date(apt.appointment_date).toDateString() === day.toDateString()
            );
            
            return (
              <div key={index} className="week-day">
                <div className="week-day-header">
                  <div className="week-day-name">
                    {day.toLocaleDateString('en-US', { weekday: 'short' })}
                  </div>
                  <div className="week-day-number">
                    {day.getDate()}
                  </div>
                  {dayAppointments.length > 0 && (
                    <div className="week-day-count">
                      {dayAppointments.length}
                    </div>
                  )}
                </div>
                <div className="week-day-appointments">
                  {dayAppointments.slice(0, 3).map(appointment => (
                    <AppointmentCard 
                      key={appointment.id} 
                      appointment={appointment} 
                      compact={true}
                    />
                  ))}
                  {dayAppointments.length > 3 && (
                    <div className="more-appointments">
                      +{dayAppointments.length - 3} more
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderMonthlyView = () => {
    const startOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    const startOfCalendar = new Date(startOfMonth);
    startOfCalendar.setDate(startOfCalendar.getDate() - startOfMonth.getDay());
    
    const calendarDays = [];
    const currentDay = new Date(startOfCalendar);
    
    for (let week = 0; week < 6; week++) {
      const weekDays = [];
      for (let day = 0; day < 7; day++) {
        const dayAppointments = filteredAppointments.filter(apt => 
          new Date(apt.appointment_date).toDateString() === currentDay.toDateString()
        );
        
        weekDays.push({
          date: new Date(currentDay),
          appointments: dayAppointments,
          isCurrentMonth: currentDay.getMonth() === currentDate.getMonth(),
          isToday: currentDay.toDateString() === new Date().toDateString()
        });
        
        currentDay.setDate(currentDay.getDate() + 1);
      }
      calendarDays.push(weekDays);
    }

    return (
      <div className="calendar-monthly-view">
        <div className="monthly-header">
          <div className="month-day-names">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
              <div key={day} className="month-day-name">{day}</div>
            ))}
          </div>
        </div>
        <div className="monthly-grid">
          {calendarDays.map((week, weekIndex) => (
            <div key={weekIndex} className="month-week">
              {week.map((day, dayIndex) => (
                <div 
                  key={dayIndex} 
                  className={`month-day ${
                    day.isCurrentMonth ? 'current-month' : 'other-month'
                  } ${
                    day.isToday ? 'today' : ''
                  }`}
                >
                  <div className="month-day-number">{day.date.getDate()}</div>
                  {day.appointments.length > 0 && (
                    <div className="month-day-indicators">
                      {day.appointments.slice(0, 3).map((apt, index) => (
                        <div 
                          key={index}
                          className={`appointment-indicator ${apt.absence_type.toLowerCase()}`}
                          title={`${apt.personnel_name} - ${apt.absence_type}`}
                        />
                      ))}
                      {day.appointments.length > 3 && (
                        <div className="more-indicator">+{day.appointments.length - 3}</div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="calendar-loading">
        <div className="loading-spinner">
          <RefreshCw className="spin" size={32} />
          <p>Loading calendar...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="calendar-page">
      <div className="calendar-header-section">
        <button onClick={() => navigate('/')} className="back-button">
          <ArrowLeft size={20} />
          Back to Home
        </button>
        
        <div className="calendar-title-section">
          <h1 className="calendar-title">Section Calendar</h1>
          <p className="calendar-subtitle">Track all personnel appointments and schedules</p>
        </div>
      </div>

      <div className="calendar-controls">
        <div className="calendar-navigation">
          <button 
            onClick={() => navigateDate('prev')} 
            className="nav-button"
            title="Previous"
          >
            <ChevronLeft size={20} />
          </button>
          
          <div className="current-date-display">
            <h2 className="date-display">{dateDisplay}</h2>
            <button 
              onClick={() => navigateDate('today')} 
              className="today-button"
              title="Go to today"
            >
              <CalendarCheck size={16} />
              Today
            </button>
          </div>
          
          <button 
            onClick={() => navigateDate('next')} 
            className="nav-button"
            title="Next"
          >
            <ChevronRight size={20} />
          </button>
        </div>
        
        <div className="view-controls">
          <div className="view-toggle">
            {(['daily', 'weekly', 'monthly'] as const).map((viewType) => (
              <button
                key={viewType}
                onClick={() => setView(viewType)}
                className={`toggle-button ${view === viewType ? 'active' : ''}`}
                title={`${viewType.charAt(0).toUpperCase() + viewType.slice(1)} view`}
              >
                {getViewIcon(viewType)}
                {viewType.charAt(0).toUpperCase() + viewType.slice(1)}
              </button>
            ))}
          </div>
          
          <button 
            onClick={handleRefresh} 
            className={`refresh-button ${refreshing ? 'refreshing' : ''}`}
            disabled={refreshing}
            title="Refresh calendar"
          >
            <RefreshCw size={16} className={refreshing ? 'spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      <div className="calendar-content">
        {view === 'daily' && renderDailyView()}
        {view === 'weekly' && renderWeeklyView()}
        {view === 'monthly' && renderMonthlyView()}
      </div>
    </div>
  );
};

export default CalendarPage;