// Section Calendar Manager
class SectionCalendar {
    constructor() {
        this.appointments = [];
        this.currentView = 'daily';
        this.currentDate = new Date();
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadAppointments();
        this.updateDateDisplay();
    }
    
    bindEvents() {
        // View toggle buttons
        document.getElementById('dailyViewBtn').addEventListener('click', () => {
            this.switchView('daily');
        });
        
        document.getElementById('weeklyViewBtn').addEventListener('click', () => {
            this.switchView('weekly');
        });
        
        document.getElementById('monthlyViewBtn').addEventListener('click', () => {
            this.switchView('monthly');
        });
        
        // Navigation buttons
        document.getElementById('prevButton').addEventListener('click', () => {
            this.navigateDate(-1);
        });
        
        document.getElementById('nextButton').addEventListener('click', () => {
            this.navigateDate(1);
        });
        
        document.getElementById('todayButton').addEventListener('click', () => {
            this.goToToday();
        });
        
        // Refresh button
        document.getElementById('refreshCalendarButton').addEventListener('click', () => {
            this.refreshData();
        });
        
        // Auto-refresh every 2 minutes
        setInterval(() => {
            this.loadAppointments();
        }, 120000);
    }
    
    async loadAppointments() {
        this.showLoading(true);
        
        try {
            const response = await fetch('/api/appointments');
            const data = await response.json();
            
            if (data.success) {
                this.appointments = data.appointments;
                this.eventsByCategory = data.events_by_category;
                this.renderCurrentView();
            } else {
                this.showError('Failed to load calendar events');
            }
            
        } catch (error) {
            console.error('Failed to load calendar events:', error);
            this.showError('Failed to load calendar events');
        } finally {
            this.showLoading(false);
        }
    }
    
    switchView(viewType) {
        this.currentView = viewType;
        
        // Update button states
        document.getElementById('dailyViewBtn').classList.toggle('active', viewType === 'daily');
        document.getElementById('weeklyViewBtn').classList.toggle('active', viewType === 'weekly');
        document.getElementById('monthlyViewBtn').classList.toggle('active', viewType === 'monthly');
        
        // Show/hide views
        document.getElementById('dailyView').classList.toggle('hidden', viewType !== 'daily');
        document.getElementById('weeklyView').classList.toggle('hidden', viewType !== 'weekly');
        document.getElementById('monthlyView').classList.toggle('hidden', viewType !== 'monthly');
        
        this.updateDateDisplay();
        this.renderCurrentView();
    }
    
    navigateDate(direction) {
        if (this.currentView === 'daily') {
            this.currentDate.setDate(this.currentDate.getDate() + direction);
        } else if (this.currentView === 'weekly') {
            this.currentDate.setDate(this.currentDate.getDate() + (direction * 7));
        } else if (this.currentView === 'monthly') {
            this.currentDate.setMonth(this.currentDate.getMonth() + direction);
        }
        
        this.updateDateDisplay();
        this.renderCurrentView();
    }
    
    goToToday() {
        this.currentDate = new Date();
        this.updateDateDisplay();
        this.renderCurrentView();
    }
    
