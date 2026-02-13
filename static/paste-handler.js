class PasteHandler {
    constructor() {
        this.MIN_LINES_FOR_PREVIEW = 150; // Show preview for 150+ lines
        this.pastedContent = null;
        this.isExpanded = false;

        // NEW: track multiple pastes and undo stack
        this.pastedItems = [];   // [{ id, content, lineCount }]
        this.undoStack = [];
        this.nextId = 1;
        
        this.initializeElements();
        this.attachEventListeners();
    }
    
    initializeElements() {
        this.userInput = document.getElementById('userInput');
        this.inputContainer = document.getElementById('inputContainer');
        this.previewContainer = document.getElementById('pastePreviewContainer');

        // ── These single-card refs are kept for legacy compat but are NOT
        //    relied on after renderAllCards() replaces innerHTML ──
        this.previewTitle = document.getElementById('pastePreviewTitle');
        this.previewBadge = document.getElementById('pastePreviewBadge');
        this.previewLineCount = document.getElementById('pastePreviewLineCount');
        this.previewLanguage = document.getElementById('pastePreviewLanguage');
        this.previewContent = document.getElementById('pastePreviewContent');
        this.previewClose = document.getElementById('pastePreviewClose');
        this.previewExpand = document.getElementById('pastePreviewExpand');
    }
    
    attachEventListeners() {
        // Original paste event - unchanged
        if (this.userInput) {
            this.userInput.addEventListener('paste', (e) => this.handlePaste(e));
        }
        
        // Close preview (legacy single-card button - may not exist after renderAllCards)
        if (this.previewClose) {
            this.previewClose.addEventListener('click', () => this.hidePreview());
        }
        
        // Expand/Collapse preview (legacy single-card button)
        if (this.previewExpand) {
            this.previewExpand.addEventListener('click', () => this.toggleExpand());
        }

        // Ctrl+Z = undo last paste card, Ctrl+Y = redo
        if (this.userInput) {
            this.userInput.addEventListener('keydown', (e) => {
                if (e.ctrlKey && !e.shiftKey && e.key === 'z') {
                    if (this.pastedItems.length > 0) {
                        e.preventDefault();
                        this.undoLastPaste();
                    }
                }
                if (e.ctrlKey && !e.shiftKey && e.key === 'y') {
                    if (this.undoStack.length > 0) {
                        e.preventDefault();
                        this.redoLastPaste();
                    }
                }
            });
        }
    }
    
    async handlePaste(e) {
        const clipboardData = e.clipboardData || window.clipboardData;
        
        // Check for files first
        const items = clipboardData.items;
        
        if (items) {
            for (let item of items) {
                if (item.kind === 'file') {
                    // Let file upload handler manage this
                    return;
                }
            }
        }
        
        // Get text content
        const pastedText = clipboardData.getData('text');
        
        if (!pastedText) return;
        
        // Count lines
        const lines = pastedText.split('\n');
        const lineCount = lines.length;
        
        // If content is large enough, show preview instead
        if (lineCount >= this.MIN_LINES_FOR_PREVIEW) {
            e.preventDefault(); // Prevent default paste
            this.addPasteItem(pastedText, lineCount);
        } else {
            // For smaller content, allow normal paste
            if (this.inputContainer) {
                this.inputContainer.classList.add('paste-detected');
                setTimeout(() => {
                    this.inputContainer.classList.remove('paste-detected');
                }, 600);
            }
        }
    }

    // Add a new paste item and re-render all cards
    addPasteItem(content, lineCount) {
        const id = this.nextId++;
        const detection = this.detectContentType(content);
        this.pastedItems.push({ id, content, lineCount, detection });
        this.undoStack = []; // Clear redo on new paste
        this.pastedContent = content; // Keep last for backward compat
        this.renderAllCards();
        if (this.userInput) this.userInput.focus();
    }

    // Render all paste cards into the preview container
    renderAllCards() {
        if (!this.previewContainer) return;

        // Clear existing
        this.previewContainer.innerHTML = '';

        if (this.pastedItems.length === 0) {
            this.previewContainer.classList.remove('active');
            return;
        }

        this.previewContainer.classList.add('active');

        // Multiple items: show header with count + expand/collapse all
        if (this.pastedItems.length > 1) {
            const header = document.createElement('div');
            header.className = 'paste-multi-header';
            header.innerHTML = `
                <div class="paste-multi-info">
                    <i class="fas fa-layer-group"></i>
                    <span>${this.pastedItems.length} snippets attached</span>
                </div>
                <div class="paste-multi-actions">
                    <button class="paste-multi-btn" id="pasteExpandAll">
                        <i class="fas fa-chevron-down"></i>
                        <span>Show all</span>
                    </button>
                    <button class="paste-multi-btn" id="pasteClearAll" title="Remove all">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            `;
            this.previewContainer.appendChild(header);

            // Expand/collapse all
            const expandBtn = header.querySelector('#pasteExpandAll');
            expandBtn.addEventListener('click', () => {
                const allCards = this.previewContainer.querySelectorAll('.paste-preview-card');
                const allCollapsed = Array.from(allCards).every(c => c.classList.contains('collapsed'));
                
                allCards.forEach(card => {
                    if (allCollapsed) {
                        card.classList.remove('collapsed');
                    } else {
                        card.classList.add('collapsed');
                    }
                });

                expandBtn.innerHTML = allCollapsed
                    ? '<i class="fas fa-chevron-up"></i><span>Hide all</span>'
                    : '<i class="fas fa-chevron-down"></i><span>Show all</span>';
            });

            // Clear all
            const clearBtn = header.querySelector('#pasteClearAll');
            clearBtn.addEventListener('click', () => {
                if (confirm(`Remove all ${this.pastedItems.length} pasted snippets?`)) {
                    this.pastedItems = [];
                    this.pastedContent = null;
                    this.renderAllCards();
                    this.showToast('All pastes cleared');
                }
            });
        }

        // Render cards in REVERSE order (newest on top)
        const reversedItems = [...this.pastedItems].reverse();
        reversedItems.forEach((item, visualIndex) => {
            const card = this.buildCard(item, visualIndex === 0 && this.pastedItems.length > 1);
            this.previewContainer.appendChild(card);
        });
    }

    // Build a single paste card element
    buildCard(item, isNewest = false) {
        const { id, content, lineCount, detection } = item;

        const card = document.createElement('div');
        card.className = 'paste-preview-card';
        if (this.pastedItems.length > 1) {
            card.classList.add('collapsed'); // Start collapsed when multiple
        }
        if (isNewest) {
            card.classList.add('newest'); // Highlight newest
        }
        card.dataset.pasteId = id;

        // Header
        const header = document.createElement('div');
        header.className = 'paste-preview-header';
        header.innerHTML = `
            <div class="paste-preview-title">
                <i class="fas fa-clipboard paste-preview-icon"></i>
                <span>${detection.title}</span>
                <span class="paste-preview-badge">
                    <i class="fas ${detection.icon}"></i>
                    <span>${lineCount.toLocaleString()} lines</span>
                </span>
                ${detection.language ? `<span class="paste-preview-language" style="display:inline-block">${detection.language.toUpperCase()}</span>` : ''}
                ${isNewest ? '<span class="paste-newest-badge">NEW</span>' : ''}
            </div>
            <div class="paste-preview-actions">
                <button class="paste-preview-action-btn expand">
                    <i class="fas fa-chevron-down"></i>
                    <span>Expand</span>
                </button>
                <button class="paste-preview-close" title="Remove">
                    <i class="fas fa-times"></i>
                    <span class="close-label"></span>
                </button>
            </div>
        `;

        // Body
        const body = document.createElement('div');
        body.className = 'paste-preview-content';
        const lineNumbers = content.split('\n').map((_, i) => i + 1).join('\n');
        body.innerHTML = `
            <div class="paste-preview-line-numbers">
                <pre class="paste-preview-lines">${lineNumbers}</pre>
                <pre class="paste-preview-code"><code>${this.escapeHtml(content)}</code></pre>
            </div>
        `;

        // Syntax highlight
        if (window.hljs && detection.language) {
            const codeEl = body.querySelector('code');
            try { codeEl.className = `language-${detection.language}`; hljs.highlightElement(codeEl); } catch (_) {}
        }

        // Expand button - toggles individual card
        header.querySelector('.expand').addEventListener('click', (e) => {
            e.stopPropagation();
            const btn = e.currentTarget;
            const closeBtn = header.querySelector('.paste-preview-close');
            const closeLabel = closeBtn.querySelector('.close-label');
            const isNowCollapsed = card.classList.toggle('collapsed');

            btn.innerHTML = !isNowCollapsed
                ? '<i class="fas fa-chevron-up"></i><span>Collapse</span>'
                : '<i class="fas fa-chevron-down"></i><span>Expand</span>';

            // When expanded show "Remove" text, when collapsed show just the X icon
            if (!isNowCollapsed) {
                closeBtn.innerHTML = '<i class="fas fa-times"></i><span class="close-label"> Remove</span>';
            } else {
                closeBtn.innerHTML = '<i class="fas fa-times"></i><span class="close-label"></span>';
            }
        });

        // Click header title to expand/collapse too
        header.querySelector('.paste-preview-title').addEventListener('click', () => {
            header.querySelector('.expand').click();
        });

        // Close button - remove this specific card
        header.querySelector('.paste-preview-close').addEventListener('click', (e) => {
            e.stopPropagation();
            const found = this.pastedItems.find(i => i.id === id);
            if (found) this.undoStack.push(found);
            this.pastedItems = this.pastedItems.filter(i => i.id !== id);
            this.pastedContent = this.pastedItems.length > 0
                ? this.pastedItems[this.pastedItems.length - 1].content
                : null;
            this.renderAllCards();
        });

        card.appendChild(header);
        card.appendChild(body);
        return card;
    }

    // Ctrl+Z - remove last pasted card
    undoLastPaste() {
        const last = this.pastedItems[this.pastedItems.length - 1];
        if (!last) return;
        this.undoStack.push(last);
        this.pastedItems.pop();
        this.pastedContent = this.pastedItems.length > 0
            ? this.pastedItems[this.pastedItems.length - 1].content
            : null;
        this.renderAllCards();
        this.showToast('Paste removed — Ctrl+Y to redo');
    }

    // Ctrl+Y - restore last removed card
    redoLastPaste() {
        const item = this.undoStack.pop();
        if (!item) return;
        this.pastedItems.push(item);
        this.pastedContent = item.content;
        this.renderAllCards();
        this.showToast('Paste restored');
    }

    showToast(msg) {
        const existing = document.getElementById('pasteToast');
        if (existing) existing.remove();
        const toast = document.createElement('div');
        toast.id = 'pasteToast';
        toast.style.cssText = `
            position:fixed;bottom:130px;left:50%;transform:translateX(-50%);
            background:var(--bg-tertiary);border:1px solid var(--border-light);
            color:var(--text-secondary);padding:6px 16px;border-radius:20px;
            font-size:0.75rem;z-index:9999;pointer-events:none;
        `;
        toast.textContent = msg;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2000);
    }
    
    detectContentType(content) {
        const lines = content.split('\n');
        
        if (content.includes('<?php')) {
            return { title: 'PHP Code', language: 'php', icon: 'fa-code' };
        }
        if (content.includes('function') && content.includes('{') && content.includes('}')) {
            return { title: 'JavaScript Code', language: 'javascript', icon: 'fa-code' };
        }
        if (content.includes('def ') || content.includes('import ') || content.includes('class ')) {
            return { title: 'Python Code', language: 'python', icon: 'fa-code' };
        }
        if (content.includes('<html') || content.includes('<!DOCTYPE')) {
            return { title: 'HTML Document', language: 'html', icon: 'fa-code' };
        }
        if (content.includes('{') && content.includes('}') && content.includes(':')) {
            try {
                JSON.parse(content);
                return { title: 'JSON Data', language: 'json', icon: 'fa-brackets-curly' };
            } catch (e) {}
        }
        if (content.includes('SELECT') || content.includes('INSERT') || content.includes('UPDATE')) {
            return { title: 'SQL Query', language: 'sql', icon: 'fa-database' };
        }
        if (lines.length > 1 && lines[0].includes(',') && lines[1].includes(',')) {
            return { title: 'CSV Data', language: 'csv', icon: 'fa-table' };
        }
        return { title: 'Text Document', language: null, icon: 'fa-file-lines' };
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    toggleExpand() {
        this.isExpanded = !this.isExpanded;
        // Find the active single card content if present
        const content = this.previewContainer?.querySelector('.paste-preview-content');
        if (content) {
            if (this.isExpanded) {
                content.classList.add('expanded');
                if (this.previewExpand) this.previewExpand.innerHTML = '<i class="fas fa-compress-alt"></i><span>Collapse</span>';
            } else {
                content.classList.remove('expanded');
                if (this.previewExpand) this.previewExpand.innerHTML = '<i class="fas fa-expand-alt"></i><span>Expand</span>';
            }
        }
    }
    
    // ✅ FIXED: hidePreview now correctly clears both old single-card UI
    //    and the new multi-card system without relying on stale element refs
    hidePreview() {
        if (this.previewContainer) {
            this.previewContainer.classList.remove('active');
        }
        this.isExpanded = false;

        setTimeout(() => {
            if (this.previewContainer) {
                this.previewContainer.innerHTML = '';
            }
            // Reset stale legacy refs so they don't cause errors
            this.previewContent = null;
            this.previewExpand = null;
            this.previewClose = null;
        }, 300);
    }
    
    getPastedContent() {
        // Return all pasted items as code blocks
        if (this.pastedItems.length === 0) return this.pastedContent;
        return this.pastedItems.map((item, i) => {
            const lang = item.detection.language || '';
            const label = this.pastedItems.length > 1 ? `// Snippet ${i + 1}: ${item.detection.title}\n` : '';
            return `\`\`\`${lang}\n${label}${item.content}\n\`\`\``;
        }).join('\n\n');
    }
    
    hasPastedContent() {
        return this.pastedItems.length > 0 || this.pastedContent !== null;
    }
    
    clearPastedContent() {
        this.pastedContent = null;
        this.pastedItems = [];
        this.undoStack = [];
        if (this.previewContainer) {
            this.previewContainer.classList.remove('active');
            this.previewContainer.innerHTML = '';
        }
    }
}

// Initialize paste handler
document.addEventListener('DOMContentLoaded', () => {
    window.pasteHandler = new PasteHandler();
});