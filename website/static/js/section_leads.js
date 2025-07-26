// Section Leads Dashboard Manager
class SectionLeadsDashboard {
    constructor() {
        this.personnelStatus = null;
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadDashboardData();
    }
    
    bindEvents() {
        // Chat interface events
        this.initializeChatInterface();
        
        // Unavailable card click event
        const unavailableCard = document.getElementById('unavailableCard');
        if (unavailableCard) {
            unavailableCard.addEventListener('click', () => {
                this.showUnavailableModal();
            });
        }
        
        // Modal close events
        const closeModal = document.getElementById('closeModal');
        const modalOverlay = document.getElementById('unavailableModal');
        
        if (closeModal) {
            closeModal.addEventListener('click', () => {
                this.hideUnavailableModal();
            });
        }
        
        if (modalOverlay) {
            modalOverlay.addEventListener('click', (e) => {
                if (e.target === modalOverlay) {
                    this.hideUnavailableModal();
                }
            });
        }
        
        // Floating chat events
        this.initializeFloatingChat();
        
        // Personnel roster events
        this.initializePersonnelRoster();
        
        // Auto-refresh every 2 minutes
        setInterval(() => {
            this.loadDashboardData();
        }, 120000);
    }
    
    initializeChatInterface() {
        const rufusInput = document.getElementById('rufusInput');
        const rufusSend = document.getElementById('rufusSend');
        
        // Send button click
        if (rufusSend) {
            rufusSend.addEventListener('click', () => {
                this.sendChatMessage();
            });
        }
        
        // Enter key press
        if (rufusInput) {
            rufusInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendChatMessage();
                }
            });
            
            // Auto-resize input and typing indicators
            rufusInput.addEventListener('input', () => {
                this.updateSendButtonState();
            });
        }
        
        this.updateSendButtonState();
    }
    
    updateSendButtonState() {
        const rufusInput = document.getElementById('rufusInput');
        const rufusSend = document.getElementById('rufusSend');
        
        if (rufusInput && rufusSend) {
            const hasText = rufusInput.value.trim().length > 0;
            rufusSend.disabled = !hasText;
        }
    }
    
    async sendChatMessage() {
        console.log('sendChatMessage called');
        
        // Prevent multiple submissions
        if (this.isLoading) {
            console.log('Already processing a message, ignoring...');
            return;
        }
        
        const rufusInput = document.getElementById('rufusInput');
        const message = rufusInput.value.trim();
        
        console.log('Message:', message);
        if (!message) return;
        
        // Add user message to chat
        console.log('Adding user message to chat');
        this.addRufusMessage(message, 'user');
        
        // Clear input and disable send button
        rufusInput.value = '';
        this.updateSendButtonState();
        
        // Show typing indicator
        console.log('Showing typing indicator');
        this.showRufusTyping();
        
        // Set loading state
        this.isLoading = true;
        
        try {
            // Send message to AI agent
            console.log('Sending request to AI agent...');
            const response = await fetch('/api/ai-agent/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    sender_id: 'section_lead_' + Date.now()
                })
            });
            
            console.log('Response received, parsing JSON...');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Debug logging
            console.log('Response status:', response.status);
            console.log('Response data:', data);
            
            // Remove typing indicator
            this.hideTypingIndicator();
            
            // Remove typing indicator
            this.hideRufusTyping();
            
            if (data.success) {
                // Add AI response to chat
                const aiResponse = data.ai_response || data.response;
                console.log('Adding AI response:', aiResponse);
                this.addRufusMessage(aiResponse, 'agent');
                
                // If this was a status update, refresh the dashboard
                if (data.message_type === 'status_command' && data.person_updated) {
                    setTimeout(() => {
                        this.loadDashboardData();
                    }, 1000);
                }
            } else {
                // Log the full error data for debugging
                console.error('AI Agent Error:', data);
                
                const errorMessage = data.ai_response || data.error || 'Sorry, I encountered an error. Please try again.';
                this.addRufusMessage(errorMessage, 'agent');
            }
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideRufusTyping();
            this.addRufusMessage('Sorry, I could not process your message right now. Please try again.', 'agent');
        } finally {
            // Reset loading state
            this.isLoading = false;
        }
    }
    
    addRufusMessage(text, sender) {
        console.log('addRufusMessage called:', { text, sender });
        const rufusMessages = document.getElementById('rufusMessages');
        
        if (!rufusMessages) {
            console.error('rufusMessages element not found!');
            return;
        }
        
        // Create message bubble
        const bubble = document.createElement('div');
        bubble.className = sender === 'user' ? 'rufus-user-bubble' : 'rufus-agent-bubble';
        
        const avatar = document.createElement('div');
        avatar.className = sender === 'user' ? 'rufus-avatar rufus-user-avatar' : 'rufus-avatar';
        avatar.textContent = sender === 'user' ? 'You' : '🤖';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'rufus-message-content';
        messageContent.textContent = text;
        
        bubble.appendChild(avatar);
        bubble.appendChild(messageContent);
        
        rufusMessages.appendChild(bubble);
        
        // Force a reflow and scroll to bottom
        setTimeout(() => {
            rufusMessages.scrollTop = rufusMessages.scrollHeight;
        }, 50);
        
        console.log('Rufus message added successfully');
    }
    
    showRufusTyping() {
        const rufusMessages = document.getElementById('rufusMessages');
        
        if (!rufusMessages) return;
        
        const typingBubble = document.createElement('div');
        typingBubble.className = 'rufus-agent-bubble';
        typingBubble.id = 'rufusTyping';
        
        const avatar = document.createElement('div');
        avatar.className = 'rufus-avatar';
        avatar.textContent = '🤖';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'rufus-message-content';
        messageContent.innerHTML = '<em>AI Agent is typing...</em>';
        messageContent.style.fontStyle = 'italic';
        messageContent.style.opacity = '0.7';
        
        typingBubble.appendChild(avatar);
        typingBubble.appendChild(messageContent);
        
        rufusMessages.appendChild(typingBubble);
        rufusMessages.scrollTop = rufusMessages.scrollHeight;
    }
    
    hideRufusTyping() {
        const typingIndicator = document.getElementById('rufusTyping');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    addChatMessage(text, sender, messageType = null) {
        console.log('addChatMessage called:', { text, sender, messageType });
        const chatMessages = document.getElementById('chatMessages');
        console.log('chatMessages element:', chatMessages);
        
        if (!chatMessages) {
            console.error('chatMessages element not found!');
            return;
        }
        
        // Ensure chat window is visible
        const chatWindow = document.getElementById('chatWindow');
        if (chatWindow && chatWindow.style.display === 'none') {
            console.log('Chat window is hidden, making it visible');
            chatWindow.style.display = 'block';
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        // Force visibility with inline styles
        messageDiv.style.display = 'flex';
        messageDiv.style.marginBottom = '16px';
        messageDiv.style.opacity = '1';
        messageDiv.style.visibility = 'visible';
        
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit',
            hour12: true 
        });
        
        let senderLabel = sender === 'user' ? 'You' : '🤖 AI Agent';
        let messageClass = '';
        
        if (messageType === 'status_command') {
            messageClass = 'status-update';
        } else if (messageType === 'error') {
            messageClass = 'error-message';
        }
        
        messageDiv.innerHTML = `
            <div class="message-content ${messageClass}">
                <div class="message-text">${text}</div>
                <div class="message-time">${senderLabel} • ${timeString}</div>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        console.log('Message div appended to chat');
        console.log('Message div HTML:', messageDiv.outerHTML);
        console.log('Chat messages children count:', chatMessages.children.length);
        console.log('Chat messages computed style:', window.getComputedStyle(chatMessages));
        console.log('Chat messages scroll height:', chatMessages.scrollHeight);
        console.log('Chat messages client height:', chatMessages.clientHeight);
        console.log('Message div computed style:', window.getComputedStyle(messageDiv));
        
        // Force a repaint
        messageDiv.offsetHeight;
        
        // Scroll to bottom
        setTimeout(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
            console.log('Scrolled to bottom');
        }, 50);
    }
    
    showTypingIndicator() {
        const chatMessages = document.getElementById('chatMessages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message agent-message typing-indicator';
        typingDiv.id = 'typingIndicator';
        
        typingDiv.innerHTML = `
            <div class="message-content">
                <div class="message-text">
                    <div class="typing-animation">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                    🤖 AI Agent is typing...
                </div>
            </div>
        `;
        
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    async loadDashboardData() {
        this.showLoading(true);
        
        try {
            // Load personnel status
            const statusResponse = await fetch('/api/personnel-status');
            const statusData = await statusResponse.json();
            
            if (statusData.success) {
                this.personnelStatus = statusData;
                this.updateStaffingDashboard();
            } else {
                this.showError('Failed to load personnel status');
            }
            
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showError('Failed to load dashboard data');
        } finally {
            this.showLoading(false);
        }
    }
    
    updateStaffingDashboard() {
        if (!this.personnelStatus) return;
        
        const { stats, assignments } = this.personnelStatus;
        
        // Update overall stats
        document.getElementById('availablePersonnel').textContent = stats.working_count || 0;
        document.getElementById('unavailablePersonnel').textContent = stats.out_of_office_count || 0;
        
        // Update assignment breakdowns
        this.updateAssignmentCard('floor', assignments.floor);
        this.updateAssignmentCard('admin', assignments.admin_room);
        this.updateAssignmentCard('terminal', assignments.terminal);
    }
    
    updateAssignmentCard(cardType, assignmentData) {
        const countElement = document.getElementById(`${cardType}Count`);
        const personnelElement = document.getElementById(`${cardType}Personnel`);
        
        // Filter to only show people who are currently working
        const workingPersonnel = assignmentData.personnel.filter(person => person.status === 'working');
        
        if (countElement) {
            countElement.textContent = workingPersonnel.length;
        }
        
        if (personnelElement) {
            personnelElement.innerHTML = '';
            workingPersonnel.forEach(person => {
                const personElement = document.createElement('div');
                personElement.className = `person-item ${person.status}`;
                
                // Use just the name field since it already includes rank
                const displayName = person.name || `${person.rank} Unknown`;
                
                personElement.innerHTML = `
                    <span class="person-name">${displayName}</span>
                    <span class="person-status ${person.status}">${this.formatStatus(person.status)}</span>
                `;
                personnelElement.appendChild(personElement);
            });
        }
    }
    
    formatStatus(status) {
        const statuses = {
            'available': 'Available',
            'working': 'Working',
            'on_appointment': 'At Appointment',
            'on_leave': 'On Leave'
        };
        return statuses[status] || status;
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
    
    async showUnavailableModal() {
        const modal = document.getElementById('unavailableModal');
        const modalBody = document.getElementById('unavailableList');
        
        if (!modal || !modalBody) return;
        
        // Clear existing content and show loading
        modalBody.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">Loading...</p>';
        
        // Show modal first
        modal.style.display = 'flex';
        
        try {
            // Get unavailable personnel
            const unavailablePersonnel = await this.getUnavailablePersonnel();
            
            // Clear loading message
            modalBody.innerHTML = '';
            
            if (unavailablePersonnel.length === 0) {
                modalBody.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">All personnel are currently in the office.</p>';
            } else {
                unavailablePersonnel.forEach(person => {
                    const personElement = this.createUnavailablePersonElement(person);
                    modalBody.appendChild(personElement);
                });
            }
        } catch (error) {
            console.error('Failed to load unavailable personnel:', error);
            modalBody.innerHTML = '<p style="text-align: center; color: var(--error-red);">Failed to load personnel data.</p>';
        }
    }
    
    hideUnavailableModal() {
        const modal = document.getElementById('unavailableModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
    
    async getUnavailablePersonnel() {
        try {
            // Fetch all personnel data to find unavailable ones
            const response = await fetch('/api/personnel');
            const data = await response.json();
            
            if (!data.success) {
                return [];
            }
            
            // Filter for personnel who are unavailable (on leave or at appointments)
            const unavailable = data.personnel.filter(person => 
                person.status === 'on_leave' || person.status === 'on_appointment'
            );
            
            return unavailable;
        } catch (error) {
            console.error('Failed to fetch personnel for unavailable list:', error);
            return [];
        }
    }
    
    createUnavailablePersonElement(person) {
        const div = document.createElement('div');
        div.className = 'unavailable-person';
        
        // Get initials for avatar
        const nameParts = person.name.split(' ');
        const initials = nameParts.map(part => part[0]).join('').slice(0, 2);
        
        // Format assignment name
        const assignmentName = this.formatAssignment(person.assignment);
        
        // Get reason details
        let reasonText, reasonIcon;
        switch(person.status) {
            case 'on_appointment':
                reasonText = 'On Appointment';
                reasonIcon = 'fa-calendar-check';
                break;
            case 'on_leave':
                reasonText = 'On Leave';
                reasonIcon = 'fa-plane-departure';
                break;
            case 'available':
                reasonText = 'Available';
                reasonIcon = 'fa-clock';
                break;
            default:
                reasonText = person.status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
                reasonIcon = 'fa-question-circle';
        }
        
        div.innerHTML = `
            <div class="person-avatar">${initials}</div>
            <div class="person-info">
                <div class="person-name-row">${person.name}</div>
                <div class="person-reason">
                    <span class="reason-badge ${person.status}">
                        <i class="fas ${reasonIcon}"></i>
                        ${reasonText}
                    </span>
                </div>
            </div>
        `;
        
        return div;
    }
    
    formatAssignment(assignment) {
        const assignments = {
            'terminal': 'Terminal',
            'admin_room': 'Admin Room',
            'floor': 'Floor',
            'section_leads': 'Section Lead'
        };
        return assignments[assignment] || assignment;
    }
    
    formatStatus(status) {
        const statuses = {
            'working': 'Working',
            'available': 'Working',
            'on_leave': 'On Leave',
            'on_appointment': 'At Appointment',
            'out_of_office': 'Out of Office'
        };
        return statuses[status] || status;
    }
    
    initializeFloatingChat() {
        const rufusToggle = document.getElementById('rufusToggle');
        const rufusChatWindow = document.getElementById('rufusChatWindow');
        const rufusMinimize = document.getElementById('rufusMinimize');
        
        // Toggle chat window
        if (rufusToggle && rufusChatWindow) {
            rufusToggle.addEventListener('click', () => {
                const isVisible = rufusChatWindow.style.display === 'flex';
                rufusChatWindow.style.display = isVisible ? 'none' : 'flex';
                // Hide/show toggle button
                rufusToggle.style.display = isVisible ? 'flex' : 'none';
                
                // Focus on input when chat opens
                if (!isVisible) {
                    setTimeout(() => {
                        const rufusInput = document.getElementById('rufusInput');
                        if (rufusInput) {
                            rufusInput.focus();
                        }
                    }, 100);
                }
            });
        }
        
        // Minimize chat window
        if (rufusMinimize && rufusChatWindow) {
            rufusMinimize.addEventListener('click', () => {
                rufusChatWindow.style.display = 'none';
                // Show toggle button again
                if (rufusToggle) {
                    rufusToggle.style.display = 'flex';
                }
            });
        }
    }
    
    initializePersonnelRoster() {
        const rosterToggle = document.getElementById('personnelRosterToggle');
        const rosterModal = document.getElementById('personnelRosterModal');
        const closeRosterModal = document.getElementById('closeRosterModal');
        
        // Toggle roster modal
        if (rosterToggle) {
            rosterToggle.addEventListener('click', () => {
                this.showPersonnelRoster();
            });
        }
        
        // Close roster modal
        if (closeRosterModal) {
            closeRosterModal.addEventListener('click', () => {
                rosterModal.style.display = 'none';
            });
        }
        
        // Note: No overlay click to close since we want both roster and AI agent accessible
    }
    
    async showPersonnelRoster() {
        const modal = document.getElementById('personnelRosterModal');
        const modalBody = document.getElementById('personnelRosterList');
        
        if (!modal || !modalBody) return;
        
        // Check if already open, if so close it
        if (modal.style.display === 'flex') {
            modal.style.display = 'none';
            return;
        }
        
        // Clear existing content and show loading
        modalBody.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">Loading personnel...</p>';
        modal.style.display = 'flex';
        
        try {
            // Fetch all personnel data to show complete roster
            const response = await fetch('/api/personnel');
            const data = await response.json();
            
            if (!data.success) {
                modalBody.innerHTML = '<p style="text-align: center; color: var(--error-red);">Failed to load personnel data.</p>';
                return;
            }
            
            // Clear loading message
            modalBody.innerHTML = '';
            
            // Organize personnel by categories
            const sectionLeads = [];
            const otherPersonnel = [];
            
            data.personnel.forEach(person => {
                if (person.assignment === 'section_leads') {
                    sectionLeads.push(person);
                } else {
                    otherPersonnel.push(person);
                }
            });
            
            // Sort by rank (rough approximation)
            const rankOrder = ['TSgt', 'SSgt', 'SrA', 'A1C', 'Amn', 'AB', 'GS-', 'Mrs.', 'Mr.'];
            const sortByRank = (a, b) => {
                const aRankIndex = rankOrder.findIndex(rank => a.name.includes(rank));
                const bRankIndex = rankOrder.findIndex(rank => b.name.includes(rank));
                return aRankIndex - bRankIndex;
            };
            
            sectionLeads.sort(sortByRank);
            otherPersonnel.sort(sortByRank);
        
            // Create section leads section
            if (sectionLeads.length > 0) {
                const sectionLeadsDiv = this.createPersonnelSection('Section Leaders', sectionLeads, 'fas fa-star');
                modalBody.appendChild(sectionLeadsDiv);
            }
            
            // Create other personnel section
            if (otherPersonnel.length > 0) {
                const otherPersonnelDiv = this.createPersonnelSection('Section Personnel', otherPersonnel, 'fas fa-users');
                modalBody.appendChild(otherPersonnelDiv);
            }
            
        } catch (error) {
            console.error('Failed to load personnel roster:', error);
            modalBody.innerHTML = '<p style="text-align: center; color: var(--error-red);">Failed to load personnel data.</p>';
        }
    }
    
    createPersonnelSection(title, personnel, iconClass) {
        const sectionDiv = document.createElement('div');
        sectionDiv.className = 'personnel-section';
        
        const titleDiv = document.createElement('div');
        titleDiv.className = 'personnel-section-title';
        titleDiv.innerHTML = `<i class="${iconClass}"></i>${title} (${personnel.length})`;
        
        const listDiv = document.createElement('div');
        listDiv.className = 'personnel-list';
        
        personnel.forEach(person => {
            const personElement = this.createPersonnelItem(person);
            listDiv.appendChild(personElement);
        });
        
        sectionDiv.appendChild(titleDiv);
        sectionDiv.appendChild(listDiv);
        
        return sectionDiv;
    }
    
    createPersonnelItem(person) {
        const item = document.createElement('div');
        item.className = `personnel-item ${person.status}`;
        
        // Get initials for avatar
        const nameParts = person.name.split(' ');
        const initials = nameParts.map(part => part[0]).join('').slice(0, 2);
        
        // Format assignment name
        const assignmentName = this.formatAssignment(person.assignment);
        
        // Format status name
        const statusName = this.formatStatus(person.status);
        
        item.innerHTML = `
            <div class="personnel-avatar">${initials}</div>
            <div class="personnel-info">
                <div class="personnel-name">${person.name}</div>
                <div class="personnel-details">
                    <span>${assignmentName}</span>
                    <span class="personnel-status ${person.status}">${statusName}</span>
                </div>
            </div>
        `;
        
        return item;
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
let sectionLeadsDashboard;

// Standalone function to initialize floating buttons for use on any page
function initializeFloatingButtons() {
    // Initialize Personnel Roster
    const rosterToggle = document.getElementById('personnelRosterToggle');
    const rosterModal = document.getElementById('personnelRosterModal');
    const closeRosterModal = document.getElementById('closeRosterModal');
    
    if (rosterToggle && rosterModal) {
        rosterToggle.addEventListener('click', () => {
            showPersonnelRoster();
        });
    }
    
    if (closeRosterModal && rosterModal) {
        closeRosterModal.addEventListener('click', () => {
            rosterModal.style.display = 'none';
        });
    }
    
    // Initialize Floating Chat
    const rufusToggle = document.getElementById('rufusToggle');
    const rufusChatWindow = document.getElementById('rufusChatWindow');
    const rufusMinimize = document.getElementById('rufusMinimize');
    const rufusSend = document.getElementById('rufusSend');
    const rufusInput = document.getElementById('rufusInput');
    
    if (rufusToggle && rufusChatWindow) {
        rufusToggle.addEventListener('click', () => {
            const isVisible = rufusChatWindow.style.display === 'flex';
            rufusChatWindow.style.display = isVisible ? 'none' : 'flex';
            // Hide the toggle button when chat is open
            rufusToggle.style.display = isVisible ? 'flex' : 'none';
        });
    }
    
    if (rufusMinimize && rufusChatWindow) {
        rufusMinimize.addEventListener('click', () => {
            rufusChatWindow.style.display = 'none';
            // Show the toggle button again
            if (rufusToggle) {
                rufusToggle.style.display = 'flex';
            }
        });
    }
    
    if (rufusSend && rufusInput) {
        rufusSend.addEventListener('click', () => {
            sendChatMessage();
        });
        
        rufusInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }
}

// Standalone function to show personnel roster
function showPersonnelRoster() {
    const modal = document.getElementById('personnelRosterModal');
    const modalBody = document.getElementById('personnelRosterList');
    
    if (!modal || !modalBody) return;
    
    // Check if already open, if so close it
    if (modal.style.display === 'flex') {
        modal.style.display = 'none';
        return;
    }
    
    // Clear existing content and show loading
    modalBody.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">Loading personnel...</p>';
    modal.style.display = 'flex';
    
    // Fetch and display personnel data
    fetch('/api/personnel')
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                modalBody.innerHTML = '<p style="text-align: center; color: var(--error-red);">Failed to load personnel data.</p>';
                return;
            }
            
            // Clear loading message
            modalBody.innerHTML = '';
            
            // Organize personnel by categories
            const sectionLeads = [];
            const otherPersonnel = [];
            
            data.personnel.forEach(person => {
                if (person.assignment === 'section_leads') {
                    sectionLeads.push(person);
                } else {
                    otherPersonnel.push(person);
                }
            });
            
            // Sort by rank (rough approximation)
            const rankOrder = ['TSgt', 'SSgt', 'SrA', 'A1C', 'Amn', 'AB', 'GS-', 'Mrs.', 'Mr.'];
            const sortByRank = (a, b) => {
                const aRankIndex = rankOrder.findIndex(rank => a.name.includes(rank));
                const bRankIndex = rankOrder.findIndex(rank => b.name.includes(rank));
                return aRankIndex - bRankIndex;
            };
            
            sectionLeads.sort(sortByRank);
            otherPersonnel.sort(sortByRank);
        
            // Create section leads section
            if (sectionLeads.length > 0) {
                const sectionLeadsDiv = createPersonnelSection('Section Leaders', sectionLeads, 'fas fa-star');
                modalBody.appendChild(sectionLeadsDiv);
            }
            
            // Create other personnel section
            if (otherPersonnel.length > 0) {
                const otherPersonnelDiv = createPersonnelSection('Section Personnel', otherPersonnel, 'fas fa-users');
                modalBody.appendChild(otherPersonnelDiv);
            }
        })
        .catch(error => {
            console.error('Failed to load personnel roster:', error);
            modalBody.innerHTML = '<p style="text-align: center; color: var(--error-red);">Failed to load personnel data.</p>';
        });
}

// Standalone function to send chat messages
function sendChatMessage() {
    const input = document.getElementById('rufusInput');
    const messagesContainer = document.getElementById('rufusMessages');
    
    if (!input || !messagesContainer) return;
    
    const message = input.value.trim();
    if (!message) return;
    
    // Add user message
    addRufusMessage(message, 'user');
    input.value = '';
    
    // Send to AI
    fetch('/api/ai-agent/message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: message,
            sender_id: 'calendar_user'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addRufusMessage(data.ai_response || data.response, 'agent');
        } else {
            addRufusMessage(data.ai_response || 'Sorry, I encountered an error. Please try again.', 'agent');
        }
    })
    .catch(error => {
        console.error('Chat error:', error);
        addRufusMessage('Sorry, I encountered an error. Please try again.', 'agent');
    });
}

// Standalone function to add messages to chat
function addRufusMessage(text, sender) {
    const messagesContainer = document.getElementById('rufusMessages');
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'rufus-message';
    
    const bubble = document.createElement('div');
    bubble.className = sender === 'user' ? 'rufus-user-bubble' : 'rufus-agent-bubble';
    bubble.textContent = text;
    
    messageDiv.appendChild(bubble);
    messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Helper functions
function formatAssignment(assignment) {
    const assignments = {
        'terminal': 'Terminal',
        'admin_room': 'Admin Room', 
        'floor': 'Floor',
        'section_leads': 'Section Lead',
        'unknown': 'Unknown'
    };
    return assignments[assignment] || assignment;
}

function formatStatus(status) {
    const statuses = {
        'working': 'Working',
        'available': 'Working',
        'on_leave': 'On Leave',
        'out_of_office': 'Out of Office',
        'unknown': 'Unknown'
    };
    return statuses[status] || status;
}

// Helper function to create personnel sections
function createPersonnelSection(title, personnel, iconClass) {
    const sectionDiv = document.createElement('div');
    sectionDiv.className = 'personnel-section';
    
    const titleDiv = document.createElement('div');
    titleDiv.className = 'personnel-section-title';
    titleDiv.innerHTML = `<i class="${iconClass}"></i>${title} (${personnel.length})`;
    
    const listDiv = document.createElement('div');
    listDiv.className = 'personnel-list';
    
    personnel.forEach(person => {
        const personElement = createPersonnelItem(person);
        listDiv.appendChild(personElement);
    });
    
    sectionDiv.appendChild(titleDiv);
    sectionDiv.appendChild(listDiv);
    
    return sectionDiv;
}

// Helper function to create personnel items
function createPersonnelItem(person) {
    const item = document.createElement('div');
    item.className = `personnel-item ${person.status}`;
    
    // Get initials for avatar
    const nameParts = person.name.split(' ');
    const initials = nameParts.map(part => part[0]).join('').slice(0, 2);
    
    // Format assignment name
    const assignmentName = formatAssignment(person.assignment);
    
    // Format status name
    const statusName = formatStatus(person.status);
    
    item.innerHTML = `
        <div class="personnel-avatar">${initials}</div>
        <div class="personnel-info">
            <div class="personnel-name">${person.name}</div>
            <div class="personnel-details">
                <span>${assignmentName}</span>
                <span class="personnel-status ${person.status}">${statusName}</span>
            </div>
        </div>
    `;
    
    return item;
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize the full dashboard on the section leads page
    // Other pages will just use the floating button functions
    if (window.location.pathname === '/section-leads') {
        sectionLeadsDashboard = new SectionLeadsDashboard();
    }
});