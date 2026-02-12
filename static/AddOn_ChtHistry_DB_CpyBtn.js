class AddOnChtHistryDBCpyBtn {
    constructor() {
        this.messages = [];
        this.currentConversationId = null;
        this.isTyping = false;
        this.selectedModel = localStorage.getItem('xeergpt_selected_model') || 'gemini-1.5-flash';
        this.availableModels = {};
        
        // Concert search properties
        this.searchStartTime = null;
        this.searchTimerInterval = null;
        this.currentAbortController = null;
        this.isSearching = false;
        
        this.initializeElements();
        this.attachEventListeners();
        this.loadConversations();
        this.loadAvailableModels();
        this.setupMarkdown();
        
        console.log('✅ XeerGPT Chat initialized');
    }

    initializeElements() {
        this.welcomeScreen = document.getElementById('welcomeScreen');
        this.messagesContainer = document.getElementById('messagesContainer');
        this.messagesDiv = document.getElementById('messages');
        this.userInput = document.getElementById('userInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.historyItems = document.getElementById('historyItems');
        this.newChatBtn = document.getElementById('newChatBtn');
        
        // Model selector elements (beside send button)
        this.modelSelectorBtn = document.getElementById('modelSelectorBtn');
        this.modelDropdown = document.getElementById('modelDropdown');
        this.selectedModelIcon = document.getElementById('selectedModelIcon');
        this.selectedModelName = document.getElementById('selectedModelName');
    }

    async loadAvailableModels() {
        try {
            const response = await fetch('/api/models');
            const data = await response.json();
            
            if (data.success) {
                this.availableModels = data.providers;
                this.renderModelSelector();
                this.updateSelectedModelDisplay();
                console.log('✅ Loaded models:', this.availableModels);
            }
        } catch (error) {
            console.error('❌ Error loading models:', error);
        }
    }

    renderModelSelector() {
        if (!this.modelDropdown) return;
        
        this.modelDropdown.innerHTML = '';
        
        Object.entries(this.availableModels).forEach(([providerKey, providerData], index) => {
            // Provider header
            const header = document.createElement('div');
            header.className = 'model-dropdown-header';
            
            // Get the first model's icon for the provider header
            const firstModelIcon = Object.values(providerData.models)[0]?.icon || '🤖';
            
            header.innerHTML = `
                <span>${firstModelIcon}</span>
                <span>${providerData.display_name}</span>
            `;
            this.modelDropdown.appendChild(header);
            
            // Model group
            const group = document.createElement('div');
            group.className = 'model-group';
            
            Object.entries(providerData.models).forEach(([modelKey, modelInfo]) => {
                const item = document.createElement('div');
                item.className = 'model-item';
                if (modelKey === this.selectedModel) {
                    item.classList.add('selected');
                }
                
                item.innerHTML = `
                    <span class="model-item-icon">${modelInfo.icon}</span>
                    <div class="model-item-info">
                        <div class="model-item-name">${modelInfo.name}</div>
                        <div class="model-item-desc">${modelInfo.description}</div>
                    </div>
                    <i class="fas fa-check model-item-check"></i>
                `;
                
                item.addEventListener('click', () => {
                    this.selectModel(modelKey, modelInfo.icon, modelInfo.name);
                    this.closeModelDropdown();
                });
                
                group.appendChild(item);
            });
            
            this.modelDropdown.appendChild(group);
            
            // Add divider between providers (except last)
            if (index < Object.keys(this.availableModels).length - 1) {
                const divider = document.createElement('div');
                divider.className = 'model-divider';
                this.modelDropdown.appendChild(divider);
            }
        });
    }

    selectModel(modelKey, icon, name) {
        this.selectedModel = modelKey;
        localStorage.setItem('xeergpt_selected_model', modelKey);
        
        // Update UI
        this.updateSelectedModelDisplay(icon, name);
        this.renderModelSelector(); // Re-render to update selected state
        
        console.log(`🤖 Selected model: ${modelKey}`);
        this.showNotification(`Switched to ${name}`, 'success');
    }

    updateSelectedModelDisplay(icon, name) {
        if (!icon || !name) {
            // Find current model info
            for (const provider of Object.values(this.availableModels)) {
                if (provider.models[this.selectedModel]) {
                    icon = provider.models[this.selectedModel].icon;
                    name = provider.models[this.selectedModel].name;
                    break;
                }
            }
        }
        
        if (this.selectedModelIcon) {
            this.selectedModelIcon.textContent = icon || '🤖';
        }
        if (this.selectedModelName) {
            // Shorten name for button
            const shortName = name ? name.replace('Gemini ', '').replace('Llama ', '').replace('DeepSeek ', '') : 'Model';
            this.selectedModelName.textContent = shortName;
        }
    }

    closeModelDropdown() {
        if (this.modelDropdown) {
            this.modelDropdown.classList.remove('open');
        }
        if (this.modelSelectorBtn) {
            this.modelSelectorBtn.classList.remove('open');
        }
    }

    attachEventListeners() {
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
            
            this.userInput.addEventListener('input', () => {
                this.userInput.style.height = 'auto';
                this.userInput.style.height = Math.min(this.userInput.scrollHeight, 200) + 'px';
            });
        }
        
        if (this.newChatBtn) {
            this.newChatBtn.addEventListener('click', () => this.createNewChat());
        }
        
        // Model selector toggle
        if (this.modelSelectorBtn) {
            this.modelSelectorBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const isOpen = this.modelDropdown.classList.toggle('open');
                this.modelSelectorBtn.classList.toggle('open', isOpen);
            });
        }
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.model-selector-dropdown')) {
                this.closeModelDropdown();
            }
        });
    }

    setupMarkdown() {
        if (typeof marked === 'undefined') {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
            document.head.appendChild(script);
        }
        
        if (typeof hljs === 'undefined') {
            const hljsScript = document.createElement('script');
            hljsScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js';
            document.head.appendChild(hljsScript);
            
            const hljsCSS = document.createElement('link');
            hljsCSS.rel = 'stylesheet';
            hljsCSS.href = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css';
            document.head.appendChild(hljsCSS);
        }
    }

    async loadConversations() {
        try {
            const response = await fetch('/api/conversations');
            if (!response.ok) throw new Error('Failed to load conversations');
            
            const data = await response.json();
            this.renderConversationHistory(data.conversations || []);
            console.log(`📋 Loaded ${data.conversations?.length || 0} conversations`);
        } catch (error) {
            console.error('❌ Error loading conversations:', error);
        }
    }

    renderConversationHistory(conversations) {
        if (!this.historyItems) return;
        
        this.historyItems.innerHTML = '';
        
        const newChatItem = document.createElement('div');
        newChatItem.className = 'history-item' + (this.currentConversationId === null ? ' active' : '');
        newChatItem.innerHTML = `<i class="fas fa-message"></i><span>New Conversation</span>`;
        newChatItem.addEventListener('click', (e) => {
            e.preventDefault();
            this.createNewChat();
        });
        this.historyItems.appendChild(newChatItem);
        
        if (conversations && conversations.length > 0) {
            conversations.forEach(conv => {
                const item = document.createElement('div');
                item.className = 'history-item';
                if (conv.id === this.currentConversationId) {
                    item.classList.add('active');
                }
                
                item.innerHTML = `
                    <i class="fas fa-message"></i>
                    <span class="conversation-title" data-id="${conv.id}">${this.escapeHtml(conv.title)}</span>
                    <button class="delete-chat-btn" data-id="${conv.id}" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                `;
                
                item.addEventListener('click', (e) => {
                    if (!e.target.closest('.delete-chat-btn')) {
                        this.loadConversation(conv.id);
                    }
                });
                
                const deleteBtn = item.querySelector('.delete-chat-btn');
                if (deleteBtn) {
                    deleteBtn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        this.deleteConversation(conv.id);
                    });
                }
                
                this.historyItems.appendChild(item);
            });
        }
    }

    async loadConversation(conversationId) {
        try {
            const response = await fetch(`/api/conversations/${conversationId}/messages`);
            if (!response.ok) throw new Error('Failed to load messages');
            
            const data = await response.json();
            this.currentConversationId = conversationId;
            
            if (this.messagesDiv) this.messagesDiv.innerHTML = '';
            if (this.welcomeScreen) this.welcomeScreen.style.display = 'none';
            if (this.messagesContainer) this.messagesContainer.style.display = 'flex';
            
            if (data.messages && data.messages.length > 0) {
                data.messages.forEach(msg => {
                    this.displayMessage(msg.content, msg.role, false);
                });
            }
            
            this.updateSidebarActiveState();
            this.scrollToBottom();
            if (this.userInput) this.userInput.focus();
        } catch (error) {
            console.error('❌ Error loading conversation:', error);
        }
    }

    updateSidebarActiveState() {
        document.querySelectorAll('.history-item').forEach(item => item.classList.remove('active'));
        
        if (this.currentConversationId === null) {
            const newChatItem = this.historyItems?.querySelector('.history-item');
            if (newChatItem) newChatItem.classList.add('active');
        } else {
            const activeItem = Array.from(this.historyItems?.children || []).find(
                child => {
                    const titleSpan = child.querySelector('.conversation-title');
                    return titleSpan && parseInt(titleSpan.dataset.id) === this.currentConversationId;
                }
            );
            if (activeItem) activeItem.classList.add('active');
        }
    }

    async deleteConversation(conversationId) {
        if (!confirm('Delete this conversation?')) return;
        
        try {
            const response = await fetch(`/api/conversations/${conversationId}`, {
                method: 'DELETE'
            });
            
            if (conversationId === this.currentConversationId) {
                this.createNewChat();
            }
            this.loadConversations();
        } catch (error) {
            console.error('Error deleting conversation:', error);
        }
    }

    createNewChat() {
        this.currentConversationId = null;
        if (this.messagesDiv) this.messagesDiv.innerHTML = '';
        if (this.welcomeScreen) this.welcomeScreen.style.display = 'none';
        if (this.messagesContainer) this.messagesContainer.style.display = 'flex';
        if (this.userInput) {
            this.userInput.value = '';
            this.userInput.style.height = 'auto';
            this.userInput.focus();
        }
        this.updateSidebarActiveState();
    }

    async sendMessage() {
        const message = this.userInput?.value.trim();

        // Check if there's pasted content in the preview
        let fullMessage = message;
        if (window.pasteHandler && window.pasteHandler.hasPastedContent()) {
            const pastedContent = window.pasteHandler.getPastedContent();
            
            // Combine pasted content with user message
            if (message) {
                fullMessage = `${message}\n\n\`\`\`\n${pastedContent}\n\`\`\``;
            } else {
                fullMessage = `\`\`\`\n${pastedContent}\n\`\`\``;
            }
            
            // Clear the preview
            window.pasteHandler.hidePreview();
            window.pasteHandler.clearPastedContent();
        }

        if (!message || this.isTyping) return;

        console.log(`📤 Sending with model: ${this.selectedModel}`);

        if (this.welcomeScreen?.style.display !== 'none') {
            this.welcomeScreen.style.display = 'none';
            this.messagesContainer.style.display = 'flex';
        }

        this.displayMessage(message, 'user');
        if (this.userInput) {
            this.userInput.value = '';
            this.userInput.style.height = 'auto';
        }

        this.showTypingIndicator();

        try {
            await this.fetchBotResponseStreaming(message);
        } catch (error) {
            this.hideTypingIndicator();
            console.error('❌ Chat error:', error);
            this.displayMessage('Connection error. Please try again.', 'assistant');
        }

        this.scrollToBottom();
    }

    async fetchBotResponseStreaming(message) {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                conversation_id: this.currentConversationId,
                model: this.selectedModel
            }),
        });

        if (!response.ok) throw new Error(`Server error: ${response.status}`);

        this.hideTypingIndicator();
        
        // Create streaming message element
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant-message';

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = '<div class="logo-icon-small">X</div>';

        // Create wrapper for content + copy button
        const contentWrapper = document.createElement('div');
        contentWrapper.className = 'message-content-wrapper';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = '<span class="typing-cursor">▋</span>';

        contentWrapper.appendChild(contentDiv);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentWrapper);
        this.messagesDiv.appendChild(messageDiv);
        this.scrollToBottom();

        // Read stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let fullContent = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.slice(6));
                    
                    if (data.type === 'conversation_id') {
                        const wasNew = this.currentConversationId === null;
                        this.currentConversationId = data.conversation_id;
                        if (wasNew) await this.loadConversations();
                        
                    } else if (data.type === 'content') {
                        fullContent += data.content;
                        contentDiv.innerHTML = this.renderMarkdown(fullContent) + '<span class="typing-cursor">▋</span>';
                        this.scrollToBottom();
                        
                    } else if (data.type === 'done') {
                        contentDiv.innerHTML = this.renderMarkdown(fullContent);
                        setTimeout(() => {
                            this.addCopyButtons(contentDiv);
                            this.highlightCode(contentDiv);
                        }, 0);
                        
                        // ADD MESSAGE COPY BUTTON BELOW CONTENT
                        const copyBtn = this.createMessageCopyButton(fullContent);
                        contentWrapper.appendChild(copyBtn);
                        
                    } else if (data.type === 'error') {
                        contentDiv.innerHTML = this.renderMarkdown(data.message);
                        
                        // Add copy button even for errors
                        const copyBtn = this.createMessageCopyButton(data.message);
                        contentWrapper.appendChild(copyBtn);
                    }
                }
            }
        }
    }

    // NEW METHOD: Create message copy button
    createMessageCopyButton(content) {
        const copyBtn = document.createElement('button');
        copyBtn.className = 'message-copy-btn';
        copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy';
        copyBtn.title = 'Copy message';
        
        copyBtn.addEventListener('click', async () => {
            try {
                // Strip HTML tags and get plain text
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = content;
                const plainText = tempDiv.textContent || tempDiv.innerText || content;
                
                await navigator.clipboard.writeText(plainText);
                
                // Visual feedback
                const originalHTML = copyBtn.innerHTML;
                copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                copyBtn.classList.add('copied');
                
                setTimeout(() => {
                    copyBtn.innerHTML = originalHTML;
                    copyBtn.classList.remove('copied');
                }, 2000);
                
                this.showNotification('Message copied to clipboard', 'success');
            } catch (error) {
                console.error('Copy failed:', error);
                this.showNotification('Failed to copy message', 'error');
            }
        });
        
        return copyBtn;
    }

    // Concert search functionality
    showSearchIndicator(searchType = 'information', query = '') {
        if (!this.messagesDiv) return;
        
        this.isSearching = true;
        this.hideSearchIndicator();
        this.searchStartTime = Date.now();
        
        const searchDiv = document.createElement('div');
        searchDiv.className = 'universal-search-indicator';
        searchDiv.id = 'universalSearchIndicator';
        
        const searchTypes = {
            'concert': { icon: '🎵', text: 'Searching for concerts' },
            'event': { icon: '🎪', text: 'Searching for events' },
            'information': { icon: '🔍', text: 'Searching' }
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
        
        this.messagesDiv.appendChild(searchDiv);
        this.scrollToBottom(true);
        
        const cancelBtn = document.getElementById('cancelSearchBtn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.cancelSearch());
        }
        
        this.startSearchTimer();
    }

    startSearchTimer() {
        if (this.searchTimerInterval) {
            clearInterval(this.searchTimerInterval);
        }
        
        this.searchTimerInterval = setInterval(() => {
            const timerElement = document.getElementById('searchTimer');
            if (!timerElement) {
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
                setTimeout(() => indicator.remove(), 300);
            }, 800);
        }
    }

    cancelSearch() {
        if (this.currentAbortController) {
            this.currentAbortController.abort();
            this.currentAbortController = null;
        }
        
        this.isSearching = false;
        this.hideSearchIndicator();
        
        this.displayMessage('🛑 Search canceled. Feel free to start a new search anytime!', 'assistant');
        this.showNotification('Search canceled', 'info');
    }

    async fetchConcerts(date, keywords) {
        this.currentAbortController = new AbortController();
        
        try {
            const query = keywords && keywords !== 'all' ? keywords : 'concerts in Malaysia';
            this.showSearchIndicator('concert', query);
            
            const response = await fetch('/api/concerts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    date: date || '',
                    keywords: keywords || ''
                }),
                signal: this.currentAbortController.signal
            });
            
            this.hideSearchIndicator();
            this.currentAbortController = null;
            
            if (!response.ok) throw new Error('Failed to fetch concerts');
            
            const data = await response.json();
            
            if (data.success && data.events && data.events.length > 0) {
                let concertHTML = `🎵 **Found ${data.count} concert(s)/event(s):**\n\n`;
                
                data.events.forEach((event, index) => {
                    concertHTML += `**${index + 1}. ${event.name}**\n\n`;
                    concertHTML += `📅 **Date:** ${event.date}\n\n`;
                    concertHTML += `📍 **Venue:** ${event.venue}${event.city ? ', ' + event.city : ''}\n\n`;
                    concertHTML += `🔗 **[Get Tickets](${event.url})**\n\n`;
                    if (index < data.events.length - 1) {
                        concertHTML += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n`;
                    }
                });
                
                this.displayMessage(concertHTML, 'assistant');
            } else {
                const message = data.message || "Sorry, I couldn't find any concerts matching your search.";
                this.displayMessage(message, 'assistant');
            }
        } catch (error) {
            if (error.name === 'AbortError') return;
            
            this.hideSearchIndicator();
            this.currentAbortController = null;
            this.displayMessage("Sorry, I encountered an error while searching for concerts.", 'assistant');
            this.showNotification('Failed to fetch concerts', 'error');
        }
    }
        
    displayMessage(content, role, shouldScroll = true) {
        if (!this.messagesDiv) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = role === 'user' 
            ? '<i class="fas fa-user"></i>' 
            : '<div class="logo-icon-small">X</div>';

        // Create wrapper for content + copy button
        const contentWrapper = document.createElement('div');
        contentWrapper.className = 'message-content-wrapper';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        if (role === 'assistant') {
            contentDiv.innerHTML = this.renderMarkdown(content);
            setTimeout(() => {
                this.addCopyButtons(contentDiv);
                this.highlightCode(contentDiv);
            }, 0);
        } else {
            contentDiv.textContent = content;
        }

        // Add content to wrapper
        contentWrapper.appendChild(contentDiv);
        
        // Add message copy button below content
        const copyBtn = this.createMessageCopyButton(content);
        contentWrapper.appendChild(copyBtn);

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentWrapper);
        
        this.messagesDiv.appendChild(messageDiv);

        if (shouldScroll) this.scrollToBottom();
    }

    renderMarkdown(text) {
        if (typeof marked !== 'undefined') {
            marked.setOptions({
                breaks: true,
                gfm: true,
                highlight: function(code, lang) {
                    if (typeof hljs !== 'undefined' && lang && hljs.getLanguage(lang)) {
                        try {
                            return hljs.highlight(code, { language: lang }).value;
                        } catch (e) {}
                    }
                    return code;
                }
            });
            return marked.parse(text);
        }
        return this.simpleMarkdown(text);
    }

    simpleMarkdown(text) {
        return text
            .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
            .replace(/\n/g, '<br>');
    }

    addCopyButtons(container) {
        const codeBlocks = container.querySelectorAll('pre');
        codeBlocks.forEach(pre => {
            const wrapper = document.createElement('div');
            wrapper.className = 'code-block-wrapper';
            
            const copyBtn = document.createElement('button');
            copyBtn.className = 'copy-code-btn';
            copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy';
            
            copyBtn.addEventListener('click', () => {
                const code = pre.querySelector('code')?.textContent || pre.textContent;
                navigator.clipboard.writeText(code).then(() => {
                    copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                    copyBtn.classList.add('copied');
                    setTimeout(() => {
                        copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy';
                        copyBtn.classList.remove('copied');
                    }, 2000);
                });
            });
            
            pre.parentNode.insertBefore(wrapper, pre);
            wrapper.appendChild(copyBtn);
            wrapper.appendChild(pre);
        });
    }

    highlightCode(container) {
        if (typeof hljs !== 'undefined') {
            container.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        }
    }

    showTypingIndicator() {
        this.isTyping = true;
        if (this.typingIndicator) this.typingIndicator.style.display = 'flex';
        if (this.sendBtn) this.sendBtn.disabled = true;
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.isTyping = false;
        if (this.typingIndicator) this.typingIndicator.style.display = 'none';
        if (this.sendBtn) this.sendBtn.disabled = false;
    }

    scrollToBottom(force = false) {
        if (!this.messagesDiv) return;
        requestAnimationFrame(() => {
            this.messagesDiv.scrollTop = this.messagesDiv.scrollHeight;
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
        `;
        
        document.body.appendChild(notification);
        setTimeout(() => {
            notification.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// FIXED: Proper initialization outside the class
document.addEventListener('DOMContentLoaded', () => {
    // Add CSS animations
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
        /* Typing cursor animation */
        .typing-cursor {
            display: inline-block;
            color: var(--accent-primary);
            animation: blink 1s infinite;
            margin-left: 2px;
            font-weight: bold;
        }
        
        @keyframes blink {
            0%, 50% { opacity: 0; }
            51%, 100% { opacity: 0; }
        }
    `;
    document.head.appendChild(style);

    // Initialize the app
    window.xeerGPT = new AddOnChtHistryDBCpyBtn();
});