"""
Bulk Analysis Page Styles
Premium SaaS styling for the bulk log analysis page.
"""

BULK_ANALYSIS_CSS = """
/* ========== PREMIUM CARD SYSTEM ========== */
.premium-card {
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.95)) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 16px !important;
    padding: 24px !important;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2), 0 1px 4px rgba(255, 255, 255, 0.04) !important;
    backdrop-filter: blur(12px) !important;
    min-height: 0 !important;
    height: auto !important;
}

/* ========== CARD TITLES ========== */
.card-title {
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    color: #f8fafc !important;
    margin: 0 0 4px 0 !important;
    letter-spacing: -0.01em !important;
}

.card-subtitle {
    font-size: 0.8rem !important;
    color: #94a3b8 !important;
    margin: 0 0 8px 0 !important;
}

.card-divider {
    margin: 8px 0 !important;
    opacity: 0.3 !important;
}

/* ========== STAT CARDS ========== */
.stat-card {
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    border-radius: 12px !important;
    padding: 16px !important;
    min-height: 100px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    transition: all 0.2s ease !important;
}

.stat-card:hover {
    border-color: rgba(56, 189, 248, 0.3) !important;
    box-shadow: 0 4px 12px rgba(56, 189, 248, 0.1) !important;
}

.stat-card-inner {
    padding-left: 12px !important;
}

.stat-icon {
    font-size: 1.5rem !important;
    margin-bottom: 4px !important;
}

.stat-value {
    font-size: 1.8rem !important;
    font-weight: 800 !important;
    line-height: 1.2 !important;
    font-family: 'Inter', 'SF Pro Display', sans-serif !important;
}

.stat-label {
    font-size: 0.75rem !important;
    color: #64748b !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}

/* ========== UPLOAD ZONE ========== */
.upload-zone {
    border: 2px dashed rgba(255, 255, 255, 0.15) !important;
    border-radius: 16px !important;
    padding: 32px 24px !important;
    text-align: center !important;
    background: rgba(0, 0, 0, 0.2) !important;
    transition: all 0.3s ease !important;
    min-height: 160px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
}

.upload-zone:hover {
    border-color: rgba(56, 189, 248, 0.5) !important;
    background: rgba(56, 189, 248, 0.05) !important;
    box-shadow: 0 0 20px rgba(56, 189, 248, 0.1) !important;
}

.upload-zone.drag-over {
    border-color: #38bdf8 !important;
    background: rgba(56, 189, 248, 0.1) !important;
}

.upload-icon {
    font-size: 3rem !important;
    margin-bottom: 12px !important;
    opacity: 0.6 !important;
}

.upload-text {
    font-size: 1rem !important;
    color: #e2e8f0 !important;
    font-weight: 600 !important;
}

.upload-hint {
    font-size: 0.8rem !important;
    color: #64748b !important;
    margin-top: 6px !important;
}

/* ========== PROGRESS BAR ========== */
.progress-container {
    padding: 8px 0 !important;
}

.progress-header {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    margin-bottom: 6px !important;
}

.progress-label {
    font-size: 0.8rem !important;
    color: #94a3b8 !important;
    font-weight: 500 !important;
}

.progress-pct {
    font-size: 0.8rem !important;
    font-weight: 700 !important;
}

.progress-track {
    height: 6px !important;
    background: rgba(255, 255, 255, 0.05) !important;
    border-radius: 3px !important;
    overflow: hidden !important;
}

.progress-fill {
    height: 100% !important;
    border-radius: 3px !important;
    transition: width 0.5s ease !important;
    background: linear-gradient(90deg, #38bdf8, #818cf8) !important;
}

/* ========== STEP PROGRESS ========== */
.step-progress {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 0 !important;
    padding: 16px 0 !important;
}

.step-item {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    gap: 6px !important;
}

.step-circle {
    width: 36px !important;
    height: 36px !important;
    border-radius: 50% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 1rem !important;
    background: rgba(255, 255, 255, 0.05) !important;
    border: 2px solid rgba(255, 255, 255, 0.1) !important;
}

.step-item.completed .step-circle {
    background: rgba(16, 185, 129, 0.15) !important;
    border-color: #10b981 !important;
}

.step-item.active .step-circle {
    background: rgba(56, 189, 248, 0.15) !important;
    border-color: #38bdf8 !important;
    animation: pulse 2s infinite !important;
}

@keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.4); }
    50% { box-shadow: 0 0 0 8px rgba(56, 189, 248, 0); }
}

.step-label {
    font-size: 0.7rem !important;
    color: #64748b !important;
    font-weight: 500 !important;
    white-space: nowrap !important;
}

.step-item.completed .step-label,
.step-item.active .step-label {
    color: #e2e8f0 !important;
}

.step-connector {
    width: 40px !important;
    height: 2px !important;
    background: rgba(255, 255, 255, 0.08) !important;
    margin: 0 4px !important;
    margin-bottom: 22px !important;
}

.step-connector.completed {
    background: #10b981 !important;
}

/* ========== LOADING SPINNER ========== */
.loading-container {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 40px !important;
    gap: 16px !important;
}

.loading-spinner {
    width: 48px !important;
    height: 48px !important;
    border: 3px solid rgba(255, 255, 255, 0.1) !important;
    border-top-color: #38bdf8 !important;
    border-radius: 50% !important;
    animation: spin 0.8s linear infinite !important;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.loading-message {
    color: #94a3b8 !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
}

/* ========== RESULTS PANEL ========== */
.results-panel {
    max-height: 600px !important;
    overflow-y: auto !important;
    padding-right: 8px !important;
}

.results-panel::-webkit-scrollbar {
    width: 4px !important;
}

.results-panel::-webkit-scrollbar-track {
    background: transparent !important;
}

.results-panel::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1) !important;
    border-radius: 2px !important;
}

/* ========== RESPONSIVE GRID ========== */
.bulk-grid {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)) !important;
    gap: 12px !important;
}

/* ========== GPU BADGE ========== */
.gpu-badge {
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
    padding: 4px 12px !important;
    border-radius: 20px !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
}

.gpu-active {
    background: rgba(16, 185, 129, 0.15) !important;
    color: #10b981 !important;
    border: 1px solid rgba(16, 185, 129, 0.3) !important;
}

.gpu-inactive {
    background: rgba(100, 116, 139, 0.15) !important;
    color: #64748b !important;
    border: 1px solid rgba(100, 116, 139, 0.3) !important;
}

/* ========== ROW EQUALIZATION ========== */
.bulk-row {
    display: flex !important;
    align-items: stretch !important;
    gap: 16px !important;
}

.bulk-row > * {
    flex: 1 !important;
    min-height: 0 !important;
}

/* ========== BUTTON ROW ========== */
.button-row {
    display: flex !important;
    gap: 10px !important;
    flex-wrap: wrap !important;
}

.button-row .gr-button {
    flex: 1 !important;
    min-width: 120px !important;
    height: 44px !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em !important;
}

/* ========== FILE INFO BADGE ========== */
.file-info {
    display: inline-flex !important;
    align-items: center !important;
    gap: 8px !important;
    padding: 8px 16px !important;
    background: rgba(56, 189, 248, 0.1) !important;
    border: 1px solid rgba(56, 189, 248, 0.2) !important;
    border-radius: 10px !important;
    font-size: 0.85rem !important;
}

/* ========== ALERT BANNER ========== */
.alert-banner {
    padding: 12px 16px !important;
    border-radius: 10px !important;
    margin: 12px 0 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}

.alert-success {
    background: rgba(16, 185, 129, 0.1) !important;
    border: 1px solid rgba(16, 185, 129, 0.3) !important;
    color: #10b981 !important;
}

.alert-error {
    background: rgba(239, 68, 68, 0.1) !important;
    border: 1px solid rgba(239, 68, 68, 0.3) !important;
    color: #ef4444 !important;
}

.alert-info {
    background: rgba(56, 189, 248, 0.1) !important;
    border: 1px solid rgba(56, 189, 248, 0.3) !important;
    color: #38bdf8 !important;
}
"""