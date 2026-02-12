// XeerGPT - Updated with Cancel Search Functionality

class XeerGPTChat {
    constructor() {
        this.messagesContainer = document.getElementById('messages');
        this.userInput = document.getElementById('userInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.suggestionsContainer = document.getElementById('suggestions');
        this.welcomeScreen = document.getElementById('welcomeScreen');
        this.messagesContainerWrapper = document.getElementById('messagesContainer');
        
        this.conversationHistory = [];
        this.userId = this.generateUserId();
        this.sessionId = this.generateSessionId();
        this.isTyping = false;
        this.retryCount = 0;
        this.maxRetries = 3;
        
        // Timer properties
        this.searchStartTime = null;
        this.searchTimerInterval = null;
        
        // Abort controller for canceling requests
        this.currentAbortController = null;
        this.isSearching = false;
        
        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.loadHistory();
        this.autoResizeTextarea();
        this.setupScrollButton();
        
        const hasHistory = this.conversationHistory.length > 0;
        const hasChatted = localStorage.getItem('xeergpt_has_chatted') === 'true';
        
        if (this.welcomeScreen) {
            this.welcomeScreen.style.display = 'flex';
        }
        
        if (hasHistory || hasChatted) {
            this.showChatInterface();
            if (hasHistory) {
                this.conversationHistory.forEach(msg => this.addMessageToUI(msg));
            } else {
                this.addWelcomeMessage();
            }
        }
        
        setTimeout(() => {
            if (this.userInput) this.userInput.focus();
        }, 100);
    }

    generateUserId() {
        let userId = localStorage.getItem('xeergpt_user_id');
        if (!userId) {
            userId = 'user_' + Math.random().toString(36).substr(2, 9) + Date.now();
            localStorage.setItem('xeergpt_user_id', userId);
        }
        return userId;
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    setupScrollButton() {
        const scrollBtn = document.createElement('button');
        scrollBtn.id = 'scrollToBottomBtn';
        scrollBtn.innerHTML = '<i class="fas fa-arrow-down"></i>';
        scrollBtn.className = 'scroll-to-bottom-btn';
        scrollBtn.style.display = 'none';
        scrollBtn.title = 'Scroll to bottom';
        
        document.body.appendChild(scrollBtn);
        
        if (this.messagesContainer) {
            this.messagesContainer.addEventListener('scroll', () => {
                const isNearBottom = this.messagesContainer.scrollHeight - 
                                    this.messagesContainer.scrollTop - 
                                    this.messagesContainer.clientHeight < 100;
                
                scrollBtn.style.display = isNearBottom ? 'none' : 'flex';
            });
        }
        
        scrollBtn.addEventListener('click', () => {
            this.scrollToBottom(true);
        });
    }
    
    setupEventListeners() {
        if (this.sendBtn) {
            this.sendBtn.addEventListener('click', () => this.sendMessage());
        }
        
        if (this.userInput) {
            this.userInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            
            this.userInput.addEventListener('input', () => this.autoResizeTextarea());
        }
        
        const voiceBtn = document.getElementById('voiceBtn');
        if (voiceBtn) {
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                this.setupVoiceRecognition();
                voiceBtn.addEventListener('click', () => this.toggleVoiceInput());
            } else {
                voiceBtn.style.display = 'none';
            }
        }
        
        document.addEventListener('click', (e) => {
            if (this.suggestionsContainer && !e.target.closest('.input-container')) {
                this.hideSuggestions();
            }
        });
    }

    cancelSearch() {
        console.log('cancelSearch called');
        
        if (this.currentAbortController) {
            this.currentAbortController.abort();
            this.currentAbortController = null;
        }
        
        this.isSearching = false;
        this.hideSearchIndicator();
        
        // Add canceled message
        this.addMessageToUI({
            type: 'bot',
            content: '🛑 Search canceled. Feel free to start a new search anytime!',
            timestamp: new Date().toISOString(),
            suggestions: ['Find concerts', 'Search again', 'Help me with code']
        });
        
        this.showNotification('Search canceled', 'info');
    }

    showChatInterface() {
        if (this.welcomeScreen) this.welcomeScreen.style.display = 'none';
        if (this.messagesContainerWrapper) this.messagesContainerWrapper.style.display = 'block';
        localStorage.setItem('xeergpt_has_chatted', 'true');
        
        setTimeout(() => {
            this.scrollToBottom();
        }, 100);
    }

    addWelcomeMessage() {
        const welcomeMessage = {
            type: 'bot',
            content: "Hello! I'm XeerGPT, your AI assistant. I can help with programming (Python, JavaScript), learning new concepts, finding concerts/events in Malaysia 🎵, creative writing, and much more. How can I assist you today?",
            timestamp: new Date().toISOString(),
            suggestions: [
                "Show me Python examples",
                "Find concerts in Malaysia",
                "Explain machine learning",
                "Tell me a story"
            ]
        };
        
        this.addMessageToUI(welcomeMessage);
        this.updateSuggestions(welcomeMessage.suggestions);
    }

    async sendMessage() {
        const message = this.userInput.value.trim();
        if (!message || this.isTyping) return;
        
        if (message.length > 1000) {
            this.showNotification('Message too long. Maximum 1000 characters.', 'error');
            return;
        }
        
        this.userInput.value = '';
        this.autoResizeTextarea();
        
        if (this.welcomeScreen && this.welcomeScreen.style.display !== 'none') {
            this.showChatInterface();
        }
        
        const userMessage = {
            type: 'user',
            content: message,
            timestamp: new Date().toISOString()
        };
        
        this.addMessageToUI(userMessage);
        this.saveToHistory(userMessage);
        
        this.showTypingIndicator();
        
        try {
            const response = await this.fetchBotResponse(message);
            
            this.hideTypingIndicator();
            
            this.retryCount = 0;
            
            if (response.response.startsWith('CONCERT_SEARCH:')) {
                const [_, params] = response.response.split(':');
                const [date, keywords] = params.split('|');
                
                await this.fetchConcerts(date === 'any' ? null : date, keywords === 'all' ? null : keywords);
            } else {
                const botMessage = {
                    type: 'bot',
                    content: response.response,
                    timestamp: response.timestamp,
                    suggestions: response.suggestions || []
                };
                
                this.addMessageToUI(botMessage);
                this.saveToHistory(botMessage);
                
                this.updateSuggestions(botMessage.suggestions);
            }
            
        } catch (error) {
            this.hideTypingIndicator();
            console.error('Chat error:', error);
            
            if (this.retryCount < this.maxRetries) {
                this.retryCount++;
                this.showNotification(`Retrying... (${this.retryCount}/${this.maxRetries})`, 'info');
                setTimeout(() => this.sendMessage(), 1000 * this.retryCount);
            } else {
                this.retryCount = 0;
                this.addMessageToUI({
                    type: 'bot',
                    content: "I'm having trouble connecting right now. Please check your internet connection and try again in a moment.",
                    timestamp: new Date().toISOString(),
                    suggestions: ["Try again"]
                });
                this.showNotification('Connection error. Please try again.', 'error');
            }
        }
    }

    showSearchIndicator(searchType = 'information', query = '') {
        console.log('showSearchIndicator called:', searchType, query);
        
        if (!this.messagesContainer) {
            console.error('messagesContainer not found');
            return;
        }
        
        this.isSearching = true;
        this.hideSearchIndicator();
        
        this.searchStartTime = Date.now();
        
        const searchDiv = document.createElement('div');
        searchDiv.className = 'universal-search-indicator';
        searchDiv.id = 'universalSearchIndicator';
        
        const searchTypes = {
            'concert': { icon: '🎵', text: 'Searching for concerts' },
            'event': { icon: '🎪', text: 'Searching for events' },
            'information': { icon: '🔍', text: 'Searching' },
            'code': { icon: '💻', text: 'Generating code' },
            'data': { icon: '📊', text: 'Fetching data' },
            'api': { icon: '🌐', text: 'Calling API' },
            'news': { icon: '📰', text: 'Searching news' },
            'weather': { icon: '🌤️', text: 'Checking weather' },
            'product': { icon: '🛍️', text: 'Searching products' },
            'location': { icon: '📍', text: 'Finding locations' },
        };
        
        const searchInfo = searchTypes[searchType] || searchTypes['information'];
        
        let searchText = searchInfo.text;
        if (query && query.trim()) {
            searchText += ` for "${query}"`;
        }
        searchText += '...';
        
        searchDiv.innerHTML = `
            <div class="search-animation">
                <div class="search-icon">${searchInfo.icon}</div>
                <div class="search-text">${searchText}</div>
                <div class="search-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                <div class="search-timer" id="searchTimer">
                    <i class="fas fa-clock"></i>
                    <span class="timer-text">Elapsed: <strong>0.0s</strong></span>
                </div>
            </div>
            <div class="search-progress">
                <div class="search-progress-bar"></div>
            </div>
            <button class="cancel-search-btn" id="cancelSearchBtn">
                <i class="fas fa-times-circle"></i>
                <span>Cancel Search</span>
            </button>
        `;
        
        this.messagesContainer.appendChild(searchDiv);
        console.log('Search indicator added to DOM');
        this.scrollToBottom(true);
        
        // Add cancel button event listener
        const cancelBtn = document.getElementById('cancelSearchBtn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.cancelSearch());
        }
        
        this.startSearchTimer();
    }

    startSearchTimer() {
        console.log('startSearchTimer called');
        
        if (this.searchTimerInterval) {
            clearInterval(this.searchTimerInterval);
        }
        
        this.searchTimerInterval = setInterval(() => {
            const timerElement = document.getElementById('searchTimer');
            if (!timerElement) {
                console.log('Timer element not found, clearing interval');
                clearInterval(this.searchTimerInterval);
                return;
            }
            
            const elapsed = (Date.now() - this.searchStartTime) / 1000;
            const timerText = timerElement.querySelector('.timer-text strong');
            if (timerText) {
                timerText.textContent = elapsed.toFixed(1) + 's';
            }
        }, 100);
    }

    hideSearchIndicator() {
        console.log('hideSearchIndicator called');
        
        this.isSearching = false;
        
        if (this.searchTimerInterval) {
            clearInterval(this.searchTimerInterval);
            this.searchTimerInterval = null;
        }
        
        const indicator = document.getElementById('universalSearchIndicator');
        if (indicator) {
            const finalTime = this.searchStartTime 
                ? ((Date.now() - this.searchStartTime) / 1000).toFixed(2)
                : '0.0';
            
            console.log('Final search time:', finalTime + 's');
            
            const timerElement = indicator.querySelector('#searchTimer');
            if (timerElement) {
                timerElement.innerHTML = `
                    <i class="fas fa-check-circle" style="color: var(--success);"></i>
                    <span class="timer-text">Completed in <strong>${finalTime}s</strong></span>
                `;
                timerElement.style.color = 'var(--success)';
            }
            
            setTimeout(() => {
                indicator.style.animation = 'fadeOut 0.3s ease';
                setTimeout(() => {
                    indicator.remove();
                    console.log('Search indicator removed');
                }, 300);
            }, 800);
        } else {
            console.log('No indicator found to hide');
        }
    }

    async fetchConcerts(date, keywords) {
        console.log('fetchConcerts called:', date, keywords);
        
        // Create new abort controller for this request
        this.currentAbortController = new AbortController();
        
        try {
            const query = keywords && keywords !== 'all' ? keywords : 'concerts in Malaysia';
            this.showSearchIndicator('concert', query);
            
            const response = await fetch('/api/concerts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    date: date || '',
                    keywords: keywords || '',
                    user_id: this.userId
                }),
                signal: this.currentAbortController.signal
            });
            
