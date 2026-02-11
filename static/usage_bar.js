/**
 * XeerGPT Usage Bar
 * Polls /api/usage every 30s, ticks countdown every second
 */

class UsageBar {
    constructor() {
        this.stats = null;
        this.pollingInterval = null;
        this.countdownInterval = null;
        this.panel = null;

        this.init();
    }

    async init() {
        this.injectPanel();
        await this.fetchAndRender();
        this.startPolling();
        this.startCountdown();
    }

    injectPanel() {
        // Insert before sidebar-footer
        const sidebarFooter = document.querySelector('.sidebar-footer');
        if (!sidebarFooter) return;

        const panel = document.createElement('div');
        panel.className = 'usage-panel';
        panel.id = 'usagePanel';
        panel.innerHTML = this.skeletonHTML();
        sidebarFooter.parentNode.insertBefore(panel, sidebarFooter);
        this.panel = panel;
    }

    skeletonHTML() {
        return `
            <div class="usage-panel-header">
                <span class="usage-panel-title">
                    <i class="fas fa-chart-bar"></i> API Usage
                </span>
            </div>
            <div class="usage-skeleton">
                <div class="usage-skeleton-bar"></div>
                <div class="usage-skeleton-text"></div>
            </div>
        `;
    }

    async fetchAndRender() {
        try {
            const res = await fetch('/api/usage');
            if (!res.ok) throw new Error('Failed');
            const data = await res.json();
            this.stats = data.stats;
            this.render();
        } catch (e) {
            console.warn('Usage fetch failed:', e);
            if (this.panel) {
                this.panel.innerHTML = `
                    <div class="usage-panel-header">
                        <span class="usage-panel-title">
                            <i class="fas fa-chart-bar"></i> API Usage
                        </span>
                    </div>
                    <div style="font-size:0.7rem; color:var(--text-muted); text-align:center; padding:4px 0;">
                        Unavailable
                    </div>
                `;
            }
        }
    }

    render() {
        if (!this.panel || !this.stats) return;

        const providers = Object.entries(this.stats);
        if (providers.length === 0) return;

        let html = `
            <div class="usage-panel-header">
                <span class="usage-panel-title">
                    <i class="fas fa-chart-bar"></i> API Usage
                </span>
                <button class="usage-refresh-btn" id="usageRefreshBtn" title="Refresh">
                    <i class="fas fa-rotate-right"></i>
                </button>
            </div>
        `;

        providers.forEach(([key, s], index) => {
            const pct = s.percent_used;
            const barWidth = Math.max(0, Math.min(100, pct));

            html += `
                <div class="usage-provider" data-provider="${key}">
                    <div class="usage-provider-row">
                        <span class="usage-provider-label" title="${s.used} / ${s.limit} requests used today">
                            <span class="usage-provider-icon">${s.icon}</span>
                            ${s.display_name}
                        </span>
                        <span class="usage-percent-badge status-${s.status}">${pct}%</span>
                    </div>
                    <div class="usage-bar-track">
                        <div class="usage-bar-fill status-${s.status}" style="width: ${barWidth}%"></div>
                    </div>
                    <div class="usage-meta">
                        <span class="usage-remaining">
                            <span class="remaining-count">${s.remaining.toLocaleString()}</span>&nbsp;left
                        </span>
                        <span class="usage-reset" title="Resets at ${s.reset_time_local}">
                            <i class="fas fa-clock"></i>
                            Resets in <span class="countdown-timer" data-seconds="${s.reset_in_seconds}">${s.reset_countdown}</span>
                        </span>
                    </div>
                </div>
            `;

            if (index < providers.length - 1) {
                html += `<div class="usage-provider-divider"></div>`;
            }
        });

        this.panel.innerHTML = html;

        // Wire up refresh button
        const refreshBtn = document.getElementById('usageRefreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', async () => {
                refreshBtn.classList.add('spinning');
                await this.fetchAndRender();
                setTimeout(() => refreshBtn.classList.remove('spinning'), 600);
            });
        }
    }

    startPolling() {
        // Refresh every 30 seconds
        this.pollingInterval = setInterval(() => {
            this.fetchAndRender();
        }, 30000);
    }

    startCountdown() {
        // Tick every second to update countdown timers
        this.countdownInterval = setInterval(() => {
            const timers = document.querySelectorAll('.countdown-timer[data-seconds]');
            timers.forEach(el => {
                let seconds = parseInt(el.dataset.seconds, 10);
                if (isNaN(seconds) || seconds <= 0) {
                    el.textContent = '0s';
                    el.dataset.seconds = 0;
                    // Trigger a fresh fetch when a timer hits 0
                    this.fetchAndRender();
                    return;
                }
                seconds -= 1;
                el.dataset.seconds = seconds;
                el.textContent = this.formatCountdown(seconds);
            });
        }, 1000);
    }

    formatCountdown(seconds) {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = seconds % 60;
        if (h > 0) return `${h}h ${m}m`;
        if (m > 0) return `${m}m ${s}s`;
        return `${s}s`;
    }

    // Call this after each successful API call to update stats immediately
    refresh() {
        this.fetchAndRender();
    }

    destroy() {
        clearInterval(this.pollingInterval);
        clearInterval(this.countdownInterval);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.usageBar = new UsageBar();
});