    updateDateDisplay() {
        const displayElement = document.getElementById('currentDateDisplay');
        
        if (this.currentView === 'daily') {
            const today = new Date();
            const isToday = this.currentDate.toDateString() === today.toDateString();
            const tomorrow = new Date(today);
            tomorrow.setDate(tomorrow.getDate() + 1);
            const isTomorrow = this.currentDate.toDateString() === tomorrow.toDateString();
            
            if (isToday) {
                displayElement.textContent = 'Today';
            } else if (isTomorrow) {
                displayElement.textContent = 'Tomorrow';
            } else {
                displayElement.textContent = this.currentDate.toLocaleDateString('en-US', {
                    weekday: 'long',
                    month: 'long',
                    day: 'numeric',
                    year: 'numeric'
                });
            }
            
            // Update daily subtitle
            const subtitle = document.getElementById('dailyDateSubtitle');
            if (subtitle) {
                subtitle.textContent = this.currentDate.toLocaleDateString('en-US', {
                    month: 'long',
                    day: 'numeric',
                    year: 'numeric'
                });
            }
            
        } else if (this.currentView === 'weekly') {
            const startOfWeek = new Date(this.currentDate);
            startOfWeek.setDate(this.currentDate.getDate() - this.currentDate.getDay());
            const endOfWeek = new Date(startOfWeek);
            endOfWeek.setDate(startOfWeek.getDate() + 6);
            
            displayElement.textContent = `${startOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${endOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
            
        } else if (this.currentView === 'monthly') {
            displayElement.textContent = this.currentDate.toLocaleDateString('en-US', {
                month: 'long',
                year: 'numeric'
            });
        }
    }
    
    renderCurrentView() {
        if (this.currentView === 'daily') {
            this.renderDailyView();
        } else if (this.currentView === 'weekly') {
            this.renderWeeklyView();
        } else if (this.currentView === 'monthly') {
            this.renderMonthlyView();
        }
    }
    
    renderDailyView() {
        const container = document.getElementById('dailyEventsContainer');
        const dateStr = this.currentDate.toISOString().split('T')[0];
        
        // Filter appointments for the current date
        const dayAppointments = this.appointments.filter(apt => apt.appointment_date === dateStr);
        
        // Update stats
        document.getElementById('dailyEventCount').textContent = dayAppointments.length;
        const uniquePersonnel = new Set(dayAppointments.map(apt => apt.personnel_name));
        document.getElementById('dailyPersonnelCount').textContent = uniquePersonnel.size;
        
        // Update title based on date
        const titleElement = document.getElementById('dailyDateTitle');
        const today = new Date();
        if (this.currentDate.toDateString() === today.toDateString()) {
            titleElement.textContent = "Today's Schedule";
        } else {
            const tomorrow = new Date(today);
            tomorrow.setDate(tomorrow.getDate() + 1);
            if (this.currentDate.toDateString() === tomorrow.toDateString()) {
                titleElement.textContent = "Tomorrow's Schedule";
            } else {
                titleElement.textContent = `Schedule for ${this.currentDate.toLocaleDateString('en-US', { weekday: 'long' })}`;
            }
        }
        
        container.innerHTML = '';
        
        if (dayAppointments.length === 0) {
            container.innerHTML = `
                <div class="no-events">
                    <i class="fas fa-calendar-check"></i>
                    <h3>No Events Scheduled</h3>
                    <p>No appointments or events for this date.</p>
                </div>
            `;
            return;
        }
        
        // Sort appointments by time
        dayAppointments.sort((a, b) => {
            if (a.all_day && !b.all_day) return -1;
            if (!a.all_day && b.all_day) return 1;
            if (a.all_day && b.all_day) return 0;
            
            const timeA = a.start_time || '0000';
            const timeB = b.start_time || '0000';
            return timeA.localeCompare(timeB);
        });
        
        // Group by time periods
        const allDayEvents = dayAppointments.filter(apt => apt.all_day);
        const morningEvents = dayAppointments.filter(apt => !apt.all_day && this.getHour(apt.start_time) < 12);
        const afternoonEvents = dayAppointments.filter(apt => !apt.all_day && this.getHour(apt.start_time) >= 12);
        
        // Render all-day events first
        if (allDayEvents.length > 0) {
            container.appendChild(this.createTimeSection('All Day', allDayEvents));
        }
        
        // Render morning events
        if (morningEvents.length > 0) {
            container.appendChild(this.createTimeSection('Morning', morningEvents));
        }
        
        // Render afternoon events
        if (afternoonEvents.length > 0) {
            container.appendChild(this.createTimeSection('Afternoon/Evening', afternoonEvents));
        }
    }
    
    renderWeeklyView() {
        const container = document.getElementById('weeklyGrid');
        container.innerHTML = '';
        
        // Get start of week (Sunday)
        const startOfWeek = new Date(this.currentDate);
        startOfWeek.setDate(this.currentDate.getDate() - this.currentDate.getDay());
        
        // Create week grid
        const weekGrid = document.createElement('div');
        weekGrid.className = 'week-grid';
        
        for (let i = 0; i < 7; i++) {
            const dayDate = new Date(startOfWeek);
            dayDate.setDate(startOfWeek.getDate() + i);
            const dateStr = dayDate.toISOString().split('T')[0];
            
            const dayColumn = document.createElement('div');
            dayColumn.className = 'week-day-column';
            
            // Day header
            const dayHeader = document.createElement('div');
            dayHeader.className = 'week-day-header';
            const isToday = dayDate.toDateString() === new Date().toDateString();
            if (isToday) dayHeader.classList.add('today');
            
            dayHeader.innerHTML = `
                <div class="day-name">${dayDate.toLocaleDateString('en-US', { weekday: 'short' })}</div>
                <div class="day-number">${dayDate.getDate()}</div>
            `;
            
            // Day events
            const dayEvents = this.appointments.filter(apt => apt.appointment_date === dateStr);
            const eventsContainer = document.createElement('div');
            eventsContainer.className = 'week-day-events';
            
            dayEvents.forEach(apt => {
                const eventElement = document.createElement('div');
                eventElement.className = `week-event ${apt.absence_type}`;
                eventElement.innerHTML = `
                    <div class="event-time">${this.formatTime(apt.start_time, apt.end_time, apt.all_day)}</div>
                    <div class="event-person">${apt.personnel_name}</div>
                    <div class="event-type">${this.formatAbsenceType(apt.absence_type)}</div>
                `;
                eventsContainer.appendChild(eventElement);
            });
            
            dayColumn.appendChild(dayHeader);
            dayColumn.appendChild(eventsContainer);
            weekGrid.appendChild(dayColumn);
        }
        
        container.appendChild(weekGrid);
    }
    
    renderMonthlyView() {
        const container = document.getElementById('monthlyGrid');
        container.innerHTML = '';
        
        // Get first day of month and calculate calendar grid
        const firstDay = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth(), 1);
        const lastDay = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth() + 1, 0);
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - firstDay.getDay()); // Start from Sunday
        
        const monthGrid = document.createElement('div');
        monthGrid.className = 'month-grid';
        
        // Generate 6 weeks (42 days) to cover all possibilities
        for (let week = 0; week < 6; week++) {
            const weekRow = document.createElement('div');
            weekRow.className = 'month-week';
            
            for (let day = 0; day < 7; day++) {
                const currentDate = new Date(startDate);
                currentDate.setDate(startDate.getDate() + (week * 7) + day);
                const dateStr = currentDate.toISOString().split('T')[0];
                
                const dayCell = document.createElement('div');
                dayCell.className = 'month-day';
                
                // Add classes for styling
                const isCurrentMonth = currentDate.getMonth() === this.currentDate.getMonth();
                const isToday = currentDate.toDateString() === new Date().toDateString();
                
                if (!isCurrentMonth) dayCell.classList.add('other-month');
                if (isToday) dayCell.classList.add('today');
                
                // Day number
                const dayNumber = document.createElement('div');
                dayNumber.className = 'day-number';
                dayNumber.textContent = currentDate.getDate();
                
                // Events for this day
                const dayEvents = this.appointments.filter(apt => apt.appointment_date === dateStr);
                const eventsContainer = document.createElement('div');
                eventsContainer.className = 'month-day-events';
                
                // Show up to 3 events, then a "more" indicator
                const maxVisible = 3;
                dayEvents.slice(0, maxVisible).forEach(apt => {
                    const eventDot = document.createElement('div');
                    eventDot.className = `month-event ${apt.absence_type}`;
                    eventDot.title = `${apt.personnel_name} - ${this.formatAbsenceType(apt.absence_type)}`;
                    eventsContainer.appendChild(eventDot);
                });
                
                if (dayEvents.length > maxVisible) {
                    const moreIndicator = document.createElement('div');
                    moreIndicator.className = 'month-event-more';
                    moreIndicator.textContent = `+${dayEvents.length - maxVisible}`;
                    eventsContainer.appendChild(moreIndicator);
                }
                
                dayCell.appendChild(dayNumber);
                dayCell.appendChild(eventsContainer);
                weekRow.appendChild(dayCell);
            }
            
            monthGrid.appendChild(weekRow);
        }
        
        container.appendChild(monthGrid);
    }
    
    createTimeSection(title, appointments) {
        const section = document.createElement('div');
        section.className = 'time-section';
        
        const header = document.createElement('div');
        header.className = 'time-section-header';
        header.innerHTML = `
            <h4>${title}</h4>
            <span class="event-count">${appointments.length} event${appointments.length !== 1 ? 's' : ''}</span>
        `;
        
        const eventsContainer = document.createElement('div');
        eventsContainer.className = 'time-section-events';
        
        appointments.forEach(apt => {
            const eventCard = this.createDailyEventCard(apt);
            eventsContainer.appendChild(eventCard);
        });
        
        section.appendChild(header);
        section.appendChild(eventsContainer);
        return section;
    }
    
    createDailyEventCard(appointment) {
        const card = document.createElement('div');
        const category = appointment.category || 'appointment';
        const categoryColor = appointment.category_color || '#007bff';
        
        card.className = `daily-event-card category-${category}`;
        card.style.borderLeftColor = categoryColor;
        
        const timeDisplay = this.formatTime(appointment.start_time, appointment.end_time, appointment.all_day);
        
        // Handle events differently (they don't have personnel)
        const isEvent = category === 'event';
        const displayName = isEvent ? (appointment.title || 'Squadron Event') : appointment.personnel_name;
        
        card.innerHTML = `
            <div class="event-time-indicator">
                <div class="event-time">${timeDisplay}</div>
                <div class="event-type-badge category-${category}" style="background-color: ${categoryColor}">
                    ${this.formatCategoryType(category, appointment.absence_type, appointment.title)}
                </div>
            </div>
            <div class="event-details">
                <div class="event-person">
                    <span class="person-name">${displayName}</span>
                    ${!isEvent && appointment.absence_type !== 'leave' ? `<span class="person-assignment">${this.formatAssignment(appointment.status || 'unknown')}</span>` : ''}
                </div>
                ${appointment.original_text ? `<div class="event-note">"${appointment.original_text}"</div>` : ''}
            </div>
        `;
        
        return card;
    }
    
    getHour(timeStr) {
        if (!timeStr || timeStr.length < 2) return 0;
        return parseInt(timeStr.substring(0, 2));
    }
    
    formatTime(startTime, endTime, allDay) {
        if (allDay) return 'All Day';
        if (!startTime) return 'Time TBD';
        
        const formatTime = (timeStr) => {
            if (!timeStr || timeStr.length < 4) return timeStr;
            const hours = parseInt(timeStr.substring(0, 2));
            const minutes = timeStr.substring(2, 4);
            const ampm = hours >= 12 ? 'PM' : 'AM';
            const displayHours = hours === 0 ? 12 : (hours > 12 ? hours - 12 : hours);
            return `${displayHours}:${minutes} ${ampm}`;
        };
        
        const start = formatTime(startTime);
        if (endTime) {
            const end = formatTime(endTime);
            return `${start} - ${end}`;
        } else {
            return start;
        }
    }
    
    formatAbsenceType(type) {
        const types = {
            'medical': 'Medical',
            'dental': 'Dental',
            'personal_business': 'Personal Business',
            'leave': 'Leave',
            'other': 'Other'
        };
        return types[type] || type;
    }
    
    formatCategoryType(category, absenceType, title) {
        if (category === 'event') {
            return title || 'Event';
        } else if (category === 'leave') {
            return 'Leave';
        } else {
            return this.formatAbsenceType(absenceType);
        }
    }
    
    formatAssignment(assignment) {
        const assignments = {
            'terminal': 'Terminal',
            'admin_room': 'Admin Room',
            'floor': 'Floor',
            'section_leads': 'Section Lead',
            'unknown': 'Unknown'
        };
        return assignments[assignment] || assignment;
    }
    
    async refreshData() {
        const refreshButton = document.getElementById('refreshCalendarButton');
        const icon = refreshButton.querySelector('i');
        
        // Add spin animation
        icon.style.transform = 'rotate(360deg)';
        
        try {
            await this.loadAppointments();
            this.showToast('Calendar refreshed successfully', 'success');
            
        } catch (error) {
            console.error('Failed to refresh data:', error);
            this.showToast('Failed to refresh calendar', 'error');
        }
        
        // Reset icon
        setTimeout(() => {
            icon.style.transform = 'rotate(0deg)';
        }, 500);
    }
    
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (show) {
            overlay.style.display = 'flex';
            this.isLoading = true;
        } else {
            overlay.style.display = 'none';
            this.isLoading = false;
        }
    }
    
    showError(message) {
        this.showToast(message, 'error');
    }
    
    showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        `;
        
        // Add toast styles if not already added
        if (!document.querySelector('#toast-styles')) {
            const style = document.createElement('style');
            style.id = 'toast-styles';
            style.textContent = `
                .toast {
                    position: fixed;
                    top: 100px;
                    right: 20px;
                    background: white;
                    border-radius: 8px;
                    padding: 16px 20px;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    z-index: 10000;
                    transform: translateX(400px);
                    transition: transform 0.3s ease;
                    max-width: 300px;
                }
                .toast.show { transform: translateX(0); }
                .toast-success { border-left: 4px solid var(--success-green); }
                .toast-error { border-left: 4px solid var(--error-red); }
                .toast-info { border-left: 4px solid var(--primary-blue); }
                .toast i { color: var(--text-secondary); }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(toast);
        
        // Show toast
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Hide toast after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => document.body.removeChild(toast), 300);
        }, 3000);
    }
}

// Global instance
let sectionCalendar;

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    sectionCalendar = new SectionCalendar();
    
    // Initialize floating buttons (AI agent and personnel roster)
    // Wait a bit to ensure section_leads.js has loaded
    setTimeout(() => {
        if (typeof initializeFloatingButtons === 'function') {
            initializeFloatingButtons();
        }
    }, 100);
});