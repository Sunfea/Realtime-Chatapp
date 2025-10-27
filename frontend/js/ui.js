class UIManager {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // File upload modal
        document.getElementById('close-upload-modal').addEventListener('click', () => {
            this.hideFileUploadModal();
        });

        document.getElementById('cancel-upload').addEventListener('click', () => {
            this.hideFileUploadModal();
        });

        document.getElementById('upload-area').addEventListener('click', () => {
            document.getElementById('file-input').click();
        });

        document.getElementById('file-input').addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files[0]);
        });

        document.getElementById('remove-file').addEventListener('click', () => {
            this.clearFileSelection();
        });

        document.getElementById('confirm-upload').addEventListener('click', () => {
            this.uploadSelectedFile();
        });

        // Drag and drop for file upload
        const uploadArea = document.getElementById('upload-area');
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = 'var(--primary)';
            uploadArea.style.background = 'var(--bg-secondary)';
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = 'var(--border)';
            uploadArea.style.background = 'var(--bg)';
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = 'var(--border)';
            uploadArea.style.background = 'var(--bg)';
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0]);
            }
        });
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = this.getToastIcon(type);
        
        toast.innerHTML = `
            <i class="fas fa-${icon}"></i>
            <span>${message}</span>
        `;

        container.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.animation = 'slideIn 0.3s ease reverse';
                setTimeout(() => toast.remove(), 300);
            }
        }, 5000);
    }

    getToastIcon(type) {
        switch (type) {
            case 'success': return 'check-circle';
            case 'error': return 'exclamation-circle';
            case 'warning': return 'exclamation-triangle';
            default: return 'info-circle';
        }
    }

    showFileUploadModal() {
        if (!chatManager.currentChat) {
            this.showToast('Please select a chat first', 'warning');
            return;
        }

        this.clearFileSelection();
        document.getElementById('file-upload-modal').classList.remove('hidden');
    }

    hideFileUploadModal() {
        document.getElementById('file-upload-modal').classList.add('hidden');
        this.clearFileSelection();
    }

    handleFileSelect(file) {
        if (!file) return;

        // Validate file size (10MB limit)
        if (file.size > 10 * 1024 * 1024) {
            this.showToast('File size must be less than 10MB', 'error');
            return;
        }

        // Show file preview
        const preview = document.getElementById('file-preview');
        const uploadArea = document.getElementById('upload-area');
        
        document.getElementById('preview-file-name').textContent = file.name;
        document.getElementById('preview-file-size').textContent = this.formatFileSize(file.size);
        
        uploadArea.classList.add('hidden');
        preview.classList.remove('hidden');
        
        // Enable upload button
        document.getElementById('confirm-upload').disabled = false;

        // Store file reference
        this.selectedFile = file;
    }

    clearFileSelection() {
        const preview = document.getElementById('file-preview');
        const uploadArea = document.getElementById('upload-area');
        
        uploadArea.classList.remove('hidden');
        preview.classList.add('hidden');
        
        document.getElementById('file-input').value = '';
        document.getElementById('confirm-upload').disabled = true;
        
        this.selectedFile = null;
    }

    async uploadSelectedFile() {
        if (!this.selectedFile || !chatManager.currentChat) return;

        try {
            this.showLoading(true);
            
            await api.uploadFile(chatManager.currentChat.id, this.selectedFile);
            
            this.hideFileUploadModal();
            this.showToast('File uploaded successfully', 'success');
            
            // Refresh files list
            chatManager.loadFiles(chatManager.currentChat.id);
            
        } catch (error) {
            this.showToast(error.message || 'File upload failed', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        if (show) {
            overlay.classList.remove('hidden');
        } else {
            overlay.classList.add('hidden');
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Mobile responsive helpers
    toggleSidebar() {
        document.querySelector('.sidebar').classList.toggle('active');
    }

    closeSidebar() {
        document.querySelector('.sidebar').classList.remove('active');
    }

    toggleFilesPanel() {
        document.getElementById('files-panel').classList.toggle('active');
    }

    closeFilesPanel() {
        document.getElementById('files-panel').classList.remove('active');
    }
}

// Create global UI instance
const ui = new UIManager();

// Mobile menu toggle (add to index.html if needed)
document.addEventListener('DOMContentLoaded', function() {
    // Add mobile menu button if needed
    if (window.innerWidth <= 768) {
        const chatHeader = document.querySelector('.chat-header');
        if (chatHeader && !document.getElementById('mobile-menu-btn')) {
            const menuBtn = document.createElement('button');
            menuBtn.className = 'icon-btn mobile-menu-btn';
            menuBtn.innerHTML = '<i class="fas fa-bars"></i>';
            menuBtn.id = 'mobile-menu-btn';
            menuBtn.addEventListener('click', () => ui.toggleSidebar());
            
            chatHeader.insertBefore(menuBtn, chatHeader.firstChild);
        }
    }
});