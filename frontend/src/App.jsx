import { useState, useRef, useEffect } from 'react'
import './App.css'
import chatbotIcon from './assets/images/chatbotIcon.png'
import userAvatar from './assets/images/uAvatar.png'
import logo from './assets/images/logo.png'
import messageIcon from './assets/images/message.png'


function App() {
  // State for storing chat messages (resets on refresh)
  const [messages, setMessages] = useState([
    {
      text: "What would you like to know about Andy?",
      isUser: false,
      timestamp: new Date()
    }
  ])
  
  // State for the current input text
  const [inputText, setInputText] = useState('')
  
  // State to track when AI is "thinking"
  const [isLoading, setIsLoading] = useState(false)
  
  // State for mobile sidebar visibility
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  
  // Reference to auto-scroll to the latest message
  const messagesEndRef = useRef(null)

  // API base URL - uses environment variable or defaults to localhost
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

  // Function to scroll to the bottom of the chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  // Scroll down when messages change
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Function to handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!inputText.trim() || isLoading) return

    // Add user message to chat
    const userMessage = {
      text: inputText,
      isUser: true,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    setInputText('')
    setIsLoading(true)

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: inputText })
      })

      const data = await response.json()
      
      const botMessage = {
        text: data.success ? data.response : `Error: ${data.response}`,
        isUser: false,
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, botMessage])
      
    } catch (error) {
      const errorMessage = {
        text: `Network error: Could not connect to the backend server. Please make sure the backend is running. Error: ${error.message}`,
        isUser: false,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  // Function to clear chat history (reset to initial state)
  const clearChat = () => {
    setMessages([
      {
        text: "What would you like to know about Andy?",
        isUser: false,
        timestamp: new Date()
      }
    ])
  }

  // Close sidebar when clicking outside on mobile
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (window.innerWidth < 768 && 
          isSidebarOpen && 
          !e.target.closest('.sidebar') && 
          !e.target.closest('.mobile-menu-toggle')) {
        setIsSidebarOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isSidebarOpen])

  return (
    <div className="app">
      {/* Mobile Menu Toggle Button */}
      {window.innerWidth < 768 && (
        <button 
          className="mobile-menu-toggle"
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          aria-label="Toggle menu"
        >
          <span></span>
        </button>
      )}

      {/* Sidebar Section */}
      <div className={`sidebar ${isSidebarOpen ? 'active' : ''}`}>
       <div className="logo">
    {/* Mobile Logo - AAA in colored box */}
    <div className="mobile-logo">
      AAA
    </div>
    
    {/* Desktop Logo - Full logo */}
    <div className="desktop-logo">
      <img src={logo} alt="Ask Andy Anything Logo" className="logo-image" />
      <span className="logo-text">Ask Andy Anything</span>
    </div>
  </div>
  
  <button className="new-chat-btn" onClick={clearChat}>
    + New Chat
  </button>
        </div>
        
        {/* Chat history section */}
        <div className="chat-history">
          <div className="history-header">Current Session Only</div>
          <div className="history-items">
            <div className="history-item">Chats reset on refresh</div>
            <div className="history-item">Ask me anything about Andy!</div>
          </div>
        </div>
        
        <div className="sidebar-footer">
          <div className="user-profile">
            <div className="user-avatar">
              <img src={userAvatar} alt="User Avatar" className="sidebar-avatar-image" />
            </div>
            <span className="user-name">User</span>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="main-content">
        <div className="chat-header">
          <h1>ASK ANDY ANYTHING</h1>
          <p>Ask this AI trained on Andy's data anything you want to know about him</p>
        </div>
        
        <div className="chat-messages">
          {messages.map((message, index) => (
            <div key={index} className={`message ${message.isUser ? 'user-message' : 'bot-message'}`}>
              <div className="message-avatar">
                {message.isUser ? (
                  <img src={userAvatar} alt="User Avatar" className="message-avatar-image" />
                ) : (
                  <img src={chatbotIcon} alt="AI Avatar" className="message-avatar-image" />
                )}
              </div>
              <div className="message-content">
                <div className="message-text">{message.text}</div>
                <div className="message-time">
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          ))}
          
          {/* Loading Indicator */}
          {isLoading && (
            <div className="message bot-message">
              <div className="message-avatar">
                <img src={chatbotIcon} alt="AI Avatar" className="message-avatar-image" />
              </div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          
          {/* Invisible element for auto-scrolling */}
          <div ref={messagesEndRef} />
        </div>
        
        {/* Input Area */}
        <div className="chat-input-container">
          <form onSubmit={handleSubmit} className="input-form">
            <div className="input-wrapper">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Ask something about Andy..."
                disabled={isLoading}
              />
              <button type="submit" disabled={isLoading || !inputText.trim()} className="send-button">
                <img src={messageIcon} alt="Send message" className="send-button-icon" />
              </button>
            </div>
          </form>
          <div className="disclaimer">
            Chats are not saved between sessions. API: {API_BASE_URL}
          </div>
        </div>
      </div>

      {/* Overlay for mobile when sidebar is open */}
      {isSidebarOpen && window.innerWidth < 768 && (
        <div 
          className="sidebar-overlay active"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}
    </div>
  )
}

export default App