            this.hideSearchIndicator();
            this.currentAbortController = null;
            
            if (!response.ok) {
                throw new Error('Failed to fetch concerts');
            }
            
            const data = await response.json();
            
            if (data.success && data.events && data.events.length > 0) {
                let concertHTML = `🎵 **Found ${data.count} concert(s)/event(s) in Malaysia:**\n\n`;
                concertHTML += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n`;
                
                data.events.forEach((event, index) => {
                    concertHTML += `**${index + 1}. ${event.name}**\n\n`;
                    concertHTML += `📅 **Date:** ${event.date}\n\n`;
                    concertHTML += `📍 **Venue:** ${event.venue}${event.city ? ', ' + event.city : ''}\n\n`;
                    concertHTML += `🔗 **[Get Tickets](${event.url})**\n\n`;
                    concertHTML += `ℹ️ **Source:** ${event.source}\n\n`;
                    
                    if (index < data.events.length - 1) {
                        concertHTML += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n`;
                    }
                });
                
                concertHTML += `\n💡 *Tip: Click the ticket links above to purchase or get more information!*`;
                
                const botMessage = {
                    type: 'bot',
                    content: concertHTML,
                    timestamp: new Date().toISOString(),
                    suggestions: ['More concerts', 'Concerts in KL', 'Upcoming events']
                };
                
                this.addMessageToUI(botMessage);
                this.saveToHistory(botMessage);
                this.updateSuggestions(botMessage.suggestions);
                
            } else {
                const message = data.message || "Sorry, I couldn't find any concerts matching your search in Malaysia. Try different keywords or dates!";
                
                const botMessage = {
                    type: 'bot',
                    content: message,
                    timestamp: new Date().toISOString(),
                    suggestions: ['Concerts in Malaysia', 'Events this month', 'Show all concerts']
                };
                
                this.addMessageToUI(botMessage);
                this.saveToHistory(botMessage);
                this.updateSuggestions(botMessage.suggestions);
            }
            
        } catch (error) {
            console.error('Concert fetch error:', error);
            
            // Check if it was aborted (canceled by user)
            if (error.name === 'AbortError') {
                console.log('Fetch was aborted by user');
                return; // Don't show error message, cancelSearch() already handled it
            }
            
            this.hideSearchIndicator();
            this.currentAbortController = null;
            
            this.addMessageToUI({
                type: 'bot',
                content: "Sorry, I encountered an error while searching for concerts. Please try again in a moment!",
                timestamp: new Date().toISOString(),
                suggestions: ['Try again', 'Help me with code']
            });
            
            this.showNotification('Failed to fetch concerts', 'error');
        }
    }

    async fetchBotResponse(message) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    user_id: this.userId,
                    session_id: this.sessionId
                }),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                if (response.status === 429) {
                    throw new Error('Rate limit exceeded. Please wait a moment.');
                }
                throw new Error(`Server error: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to get response');
            }
            
            return data;
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('Request timed out. Please try again.');
            }
            throw error;
        }
    }

    addMessageToUI(message) {
        if (!this.messagesContainer) return;
        
        const messageDiv = document.createElement('div');
        // Fix: Ensure 'bot' type becomes 'assistant-message' for CSS
        const messageClass = message.type === 'user' ? 'user-message' : 'assistant-message';
        messageDiv.className = `message ${messageClass}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = message.type === 'user' 
            ? '<i class="fas fa-user"></i>' 
            : '<i class="fas fa-robot"></i>';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const headerDiv = document.createElement('div');
        headerDiv.className = 'message-header';
        
        const senderSpan = document.createElement('span');
        senderSpan.className = 'message-sender';
        senderSpan.textContent = message.type === 'user' ? 'You' : 'XeerGPT';
        
        const timeSpan = document.createElement('span');
        timeSpan.className = 'message-time';
        try {
            const date = new Date(message.timestamp);
            timeSpan.textContent = date.toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        } catch (e) {
            timeSpan.textContent = new Date().toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        }
        
        headerDiv.appendChild(senderSpan);
        headerDiv.appendChild(timeSpan);
        
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        
        const formattedContent = this.formatMessage(message.content);
        textDiv.innerHTML = formattedContent;
        
        contentDiv.appendChild(headerDiv);
        contentDiv.appendChild(textDiv);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        
        this.messagesContainer.appendChild(messageDiv);
        
        this.scrollToBottom(true);
    }

    formatMessage(content) {
        if (!content) return '';
        
        let formatted = content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        
        formatted = formatted.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            const language = lang || 'code';
            return `<pre class="code-block language-${language}"><code>${code.trim()}</code></pre>`;
        });
        
        formatted = formatted.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
        
        formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        
        formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        
        formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="concert-link">$1</a>');
        
        formatted = formatted.replace(/\n/g, '<br>');
        
        const lines = formatted.split('<br>');
        let inList = false;
        const formattedLines = [];
        
        for (let line of lines) {
            const trimmedLine = line.trim();
            if (trimmedLine.match(/^[•\-\*]\s+/)) {
                if (!inList) {
                    formattedLines.push('<ul class="message-list">');
                    inList = true;
                }
                formattedLines.push(`<li>${trimmedLine.replace(/^[•\-\*]\s+/, '')}</li>`);
            } else {
                if (inList) {
                    formattedLines.push('</ul>');
                    inList = false;
                }
                if (trimmedLine) {
                    formattedLines.push(trimmedLine);
                }
            }
        }
        
        if (inList) {
            formattedLines.push('</ul>');
        }
        
        return formattedLines.join('<br>');
    }

    showTypingIndicator() {
        this.isTyping = true;
        if (this.sendBtn) this.sendBtn.disabled = true;
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'flex';
        }
        this.scrollToBottom(true);
    }

    hideTypingIndicator() {
        this.isTyping = false;
        if (this.sendBtn) this.sendBtn.disabled = false;
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'none';
        }
    }

    updateSuggestions(suggestions) {
        if (!this.suggestionsContainer) return;
        
        if (!suggestions || suggestions.length === 0) {
            this.suggestionsContainer.innerHTML = '';
            return;
        }
        
        this.suggestionsContainer.innerHTML = '';
        
        suggestions.slice(0, 4).forEach(suggestion => {
            const button = document.createElement('button');
            button.className = 'suggestion-btn';
            button.textContent = suggestion;
            button.addEventListener('click', () => {
                if (this.userInput) {
                    this.userInput.value = suggestion;
                    this.autoResizeTextarea();
                    this.userInput.focus();
                    this.sendMessage();
                }
            });
            this.suggestionsContainer.appendChild(button);
        });
    }

    hideSuggestions() {
        if (this.suggestionsContainer) {
            this.suggestionsContainer.innerHTML = '';
        }
    }

    autoResizeTextarea() {
        if (!this.userInput) return;
        
        this.userInput.style.height = 'auto';
        const newHeight = Math.min(this.userInput.scrollHeight, 150);
        this.userInput.style.height = newHeight + 'px';
    }

    setupVoiceRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = 'en-US';
        this.isListening = false;
        
        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            if (this.userInput) {
                this.userInput.value = transcript;
                this.autoResizeTextarea();
            }
            this.showNotification('Voice input received', 'success');
        };
        
        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.showNotification('Voice input failed: ' + event.error, 'error');
            this.isListening = false;
        };
        
        this.recognition.onend = () => {
            this.isListening = false;
            const voiceBtn = document.getElementById('voiceBtn');
            if (voiceBtn) {
                voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
                voiceBtn.title = 'Voice input';
            }
        };
    }

    toggleVoiceInput() {
        if (!this.recognition) return;
        
        const voiceBtn = document.getElementById('voiceBtn');
        
        if (this.isListening) {
            this.recognition.stop();
            this.isListening = false;
            if (voiceBtn) {
                voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
                voiceBtn.title = 'Voice input';
            }
        } else {
            try {
                this.recognition.start();
                this.isListening = true;
                if (voiceBtn) {
                    voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
                    voiceBtn.title = 'Stop listening';
                }
                this.showNotification('Listening... Speak now', 'info');
            } catch (error) {
                console.error('Voice input error:', error);
                this.showNotification('Voice input not available', 'error');
            }
        }
    }

    clearChat() {
        if (confirm('Start a new chat? This will clear the current conversation.')) {
            if (this.messagesContainer) {
                this.messagesContainer.innerHTML = '';
            }
            this.conversationHistory = [];
            localStorage.removeItem('xeergpt_chat_history');
            this.hideSuggestions();
            
            fetch('/api/clear', { method: 'POST' }).catch(console.error);
            
            this.addWelcomeMessage();
            
            this.updateChatHistory();
            
            this.showNotification('Chat cleared. Starting fresh!', 'success');
        }
    }

    saveToHistory(message) {
        this.conversationHistory.push(message);
        
        if (this.conversationHistory.length > 100) {
            this.conversationHistory = this.conversationHistory.slice(-100);
        }
        
        try {
            localStorage.setItem('xeergpt_chat_history', JSON.stringify(this.conversationHistory));
        } catch (e) {
            console.error('Failed to save to localStorage:', e);
            if (e.name === 'QuotaExceededError') {
                this.conversationHistory = this.conversationHistory.slice(-50);
                localStorage.setItem('xeergpt_chat_history', JSON.stringify(this.conversationHistory));
            }
        }
        
        this.updateChatHistory();
    }

    loadHistory() {
        try {
            const saved = localStorage.getItem('xeergpt_chat_history');
            if (saved) {
                this.conversationHistory = JSON.parse(saved);
            }
        } catch (error) {
            console.error('Failed to load history:', error);
            this.conversationHistory = [];
            localStorage.removeItem('xeergpt_chat_history');
        }
    }

    updateChatHistory() {
        const historyItems = document.getElementById('historyItems');
        if (!historyItems) return;
        
        historyItems.innerHTML = '';
        
        const newChatItem = document.createElement('div');
        newChatItem.className = 'history-item active';
        newChatItem.innerHTML = '<i class="fas fa-message"></i><span>New Conversation</span>';
        newChatItem.addEventListener('click', () => this.clearChat());
        historyItems.appendChild(newChatItem);
        
        const recentConversations = this.conversationHistory
            .filter(msg => msg.type === 'user')
            .slice(-10)
            .reverse();
        
        recentConversations.forEach((msg, index) => {
            const item = document.createElement('div');
            item.className = 'history-item';
            item.innerHTML = `<i class="fas fa-message"></i><span>${this.truncateText(msg.content, 30)}</span>`;
            item.title = msg.content;
            item.addEventListener('click', () => {
                this.showNotification('Loading conversation...', 'info');
            });
            historyItems.appendChild(item);
        });
    }

    truncateText(text, maxLength) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    scrollToBottom(force = false) {
        if (!this.messagesContainer) return;
        
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
            });
        });
    }

    showNotification(message, type = 'info') {
        const existing = document.querySelector('.notification');
        if (existing) existing.remove();
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        const colors = {
            'error': '#f44336',
            'success': '#4caf50',
            'info': '#2196f3'
        };
        
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: ${colors[type] || colors.info};
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            animation: slideInRight 0.3s ease;
            max-width: 300px;
            word-break: break-word;
            font-size: 14px;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }
        .code-block {
            background: var(--bg-secondary);
            border: 1px solid var(--border-light);
            border-radius: 8px;
            padding: 16px;
            overflow-x: auto;
            margin: 12px 0;
        }
        .inline-code {
            background: var(--bg-secondary);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: var(--font-mono);
            font-size: 0.9em;
            color: var(--accent-primary);
        }
        .message-list {
            margin: 8px 0;
            padding-left: 24px;
        }
        .message-list li {
            margin-bottom: 6px;
        }
        .concert-link {
            color: var(--accent-primary);
            text-decoration: none;
            font-weight: 500;
            border-bottom: 1px solid var(--accent-primary);
            transition: all 0.2s ease;
        }
        .concert-link:hover {
            color: var(--accent-hover);
            border-bottom-color: var(--accent-hover);
        }
        .cancel-search-btn {
            margin-top: 12px;
            padding: 10px 20px;
            background: #f44336;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
            width: 100%;
            justify-content: center;
        }
        .cancel-search-btn:hover {
            background: #d32f2f;
            transform: scale(1.02);
        }
        .cancel-search-btn:active {
            transform: scale(0.98);
        }
        .cancel-search-btn i {
            font-size: 16px;
        }
    `;
    document.head.appendChild(style);
    
   // AFTER (only initializes if AddOnChtHistryDBCpyBtn hasn't already run)
    if (document.getElementById('messages') && !window.xeerGPT) {
        window.xeerGPT = new XeerGPTChat();
    }
    
    document.querySelectorAll('.starter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const prompt = this.getAttribute('data-prompt');
            if (window.xeerGPT && window.xeerGPT.userInput) {
                window.xeerGPT.userInput.value = prompt;
                window.xeerGPT.sendMessage();
            } else {
                window.xeerGPT = new XeerGPTChat();
                setTimeout(() => {
                    if (window.xeerGPT.userInput) {
                        window.xeerGPT.userInput.value = prompt;
                        window.xeerGPT.sendMessage();
                    }
                }, 100);
            }
        });
    });
    
    document.querySelectorAll('.welcome-screen .suggestion-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const prompt = this.getAttribute('data-prompt') || this.textContent;
            if (window.xeerGPT && window.xeerGPT.userInput) {
                window.xeerGPT.userInput.value = prompt;
                window.xeerGPT.sendMessage();
            }
        });
    });
    
    document.body.classList.add('loaded');
});