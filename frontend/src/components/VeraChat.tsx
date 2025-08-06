import { useState, useEffect, useRef } from 'react';
import { Bot, Minus, Send } from 'lucide-react';
import { apiService } from '../services/api';
import './VeraChat.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

const VeraChat = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [sessionId] = useState(() => `web_user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Check authentication status and initialize conversation
  useEffect(() => {
    // Check if already authenticated
    const storedAuth = localStorage.getItem('veraAuthenticated');
    if (storedAuth === 'true') {
      setIsAuthenticated(true);
      // Load saved authenticated conversation
      const savedMessages = localStorage.getItem(`vera_conversation_${sessionId}`);
      if (savedMessages) {
        setMessages(JSON.parse(savedMessages));
      } else {
        // Initialize with welcome message
        initializeAuthenticatedChat();
      }
    } else {
      // Not authenticated - show security check
      const securityMessage: Message = {
        role: 'assistant',
        content: 'Vera Security Check\n\nWhat is the special code?',
        timestamp: new Date().toISOString()
      };
      setMessages([securityMessage]);
    }
  }, [sessionId]);

  // Listen for toggle event from Section Leads page
  useEffect(() => {
    const handleToggleVera = () => {
      setIsOpen(!isOpen);
    };
    
    window.addEventListener('toggleVera', handleToggleVera);
    return () => window.removeEventListener('toggleVera', handleToggleVera);
  }, [isOpen]);

  const initializeAuthenticatedChat = () => {
    const welcomeMessage: Message = {
      role: 'assistant',
      content: 'Vera ready to help!\n\n• Update personnel: "A1C Davis to admin room"\n• Ask questions about staffing',
      timestamp: new Date().toISOString()
    };
    setMessages([welcomeMessage]);
    localStorage.setItem(`vera_conversation_${sessionId}`, JSON.stringify([welcomeMessage]));
  };

  // Save messages to localStorage whenever messages change (only if authenticated)
  useEffect(() => {
    if (messages.length > 0 && isAuthenticated) {
      localStorage.setItem(`vera_conversation_${sessionId}`, JSON.stringify(messages));
    }
  }, [messages, sessionId, isAuthenticated]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const toggleChat = () => {
    setIsOpen(!isOpen);
    if (!isOpen) {
      // Scroll to bottom when opening
      setTimeout(scrollToBottom, 100);
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date().toISOString()
    };

    // Add user message immediately
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    const messageToSend = inputValue.trim();
    setInputValue('');
    setIsLoading(true);

    try {
      // Check authentication first
      if (!isAuthenticated) {
        if (messageToSend.toLowerCase() === 'homeomorphism') {
          // Correct security code
          setIsAuthenticated(true);
          localStorage.setItem('veraAuthenticated', 'true');
          
          const welcomeMessage: Message = {
            role: 'assistant',
            content: 'Vera ready to help!\n\n• Update personnel: "A1C Davis to admin room"\n• Ask questions about staffing',
            timestamp: new Date().toISOString()
          };
          
          setMessages(prev => [...prev, welcomeMessage]);
          setIsLoading(false);
          return;
        } else {
          // Wrong security code
          const deniedMessage: Message = {
            role: 'assistant',
            content: 'Access denied. What is the special code?',
            timestamp: new Date().toISOString()
          };
          
          setMessages(prev => [...prev, deniedMessage]);
          setIsLoading(false);
          return;
        }
      }

      // Send authenticated message to API
      const response = await apiService.sendMessage(messageToSend, sessionId);
      
      if (response.data.success) {
        const assistantMessage: Message = {
          role: 'assistant',
          content: response.data.ai_response || response.data.response,
          timestamp: new Date().toISOString()
        };
        
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error(response.data.error || 'Failed to get response');
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again later.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearConversation = () => {
    if (isAuthenticated) {
      initializeAuthenticatedChat();
    } else {
      const securityMessage: Message = {
        role: 'assistant',
        content: 'Vera Security Check\n\nWhat is the special code?',
        timestamp: new Date().toISOString()
      };
      setMessages([securityMessage]);
    }
    localStorage.removeItem(`vera_conversation_${sessionId}`);
  };

  const logout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem('veraAuthenticated');
    localStorage.removeItem(`vera_conversation_${sessionId}`);
    const securityMessage: Message = {
      role: 'assistant',
      content: 'Vera Security Check\n\nWhat is the special code?',
      timestamp: new Date().toISOString()
    };
    setMessages([securityMessage]);
  };

  const formatMessageContent = (content: string, isFirst: boolean = false) => {
    if (isFirst && content.includes('Vera Security Check')) {
      return content.split('\n').map((line, i) => (
        <div key={i}>
          {i === 0 ? <strong>Vera</strong> : ''} 
          {line.replace('Vera Security Check', 'Security Check')}
        </div>
      ));
    }
    
    return content.split('\n').map((line, i) => (
      <div key={i}>{line || '\u00A0'}</div>
    ));
  };

  return (
    <div className="rufus-chat-container">
      {/* Chat Window */}
      {isOpen && (
        <div className="rufus-chat-window">
          <div className="rufus-header">
            <div className="rufus-title">
              <Bot size={20} />
              <span>Vera</span>
              {isAuthenticated && (
                <span className="memory-indicator" title="Authenticated & Memory active">
                  🔓💭
                </span>
              )}
            </div>
            <div className="rufus-controls">
              {isAuthenticated && (
                <button 
                  className="rufus-logout" 
                  onClick={logout}
                  title="Logout"
                  aria-label="Logout"
                >
                  🔒
                </button>
              )}
              <button 
                className="rufus-clear" 
                onClick={clearConversation}
                title="Clear conversation"
                aria-label="Clear conversation"
              >
                🗑️
              </button>
              <button 
                className="rufus-minimize" 
                onClick={toggleChat}
                aria-label="Close chat"
              >
                <Minus size={16} />
              </button>
            </div>
          </div>
          
          <div className="rufus-body">
            {/* Message History */}
            <div className="rufus-messages">
              {messages.map((message, index) => (
                <div key={`${message.timestamp}-${index}`} className={message.role === 'assistant' ? 'rufus-agent-bubble' : 'rufus-user-bubble'}>
                  {message.role === 'assistant' && (
                    <div className="rufus-avatar">
                      <Bot size={16} />
                    </div>
                  )}
                  {message.role === 'user' && (
                    <div className="rufus-user-avatar">U</div>
                  )}
                  <div className="rufus-message-content">
                    {formatMessageContent(message.content, index === 0 && !isAuthenticated)}
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="rufus-agent-bubble">
                  <div className="rufus-avatar">
                    <Bot size={16} />
                  </div>
                  <div className="rufus-message-content">
                    <div className="loading-indicator">
                      <div className="loading-circle"></div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
            
            {/* Message Input */}
            <div className="rufus-input-area">
              <div className="conversation-stats">
                {isAuthenticated && messages.length > 1 && (
                  <span className="message-count">
                    {Math.floor((messages.length - 1) / 2)} exchanges • Authenticated
                  </span>
                )}
                {!isAuthenticated && (
                  <span className="security-notice">
                    🔒 Enter security code to access Vera
                  </span>
                )}
              </div>
              <div className="rufus-input-wrapper">
                <input 
                  type="text" 
                  className="rufus-input" 
                  placeholder={isAuthenticated ? "Ask me anything about section operations..." : "Enter the special code..."}
                  maxLength={500}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyPress}
                  disabled={isLoading}
                />
                <button 
                  className="rufus-send"
                  onClick={sendMessage}
                  disabled={!inputValue.trim() || isLoading}
                  aria-label="Send message"
                >
                  <Send size={16} />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VeraChat;