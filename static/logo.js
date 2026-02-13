//  ═══════════════════════════════════════════════════════════════════════
//    ANIMATED LOGO HELPER FUNCTIONS
//  ═══════════════════════════════════════════════════════════════════════ 
/**
 * Creates the animated Xeer logo element
 * @param {boolean} animated - Whether the logo should be animating
 * @returns {HTMLElement} The logo element
 */
window.createXeerLogo = function(animated = false) {
    const logo = document.createElement('div');
    logo.className = animated ? 'xeer-logo animating' : 'xeer-logo static';
    
    const letter = document.createElement('span');
    letter.className = 'xeer-letter';
    letter.textContent = 'X';
    
    logo.appendChild(letter);
    return logo;
};

/**
 * Stops the logo animation and returns it to static state
 * @param {HTMLElement} logo - The logo element to stop animating
 */
window.stopLogoAnimation = function(logo) {
    if (!logo || !logo.classList) return;
    
    logo.classList.remove('animating');
    logo.classList.add('static');
    
    console.log('⏹️ Logo animation stopped');
};

/**
 * Starts the logo animation
 * @param {HTMLElement} logo - The logo element to start animating
 */
window.startLogoAnimation = function(logo) {
    if (!logo || !logo.classList) return;
    
    logo.classList.remove('static');
    logo.classList.add('animating');
    
    console.log('▶️ Logo animation started');
};


// <!-- ═══════════════════════════════════════════════════════════════════════
//      INTEGRATION WITH CHAT SYSTEM - IMPROVED TIMING
//      ═══════════════════════════════════════════════════════════════════════ -->

// Wait for xeerGPT to be fully initialized before patching
function waitForXeerGPT(callback, maxAttempts = 20) {
    let attempts = 0;
    
    const checkInterval = setInterval(() => {
        attempts++;
        
        if (window.xeerGPT) {
            clearInterval(checkInterval);
            console.log('✅ xeerGPT found, applying animated logo patches...');
            callback();
        } else if (attempts >= maxAttempts) {
            clearInterval(checkInterval);
            console.warn('⚠️ xeerGPT not found after ' + maxAttempts + ' attempts');
        }
    }, 100); // Check every 100ms
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Waiting for xeerGPT to initialize...');
    
    waitForXeerGPT(function() {
        // ═══════════════════════════════════════════════════════════════════
        // PATCH 1: Override displayMessage to use animated logos
        // ═══════════════════════════════════════════════════════════════════
        const originalDisplayMessage = window.xeerGPT.displayMessage.bind(window.xeerGPT);
        window.xeerGPT.displayMessage = function(content, role, shouldScroll = true) {
            if (!this.messagesDiv) return;
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}-message`;

            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            
            if (role === 'user') {
                avatar.innerHTML = '<i class="fas fa-user"></i>';
            } else {
                // ✅ USE ANIMATED LOGO
                avatar.className = 'message-avatar bot';
                if (window.createXeerLogo) {
                    const logo = window.createXeerLogo(false); // false = static
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
        };
        
        // ═══════════════════════════════════════════════════════════════════
        // PATCH 2: Override fetchBotResponseStreaming to use animated logos
        // ═══════════════════════════════════════════════════════════════════
        const originalFetchBotResponseStreaming = window.xeerGPT.fetchBotResponseStreaming.bind(window.xeerGPT);
        window.xeerGPT.fetchBotResponseStreaming = async function(message) {
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
                if (err.name === 'AbortError') {
                    console.log('✅ Request aborted by user');
                    return;
                }
                throw err;
            }

            if (!response.ok) {
                this.hideStreamingState();
                this.currentAbortController = null;
                throw new Error(`Server error: ${response.status}`);
            }

            this.hideTypingIndicator();
            
            // ═══ CREATE MESSAGE WITH ANIMATED LOGO ═══
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message assistant-message streaming';

            const avatar = document.createElement('div');
            avatar.className = 'message-avatar bot';
            
            // ✅ CREATE ANIMATED LOGO
            let logo;
            if (window.createXeerLogo) {
                logo = window.createXeerLogo(true); // true = animating
                avatar.appendChild(logo);
                console.log('🎨 Created animated logo');
            } else {
                avatar.innerHTML = '<div class="logo-icon-small">X</div>';
                console.warn('⚠️ createXeerLogo not found, using fallback');
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

            // Read stream
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
                                // ✅ STOP LOGO ANIMATION
                                messageDiv.classList.remove('streaming');
                                if (logo && window.stopLogoAnimation) {
                                    window.stopLogoAnimation(logo);
                                    console.log('⏹️ Stopped logo animation');
                                }
                                
                                contentDiv.innerHTML = this.renderMarkdown(fullContent);
                                setTimeout(() => {
                                    this.addCopyButtons(contentDiv);
                                    this.highlightCode(contentDiv);
                                }, 0);
                                const actionBar = this.createMessageActionBar(content, role);
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
                    console.log('✅ Stream reading aborted');
                    messageDiv.classList.remove('streaming');
                    
                    // Stop logo animation
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
                        const actionBar = this.createMessageActionBar(content, role);
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
        };
        
        // ═══════════════════════════════════════════════════════════════════
        // PATCH 3: Ensure stopStreaming stops all logo animations
        // ═══════════════════════════════════════════════════════════════════
        const originalStopStreaming = window.xeerGPT.stopStreaming.bind(window.xeerGPT);
        window.xeerGPT.stopStreaming = function() {
            console.log('🛑 Stopping stream and animations...');
            if (this.currentAbortController) {
                this.currentAbortController.abort();
                this.currentAbortController = null;
                console.log('✅ Stream aborted');
            }
            this.hideStreamingState();
            this.hideTypingIndicator();
            
            // Stop all logo animations
            const allLogos = document.querySelectorAll('.xeer-logo.animating');
            allLogos.forEach(logo => {
                if (window.stopLogoAnimation) {
                    window.stopLogoAnimation(logo);
                }
            });
        };
        
        console.log('✅ Chat system patched for animated logos');
    });
});