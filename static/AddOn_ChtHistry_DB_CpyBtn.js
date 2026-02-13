/* ==================================
   XeerGPT - COMPLETE JAVASCRIPT
   Chat Interface with ALL Features
   NOTHING MISSING - FULL CODE
   ================================== */

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
        this.userScrolled = false;

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
        
        // ── Stop button (added in chat.html inside .send-btn-wrap) ──
        this.sendBtnWrap = document.getElementById('sendBtnWrap');
        this.stopBtn = document.getElementById('stopBtn');
        
        // Model selector elements (beside send button)
        this.modelSelectorBtn = document.getElementById('modelSelectorBtn');
        this.modelDropdown = document.getElementById('modelDropdown');
        this.selectedModelIcon = document.getElementById('selectedModelIcon');
        this.selectedModelName = document.getElementById('selectedModelName');
        this.scrollBtn = this.createScrollButton();

        if (this.messagesDiv) {
            this.messagesDiv.addEventListener('scroll', () => {
                const el = this.messagesDiv;
                const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
                this.userScrolled = distanceFromBottom > 1;
            });
        }
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
            const header = document.createElement('div');
            header.className = 'model-dropdown-header';
            
            const firstModelIcon = Object.values(providerData.models)[0]?.icon || '🤖';
            header.innerHTML = `<span>${firstModelIcon}</span><span>${providerData.display_name}</span>`;
            this.modelDropdown.appendChild(header);
            
            const group = document.createElement('div');
            group.className = 'model-group';
            
            Object.entries(providerData.models).forEach(([modelKey, modelInfo]) => {
                const item = document.createElement('div');
                item.className = 'model-item';
                if (modelKey === this.selectedModel) item.classList.add('selected');
                
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
        
        this.updateSelectedModelDisplay(icon, name);
        this.renderModelSelector();
        
        console.log(`🤖 Selected model: ${modelKey}`);
        this.showNotification(`Switched to ${name}`, 'success');
    }

    updateSelectedModelDisplay(icon, name) {
        if (!icon || !name) {
            for (const provider of Object.values(this.availableModels)) {
                if (provider.models[this.selectedModel]) {
                    icon = provider.models[this.selectedModel].icon;
                    name = provider.models[this.selectedModel].name;
                    break;
                }
            }
        }
        if (this.selectedModelIcon) this.selectedModelIcon.textContent = icon || '🤖';
        if (this.selectedModelName) {
            const shortName = name ? name.replace('Gemini ', '').replace('Llama ', '').replace('DeepSeek ', '') : 'Model';
            this.selectedModelName.textContent = shortName;
        }
    }

    closeModelDropdown() {
        if (this.modelDropdown) this.modelDropdown.classList.remove('open');
        if (this.modelSelectorBtn) this.modelSelectorBtn.classList.remove('open');
    }

    createScrollButton() {
        const btn = document.createElement('button');
        btn.id = 'scrollToBottomBtn';
        btn.innerHTML = '<i class="fas fa-chevron-down"></i>';
        btn.style.cssText = `
            position: fixed;
            bottom: 100px;
            right: 24px;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: var(--bg-secondary);
            border: 1px solid var(--border-light);
            color: var(--text-primary);
            cursor: pointer;
            display: none;
            align-items: center;
            justify-content: center;
            font-size: 0.85rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            z-index: 500;
            transition: all 0.2s ease;
        `;

        btn.addEventListener('mouseenter', () => {
            btn.style.background = 'var(--bg-tertiary)';
            btn.style.borderColor = 'var(--accent-primary)';
            btn.style.transform = 'scale(1.1)';
        });
        btn.addEventListener('mouseleave', () => {
            btn.style.background = 'var(--bg-secondary)';
            btn.style.borderColor = 'var(--border-light)';
            btn.style.transform = 'scale(1)';
        });

        btn.addEventListener('click', () => {
            this.userScrolled = false;
            this.scrollToBottom(true);
        });

        document.body.appendChild(btn);

        if (this.messagesDiv) {
            this.messagesDiv.addEventListener('scroll', () => {
                const el = this.messagesDiv;
                const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
                btn.style.display = distanceFromBottom > 100 ? 'flex' : 'none';
            });
        }

        return btn;
    }    

    attachEventListeners() {
        if (this.sendBtn) {
            this.sendBtn.addEventListener('click', () => this.sendMessage());
        }

        if (this.stopBtn) {
            this.stopBtn.addEventListener('click', () => this.stopStreaming());
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
        
        if (this.modelSelectorBtn) {
            this.modelSelectorBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const isOpen = this.modelDropdown.classList.toggle('open');
                this.modelSelectorBtn.classList.toggle('open', isOpen);
            });
        }
        
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.model-selector-dropdown')) this.closeModelDropdown();
        });
    }

    showStreamingState() {
        if (this.sendBtnWrap) this.sendBtnWrap.classList.add('is-streaming');
    }

    hideStreamingState() {
        if (this.sendBtnWrap) this.sendBtnWrap.classList.remove('is-streaming');
    }

    stopStreaming() {
        if (this.currentAbortController) {
            this.currentAbortController.abort();
            this.currentAbortController = null;
        }
        this.hideStreamingState();
        this.hideTypingIndicator();
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
        newChatItem.addEventListener('click', (e) => { e.preventDefault(); this.createNewChat(); });
        this.historyItems.appendChild(newChatItem);
        
        if (conversations && conversations.length > 0) {
            conversations.forEach(conv => {
                const item = document.createElement('div');
                item.className = 'history-item';
                if (conv.id === this.currentConversationId) item.classList.add('active');
                
                item.innerHTML = `
                    <i class="fas fa-message"></i>
                    <span class="conversation-title" data-id="${conv.id}">${this.escapeHtml(conv.title)}</span>
                    <button class="delete-chat-btn" data-id="${conv.id}" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                `;
                
                item.addEventListener('click', (e) => {
                    if (!e.target.closest('.delete-chat-btn')) this.loadConversation(conv.id);
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
                data.messages.forEach(msg => this.displayMessage(msg.content, msg.role, false));
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
            const activeItem = Array.from(this.historyItems?.children || []).find(child => {
                const titleSpan = child.querySelector('.conversation-title');
                return titleSpan && parseInt(titleSpan.dataset.id) === this.currentConversationId;
            });
            if (activeItem) activeItem.classList.add('active');
        }
    }

    async deleteConversation(conversationId) {
        if (!confirm('Delete this conversation?')) return;
        try {
            await fetch(`/api/conversations/${conversationId}`, { method: 'DELETE' });
            if (conversationId === this.currentConversationId) this.createNewChat();
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

        // Merge any pasted snippets into the message
        let fullMessage = message;
        if (window.pasteHandler && window.pasteHandler.hasPastedContent()) {
            const pastedContent = window.pasteHandler.getPastedContent();
            fullMessage = message
                ? `${message}\n\n${pastedContent}`
                : pastedContent;
            window.pasteHandler.hidePreview?.();
            window.pasteHandler.clearPastedContent();
        }

        if (!fullMessage || this.isTyping) return;

        console.log(`📤 Sending with model: ${this.selectedModel}`);

        if (this.welcomeScreen?.style.display !== 'none') {
            this.welcomeScreen.style.display = 'none';
            this.messagesContainer.style.display = 'flex';
        }

        this.displayMessage(message || '[Pasted Code]', 'user');
        if (this.userInput) {
            this.userInput.value = '';
            this.userInput.style.height = 'auto';
        }

        this.userScrolled = false;      // ← reset BEFORE streaming starts
        this.scrollToBottom(true);      // ← snap to bottom when user sends

        this.showTypingIndicator();

        try {
            // ── CHANGED: pass fullMessage (with pasted content) ──
            await this.fetchBotResponseStreaming(fullMessage);
        } catch (error) {
            this.hideTypingIndicator();
            this.hideStreamingState();// ← restore Send button on error
            console.error('❌ Chat error:', error);
            if (error.name !== 'AbortError') {
                this.displayMessage('Connection error. Please try again.', 'assistant');
            }
        }
    }

    async fetchBotResponseStreaming(message) {
        this.currentAbortController = new AbortController();
        this.showStreamingState();

        let response;
        try {
            response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    conversation_id: this.currentConversationId,
                    model: this.selectedModel
                }),
                signal: this.currentAbortController.signal,
            });
        } catch (err) {
            this.hideStreamingState();
            this.currentAbortController = null;
            if (err.name === 'AbortError') return;
            throw err;
        }

        if (!response.ok) {
            this.hideStreamingState();
            this.currentAbortController = null;
            throw new Error(`Server error: ${response.status}`);
        }

        this.hideTypingIndicator();
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant-message streaming';

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar bot';
        
        let logo;
        if (window.createXeerLogo) {
            logo = window.createXeerLogo(true);
            avatar.appendChild(logo);
        } else {
            avatar.innerHTML = '<div class="logo-icon-small">X</div>';
        }

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

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let fullContent = '';

        try {
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
                            messageDiv.classList.remove('streaming');
                            if (logo && window.stopLogoAnimation) {
                                window.stopLogoAnimation(logo);
                            }
                            
                            contentDiv.innerHTML = this.renderMarkdown(fullContent);
                            setTimeout(() => {
                                this.addCopyButtons(contentDiv);
                                this.highlightCode(contentDiv);
                            }, 0);
                            const actionBar = this.createMessageActionBar(fullContent, 'assistant');
                            contentWrapper.appendChild(actionBar);
                            
                        } else if (data.type === 'error') {
                            messageDiv.classList.remove('streaming');
                            if (logo && window.stopLogoAnimation) {
                                window.stopLogoAnimation(logo);
                            }
                            
                            contentDiv.innerHTML = this.renderMarkdown(data.message);
                            const actionBar = this.createMessageActionBar(data.message, 'assistant');
                            contentWrapper.appendChild(actionBar);
                        }
                    }
                }
            }
        } catch (err) {
            if (err.name === 'AbortError') {
                messageDiv.classList.remove('streaming');
                
                if (logo && window.stopLogoAnimation) {
                    window.stopLogoAnimation(logo);
                }
                
                if (fullContent) {
                    contentDiv.innerHTML = this.renderMarkdown(fullContent) +
                        '<p style="color:var(--text-muted);font-size:0.8rem;margin-top:8px">' +
                        '<i class="fas fa-stop-circle"></i> Generation stopped</p>';
                    setTimeout(() => {
                        this.addCopyButtons(contentDiv);
                        this.highlightCode(contentDiv);
                    }, 0);
                    const actionBar = this.createMessageActionBar(fullContent, 'assistant');
                    contentWrapper.appendChild(actionBar);
                } else {
                    messageDiv.remove();
                }
            } else {
                throw err;
            }
        } finally {
            this.hideStreamingState();
            this.currentAbortController = null;
        }
    }

    createMessageActionBar(content, role) {
        if (role === 'user') {
            return this.createSimpleCopyButton(content);
        }
        
        const actionBar = document.createElement('div');
        actionBar.className = 'message-actions';
        
        const copyBtn = document.createElement('button');
        copyBtn.className = 'message-action-btn';
        copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
        copyBtn.title = 'Copy';
        copyBtn.addEventListener('click', async () => {
            try {
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = content;
                const plainText = tempDiv.textContent || tempDiv.innerText || content;
                await navigator.clipboard.writeText(plainText);
                
                const originalHTML = copyBtn.innerHTML;
                copyBtn.innerHTML = '<i class="fas fa-check"></i>';
                copyBtn.classList.add('active');
                setTimeout(() => {
                    copyBtn.innerHTML = originalHTML;
                    copyBtn.classList.remove('active');
                }, 2000);
                
                this.showNotification('Copied to clipboard', 'success');
            } catch (error) {
                this.showNotification('Failed to copy', 'error');
            }
        });
        
        const thumbsUpBtn = document.createElement('button');
        thumbsUpBtn.className = 'message-action-btn';
        thumbsUpBtn.innerHTML = '<i class="far fa-thumbs-up"></i>';
        thumbsUpBtn.title = 'Good response';
        thumbsUpBtn.addEventListener('click', () => {
            thumbsUpBtn.classList.toggle('active');
            if (thumbsUpBtn.classList.contains('active')) {
                thumbsUpBtn.innerHTML = '<i class="fas fa-thumbs-up"></i>';
                thumbsDownBtn.classList.remove('active');
                thumbsDownBtn.innerHTML = '<i class="far fa-thumbs-down"></i>';
            } else {
                thumbsUpBtn.innerHTML = '<i class="far fa-thumbs-up"></i>';
            }
        });
        
        const thumbsDownBtn = document.createElement('button');
        thumbsDownBtn.className = 'message-action-btn';
        thumbsDownBtn.innerHTML = '<i class="far fa-thumbs-down"></i>';
        thumbsDownBtn.title = 'Bad response';
        thumbsDownBtn.addEventListener('click', () => {
            thumbsDownBtn.classList.toggle('active');
            if (thumbsDownBtn.classList.contains('active')) {
                thumbsDownBtn.innerHTML = '<i class="fas fa-thumbs-down"></i>';
                thumbsUpBtn.classList.remove('active');
                thumbsUpBtn.innerHTML = '<i class="far fa-thumbs-up"></i>';
            } else {
                thumbsDownBtn.innerHTML = '<i class="far fa-thumbs-down"></i>';
            }
        });
        
        const separator1 = document.createElement('div');
        separator1.className = 'message-actions-separator';
        
        const regenBtn = document.createElement('button');
        regenBtn.className = 'message-action-btn';
        regenBtn.innerHTML = '<i class="fas fa-redo"></i>';
        regenBtn.title = 'Regenerate';
        regenBtn.addEventListener('click', () => {
            this.showNotification('Regenerate feature coming soon!', 'info');
        });
        
        const shareBtn = document.createElement('button');
        shareBtn.className = 'message-action-btn';
        shareBtn.innerHTML = '<i class="fas fa-share"></i>';
        shareBtn.title = 'Share';
        shareBtn.addEventListener('click', () => {
            this.showNotification('Share feature coming soon!', 'info');
        });
        
        const moreBtn = document.createElement('button');
        moreBtn.className = 'message-action-btn';
        moreBtn.innerHTML = '<i class="fas fa-ellipsis"></i>';
        moreBtn.title = 'More options';
        moreBtn.addEventListener('click', () => {
            this.showNotification('More options coming soon!', 'info');
        });
        
        actionBar.appendChild(copyBtn);
        actionBar.appendChild(thumbsUpBtn);
        actionBar.appendChild(thumbsDownBtn);
        actionBar.appendChild(separator1);
        actionBar.appendChild(regenBtn);
        actionBar.appendChild(shareBtn);
        actionBar.appendChild(moreBtn);
        
        return actionBar;
    }

    createSimpleCopyButton(content) {
        const copyBtn = document.createElement('button');
        copyBtn.className = 'message-copy-btn';
        copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy';
        copyBtn.title = 'Copy message';
        
        copyBtn.addEventListener('click', async () => {
            try {
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = content;
                const plainText = tempDiv.textContent || tempDiv.innerText || content;
                
                await navigator.clipboard.writeText(plainText);
                
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

    displayMessage(content, role, shouldScroll = true) {
        if (!this.messagesDiv) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        
        if (role === 'user') {
            avatar.innerHTML = '<i class="fas fa-user"></i>';
        } else {
            avatar.className = 'message-avatar bot';
            if (window.createXeerLogo) {
                const logo = window.createXeerLogo(false);
                avatar.appendChild(logo);
            } else {
                avatar.innerHTML = '<div class="logo-icon-small">X</div>';
            }
        }

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

        contentWrapper.appendChild(contentDiv);
        
        const actionBar = this.createMessageActionBar(content, role);
        contentWrapper.appendChild(actionBar);

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
                        try { return hljs.highlight(code, { language: lang }).value; } catch (e) {}
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
            container.querySelectorAll('pre code').forEach(block => hljs.highlightElement(block));
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
        
        if (force || !this.userScrolled) {
            requestAnimationFrame(() => {
                this.messagesDiv.scrollTop = this.messagesDiv.scrollHeight;
            });
        }
    }

    showNotification(message, type = 'info') {
        const existing = document.querySelector('.notification');
        if (existing) existing.remove();
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        const colors = { 'error': '#f44336', 'success': '#4caf50', 'info': '#2196f3' };
        
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

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to   { transform: translateX(0);    opacity: 1; }
        }
        @keyframes fadeOut {
            from { opacity: 1; }
            to   { opacity: 0; }
        }
    `;
    document.head.appendChild(style);

    // Initialize the app
    window.xeerGPT = new AddOnChtHistryDBCpyBtn();
});