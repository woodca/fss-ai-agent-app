import { useState, useMemo } from 'react';
import type { Appointment } from '../types';

export type CalendarView = 'daily' | 'weekly' | 'monthly';

export const useCalendar = (appointments: Appointment[]) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState<CalendarView>('daily');

  const navigateDate = (direction: 'prev' | 'next' | 'today') => {
    const newDate = new Date(currentDate);
    
    switch (direction) {
      case 'today':
        setCurrentDate(new Date());
        break;
      case 'prev':
        if (view === 'daily') {
          newDate.setDate(newDate.getDate() - 1);
        } else if (view === 'weekly') {
          newDate.setDate(newDate.getDate() - 7);
        } else if (view === 'monthly') {
          newDate.setMonth(newDate.getMonth() - 1);
        }
        setCurrentDate(newDate);
        break;
      case 'next':
        if (view === 'daily') {
          newDate.setDate(newDate.getDate() + 1);
        } else if (view === 'weekly') {
          newDate.setDate(newDate.getDate() + 7);
        } else if (view === 'monthly') {
          newDate.setMonth(newDate.getMonth() + 1);
        }
        setCurrentDate(newDate);
        break;
    }
  };

  const getFilteredAppointments = useMemo(() => {
    const startOfDay = (date: Date) => {
      const start = new Date(date);
      start.setHours(0, 0, 0, 0);
      return start;
    };

    const endOfDay = (date: Date) => {
      const end = new Date(date);
      end.setHours(23, 59, 59, 999);
      return end;
    };

    const startOfWeek = (date: Date) => {
      const start = new Date(date);
      const day = start.getDay();
      const diff = start.getDate() - day;
      start.setDate(diff);
      return startOfDay(start);
    };

    const endOfWeek = (date: Date) => {
      const end = new Date(date);
      const day = end.getDay();
      const diff = end.getDate() + (6 - day);
      end.setDate(diff);
      return endOfDay(end);
    };

    const startOfMonth = (date: Date) => {
      const start = new Date(date.getFullYear(), date.getMonth(), 1);
      return startOfDay(start);
    };

    const endOfMonth = (date: Date) => {
      const end = new Date(date.getFullYear(), date.getMonth() + 1, 0);
      return endOfDay(end);
    };

    let startDate: Date;
    let endDate: Date;

    switch (view) {
      case 'daily':
        startDate = startOfDay(currentDate);
        endDate = endOfDay(currentDate);
        break;
      case 'weekly':
        startDate = startOfWeek(currentDate);
        endDate = endOfWeek(currentDate);
        break;
      case 'monthly':
        startDate = startOfMonth(currentDate);
        endDate = endOfMonth(currentDate);
        break;
    }

    return appointments.filter(apt => {
      const aptStartDate = new Date(apt.appointment_date + 'T00:00:00'); // Fix timezone
      const aptEndDate = apt.end_date ? new Date(apt.end_date + 'T23:59:59') : aptStartDate;
      
      // Check if appointment overlaps with view date range
      return (aptStartDate <= endDate && aptEndDate >= startDate);
    });
  }, [appointments, currentDate, view]);

  const formatDateDisplay = () => {
    const options: Intl.DateTimeFormatOptions = {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    };

    switch (view) {
      case 'daily':
        return currentDate.toLocaleDateString('en-US', options);
      case 'weekly':
        const startOfWeek = new Date(currentDate);
        const endOfWeek = new Date(currentDate);
        startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
        endOfWeek.setDate(startOfWeek.getDate() + 6);
        return `${startOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${endOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
      case 'monthly':
        return currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    }
  };

  return {
    currentDate,
    view,
    setView,
    navigateDate,
    filteredAppointments: getFilteredAppointments,
    dateDisplay: formatDateDisplay(),
  };
};