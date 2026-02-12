class PasteHandler {
    constructor() {
        this.MIN_LINES_FOR_PREVIEW = 150; // Show preview for 150+ lines
        this.pastedContent = null;
        this.isExpanded = false;
        
        this.initializeElements();
        this.attachEventListeners();
    }
    
    initializeElements() {
        this.userInput = document.getElementById('userInput');
        this.inputContainer = document.getElementById('inputContainer');
        this.previewContainer = document.getElementById('pastePreviewContainer');
        this.previewTitle = document.getElementById('pastePreviewTitle');
        this.previewBadge = document.getElementById('pastePreviewBadge');
        this.previewLineCount = document.getElementById('pastePreviewLineCount');
        this.previewLanguage = document.getElementById('pastePreviewLanguage');
        this.previewContent = document.getElementById('pastePreviewContent');
        this.previewClose = document.getElementById('pastePreviewClose');
        this.previewExpand = document.getElementById('pastePreviewExpand');
    }
    
    attachEventListeners() {
        // Enhanced paste event
        if (this.userInput) {
            this.userInput.addEventListener('paste', (e) => this.handlePaste(e));
        }
        
        // Close preview
        if (this.previewClose) {
            this.previewClose.addEventListener('click', () => this.hidePreview());
        }
        
        // Expand/Collapse preview
        if (this.previewExpand) {
            this.previewExpand.addEventListener('click', () => this.toggleExpand());
        }
    }
    
    async handlePaste(e) {
        const clipboardData = e.clipboardData || window.clipboardData;
        
        // Check for files first
        const items = clipboardData.items;
        let hasFiles = false;
        
        if (items) {
            for (let item of items) {
                if (item.kind === 'file') {
                    hasFiles = true;
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
            this.showPreview(pastedText, lineCount);
        } else {
            // For smaller content, allow normal paste
            // Add a subtle animation
            this.inputContainer.classList.add('paste-detected');
            setTimeout(() => {
                this.inputContainer.classList.remove('paste-detected');
            }, 600);
        }
    }
    
    showPreview(content, lineCount) {
        this.pastedContent = content;
        
        // Detect content type and language
        const detection = this.detectContentType(content);
        
        // Update header
        this.previewTitle.textContent = detection.title;
        this.previewLineCount.textContent = `${lineCount.toLocaleString()} lines`;
        
        // Show language badge if it's code
        if (detection.language) {
            this.previewLanguage.textContent = detection.language.toUpperCase();
            this.previewLanguage.style.display = 'inline-block';
        } else {
            this.previewLanguage.style.display = 'none';
        }
        
        // Update badge icon
        const badgeIcon = this.previewBadge.querySelector('i');
        badgeIcon.className = `fas ${detection.icon}`;
        
        // Render content with syntax highlighting or line numbers
        this.renderPreviewContent(content, detection.language);
        
        // Show preview with animation
        requestAnimationFrame(() => {
            this.previewContainer.classList.add('active');
        });
        
        // Focus stays on input
        this.userInput.focus();
    }
    
    detectContentType(content) {
        const lines = content.split('\n');
        const firstLine = lines[0].trim();
        const extension = this.detectLanguageFromContent(content);
        
        // Check for specific patterns
        if (content.includes('<?php')) {
            return {
                title: 'PHP Code',
                language: 'php',
                icon: 'fa-code'
            };
        }
        
        if (content.includes('function') && content.includes('{') && content.includes('}')) {
            return {
                title: 'JavaScript Code',
                language: 'javascript',
                icon: 'fa-code'
            };
        }
        
        if (content.includes('def ') || content.includes('import ') || content.includes('class ')) {
            return {
                title: 'Python Code',
                language: 'python',
                icon: 'fa-code'
            };
        }
        
        if (content.includes('<html') || content.includes('<!DOCTYPE')) {
            return {
                title: 'HTML Document',
                language: 'html',
                icon: 'fa-code'
            };
        }
        
        if (content.includes('{') && content.includes('}') && content.includes(':')) {
            try {
                JSON.parse(content);
                return {
                    title: 'JSON Data',
                    language: 'json',
                    icon: 'fa-brackets-curly'
                };
            } catch (e) {
                // Not valid JSON
            }
        }
        
        if (content.includes('SELECT') || content.includes('INSERT') || content.includes('UPDATE')) {
            return {
                title: 'SQL Query',
                language: 'sql',
                icon: 'fa-database'
            };
        }
        
        // Check for CSV
        if (lines.length > 1 && lines[0].includes(',') && lines[1].includes(',')) {
            return {
                title: 'CSV Data',
                language: 'csv',
                icon: 'fa-table'
            };
        }
        
        // Default to text
        return {
            title: 'Text Document',
            language: null,
            icon: 'fa-file-lines'
        };
    }
    
    detectLanguageFromContent(content) {
        // Simple language detection based on syntax
        if (content.includes('<?php')) return 'php';
        if (content.includes('function') && content.includes('=>')) return 'javascript';
        if (content.includes('def ') && content.includes(':')) return 'python';
        if (content.includes('<html') || content.includes('<!DOCTYPE')) return 'html';
        if (content.includes('.class') || content.includes('public static')) return 'java';
        if (content.includes('#include') || content.includes('int main')) return 'cpp';
        return null;
    }
    
    renderPreviewContent(content, language) {
        const lines = content.split('\n');
        
        // Create line numbers and content
        const lineNumbers = lines.map((_, i) => i + 1).join('\n');
        
        const contentHTML = `
            <div class="paste-preview-line-numbers">
                <pre class="paste-preview-lines">${lineNumbers}</pre>
                <pre class="paste-preview-code"><code>${this.escapeHtml(content)}</code></pre>
            </div>
        `;
        
        this.previewContent.innerHTML = contentHTML;
        
        // Apply syntax highlighting if available
        if (window.hljs && language) {
            const codeBlock = this.previewContent.querySelector('code');
            try {
                hljs.highlightElement(codeBlock);
            } catch (e) {
                console.log('Syntax highlighting failed:', e);
            }
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    toggleExpand() {
        this.isExpanded = !this.isExpanded;
        
        if (this.isExpanded) {
            this.previewContent.classList.add('expanded');
            this.previewExpand.innerHTML = '<i class="fas fa-compress-alt"></i><span>Collapse</span>';
        } else {
            this.previewContent.classList.remove('expanded');
            this.previewExpand.innerHTML = '<i class="fas fa-expand-alt"></i><span>Expand</span>';
        }
    }
    
    hidePreview() {
        this.previewContainer.classList.remove('active');
        this.isExpanded = false;
        this.previewContent.classList.remove('expanded');
        this.previewExpand.innerHTML = '<i class="fas fa-expand-alt"></i><span>Expand</span>';
        
        // Clear content after animation
        setTimeout(() => {
            this.previewContent.innerHTML = '';
            this.pastedContent = null;
        }, 300);
    }
    
    getPastedContent() {
        return this.pastedContent;
    }
    
    hasPastedContent() {
        return this.pastedContent !== null;
    }
    
    clearPastedContent() {
        this.pastedContent = null;
    }
}

// Initialize paste handler
document.addEventListener('DOMContentLoaded', () => {
    window.pasteHandler = new PasteHandler();
});