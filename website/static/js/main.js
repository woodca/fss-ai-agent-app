// Vera - Main JavaScript
class FSSAgent {
    constructor() {
        this.appointments = [];
        this.manning = null;
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadInitialData();
    }
    
    bindEvents() {
        // Calendar button click
        document.getElementById('startButton').addEventListener('click', () => {
            window.location.href = '/calendar';
        });
        
        // Section leads button click
        document.getElementById('sectionLeadsButton').addEventListener('click', () => {
            window.location.href = '/section-leads';
        });
        
        // Refresh button click
        document.getElementById('refreshButton').addEventListener('click', () => {
            this.refreshData();
        });
        
        // Auto-refresh every 30 seconds
        setInterval(() => {
            this.loadStats();
        }, 30000);
    }
    
    async loadInitialData() {
        this.showLoading(true);
        try {
            await this.loadStats();
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showError('Failed to load initial data');
        } finally {
            this.showLoading(false);
        }
    }
    
    async loadStats() {
        try {
            const response = await fetch('/api/manning');
            const data = await response.json();
            
            if (data.success) {
                this.manning = data.manning;
                this.updateStatsDisplay();
            }
            
            // Also load appointment count
            const appointmentsResponse = await fetch('/api/appointments');
            const appointmentsData = await appointmentsResponse.json();
            
            if (appointmentsData.success) {
                this.appointments = appointmentsData.appointments;
                this.updateAppointmentCount();
            }
            
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }
    
    updateStatsDisplay() {
        if (!this.manning) return;
        
        document.getElementById('availablePersonnel').textContent = 
            this.manning.available || '-';
        
        document.getElementById('availabilityPercent').textContent = 
            this.manning.availability_percentage ? 
            `${Math.round(this.manning.availability_percentage)}%` : '-';
    }
    
    updateAppointmentCount() {
        document.getElementById('totalAppointments').textContent = 
            this.appointments.length;
    }
    
    async showAppointments() {
        // Show loading
        this.showLoading(true);
        
        try {
            // Load fresh appointment data
            await this.loadAppointments();
            
            // Hide hero section and show appointments
            document.querySelector('.hero').style.display = 'none';
            document.getElementById('appointmentsSection').style.display = 'block';
            
            // Render appointments
            this.renderAppointments();
            
            // Smooth scroll to appointments
            document.getElementById('appointmentsSection').scrollIntoView({
                behavior: 'smooth'
            });
            
        } catch (error) {
            console.error('Failed to load appointments:', error);
            this.showError('Failed to load appointments');
        } finally {
            this.showLoading(false);
        }
    }
    
    async loadAppointments() {
        const response = await fetch('/api/appointments');
        const data = await response.json();
        
        if (data.success) {
            this.appointments = data.appointments;
        } else {
            throw new Error(data.error || 'Failed to load appointments');
        }
    }
    
    renderAppointments() {
        const grid = document.getElementById('appointmentsGrid');
        grid.innerHTML = '';
        
        if (this.appointments.length === 0) {
            grid.innerHTML = `
                <div class="no-appointments">
                    <i class="fas fa-calendar-check" style="font-size: 48px; color: var(--text-secondary); margin-bottom: 16px;"></i>
                    <h3>No Active Appointments</h3>
                    <p>All personnel are currently available.</p>
                </div>
            `;
            return;
        }
        
        // Sort appointments by date and time
        const sortedAppointments = this.appointments.sort((a, b) => {
            const dateA = new Date(a.appointment_date + 'T' + (a.start_time ? this.formatTimeForSort(a.start_time) : '00:00'));
            const dateB = new Date(b.appointment_date + 'T' + (b.start_time ? this.formatTimeForSort(b.start_time) : '00:00'));
            return dateA - dateB;
        });
        
        sortedAppointments.forEach(appointment => {
            const card = this.createAppointmentCard(appointment);
            grid.appendChild(card);
        });
    }
    
    createAppointmentCard(appointment) {
        const card = document.createElement('div');
        card.className = `appointment-card ${appointment.absence_type} fade-in`;
        
        const formattedDate = this.formatDate(appointment.appointment_date);
        const formattedTime = this.formatTime(appointment.start_time, appointment.end_time, appointment.all_day);
        const absenceType = this.formatAbsenceType(appointment.absence_type);
        
        card.innerHTML = `
            <div class="appointment-header">
                <div class="appointment-person">
                    <div class="person-name">${appointment.personnel_name}</div>
                    ${appointment.personnel_rank ? `<div class="person-rank">${appointment.personnel_rank}</div>` : ''}
                </div>
                <div class="appointment-type">${absenceType}</div>
            </div>
            
            <div class="appointment-details">
                <div class="appointment-time">${formattedTime}</div>
                <div class="appointment-date">${formattedDate}</div>
            </div>
            
            ${appointment.original_text ? `
                <div class="appointment-message">
                    "${appointment.original_text}"
                </div>
            ` : ''}
        `;
        
        return card;
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        const today = new Date();
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        
        if (date.toDateString() === today.toDateString()) {
            return 'Today';
        } else if (date.toDateString() === tomorrow.toDateString()) {
            return 'Tomorrow';
        } else {
            return date.toLocaleDateString('en-US', {
                weekday: 'long',
                month: 'long',
                day: 'numeric',
                year: 'numeric'
            });
        }
    }
    
    formatTime(startTime, endTime, allDay) {
        if (allDay) {
            return 'All Day';
        }
        
        if (!startTime) {
            return 'Time TBD';
        }
        
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
            return `${start}+`;
        }
    }
    
    formatTimeForSort(timeStr) {
        if (!timeStr || timeStr.length < 4) return '00:00';
        return timeStr.substring(0, 2) + ':' + timeStr.substring(2, 4);
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
    
    async refreshData() {
        const refreshButton = document.getElementById('refreshButton');
        const icon = refreshButton.querySelector('i');
        
        // Add spin animation
        icon.style.transform = 'rotate(360deg)';
        
        try {
            await this.loadAppointments();
            this.renderAppointments();
            await this.loadStats();
            
            // Show success feedback
            this.showToast('Data refreshed successfully', 'success');
            
        } catch (error) {
            console.error('Failed to refresh data:', error);
            this.showToast('Failed to refresh data', 'error');
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

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FSSAgent();
});