class ChatManager {
    constructor() {
        this.currentChat = null;
        this.chats = [];
        this.typingUsers = new Map();
        this.typingTimeout = null;
    }

    init() {
        this.bindEvents();
    }
    
    initializeForUser() {
        this.loadChats();
    }

    bindEvents() {
        const messageInput = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');

        messageInput.addEventListener('input', () => this.handleTyping());
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        sendBtn.addEventListener('click', () => this.sendMessage());

        document.getElementById('attachment-btn').addEventListener('click', () => {
            ui.showFileUploadModal();
        });

        const userSearch = document.getElementById('user-search');
        let searchTimeout;
        
        userSearch.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.searchUsers(e.target.value);
            }, 300);
        });

        document.getElementById('new-chat-btn').addEventListener('click', () => {
            userSearch.value = '';
            userSearch.focus();
        });

        document.getElementById('files-btn').addEventListener('click', () => {
            this.toggleFilesPanel();
        });

        document.getElementById('close-files-panel').addEventListener('click', () => {
            this.closeFilesPanel();
        });
    }

    async loadChats() {
        try {
            this.chats = await api.getChats();
            this.renderChatsList();
        } catch (error) {
            ui.showToast('Failed to load chats', 'error');
        }
    }

    renderChatsList() {
        const chatsList = document.getElementById('chats-list');
        chatsList.innerHTML = '';

        if (this.chats.length === 0) {
            chatsList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-comments"></i>
                    <p>No chats yet</p>
                    <small>Start a new conversation!</small>
                </div>
            `;
            return;
        }

        this.chats.forEach(chat => {
            const lastMessage = chat.last_message?.content || 'No messages yet';
            const time = chat.last_message_at ? this.formatTime(chat.last_message_at) : '';
            
            const chatElement = document.createElement('div');
            chatElement.className = `chat-item ${this.currentChat?.id === chat.id ? 'active' : ''}`;
            chatElement.innerHTML = `
                <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(chat.other_user.full_name)}&background=10b981&color=fff" 
                     alt="${chat.other_user.full_name}" class="chat-avatar">
                <div class="chat-info">
                    <div class="chat-header">
                        <span class="chat-partner">${chat.other_user.full_name}</span>
                        <span class="chat-time">${time}</span>
                    </div>
                    <div class="chat-last-message">${lastMessage}</div>
                </div>
                <div class="chat-unread" style="display: none">0</div>
            `;

            chatElement.addEventListener('click', () => {
                this.selectChat(chat);
            });

            chatsList.appendChild(chatElement);
        });
    }

    async selectChat(chat) {
        this.currentChat = chat;
        
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const chatItems = document.querySelectorAll('.chat-item');
        chatItems.forEach(item => {
            const chatPartner = item.querySelector('.chat-partner');
            if (chatPartner && chatPartner.textContent === chat.other_user.full_name) {
                item.classList.add('active');
            }
        });

        document.getElementById('welcome-screen').classList.add('hidden');
        document.getElementById('active-chat').classList.remove('hidden');

        this.updateChatHeader(chat);

        websocketManager.joinChat(chat.id);

        await this.loadMessages(chat.id);

        await this.loadFiles(chat.id);

        this.closeSearchResults();
    }

    updateChatHeader(chat) {
        document.getElementById('partner-name').textContent = chat.other_user.full_name;
        document.getElementById('partner-avatar').src = 
            `https://ui-avatars.com/api/?name=${encodeURIComponent(chat.other_user.full_name)}&background=10b981&color=fff`;
    }

    async loadMessages(chatId) {
        try {
            const messages = await api.getChatMessages(chatId);
            this.renderMessages(messages);
        } catch (error) {
            ui.showToast('Failed to load messages', 'error');
        }
    }

    renderMessages(messages) {
        const container = document.getElementById('messages-container');
        container.innerHTML = '';

        messages.forEach(message => {
            this.appendMessage(message);
        });

        this.scrollToBottom();
    }

    appendMessage(message) {
        const container = document.getElementById('messages-container');
        const isSent = message.sender_id === authManager.getCurrentUser().id;
        
        const messageElement = document.createElement('div');
        messageElement.className = `message ${isSent ? 'sent' : 'received'}`;
        messageElement.dataset.messageId = message.id;
        
        const time = this.formatTime(message.sent_at);
        
        messageElement.innerHTML = `
            <div class="message-content">${this.escapeHtml(message.content)}</div>
            <div class="message-time">${time}</div>
            ${isSent ? `<div class="message-status">${message.is_read ? '✓✓' : '✓'}</div>` : ''}
        `;

        container.appendChild(messageElement);
    }

    async sendMessage() {
        const input = document.getElementById('message-input');
        const content = input.value.trim();

        if (!content || !this.currentChat) return;

        try {
            input.value = '';

            const message = await api.sendMessage(this.currentChat.id, content);
            
            this.appendMessage(message);
            this.scrollToBottom();

            this.stopTyping();

        } catch (error) {
            ui.showToast('Failed to send message', 'error');
            input.value = content;
        }
    }

    handleNewMessage(message, chatId) {
        if (this.currentChat && this.currentChat.id === chatId) {
            this.appendMessage(message);
            this.scrollToBottom();
            
            this.markMessagesAsRead([message.id]);
        }

        this.loadChats();
    }

    handleTypingIndicator(userId, chatId, isTyping) {
        if (!this.currentChat || this.currentChat.id !== chatId) return;

        const typingIndicator = document.getElementById('typing-indicator');
        
        if (isTyping) {
            this.typingUsers.set(userId, true);
            typingIndicator.classList.remove('hidden');
            
            const user = this.currentChat.other_user;
            typingIndicator.querySelector('span:last-child').textContent = `${user.full_name} is typing...`;
        } else {
            this.typingUsers.delete(userId);
            if (this.typingUsers.size === 0) {
                typingIndicator.classList.add('hidden');
            }
        }
    }

    handleTyping() {
        if (!this.currentChat) return;

        websocketManager.sendTypingIndicator(this.currentChat.id, true);

        clearTimeout(this.typingTimeout);

        this.typingTimeout = setTimeout(() => {
            this.stopTyping();
        }, 1000);
    }

    stopTyping() {
        if (!this.currentChat) return;

        clearTimeout(this.typingTimeout);
        websocketManager.sendTypingIndicator(this.currentChat.id, false);
    }

    async searchUsers(query) {
        if (!query.trim()) {
            this.renderChatsList();
            return;
        }

        try {
            const users = await api.searchUsers(query);
            this.showSearchResults(users);
        } catch (error) {
            console.error('Search failed:', error);
        }
    }

    showSearchResults(users) {
        const chatsList = document.getElementById('chats-list');
        
        if (users.length === 0) {
            chatsList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <p>No users found</p>
                </div>
            `;
            return;
        }

        chatsList.innerHTML = '';
        
        users.forEach(user => {
            const currentUser = authManager.getCurrentUser();
            if (currentUser && user.id === currentUser.id) {
                return;
            }

            const userElement = document.createElement('div');
            userElement.className = 'chat-item search-result';
            userElement.innerHTML = `
                <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(user.full_name)}&background=6366f1&color=fff" 
                     alt="${user.full_name}" class="chat-avatar">
                <div class="chat-info">
                    <div class="chat-header">
                        <span class="chat-partner">${user.full_name}</span>
                    </div>
                    <div class="chat-last-message">@${user.username}</div>
                </div>
                <i class="fas fa-plus"></i>
            `;

            userElement.addEventListener('click', async () => {
                if (userElement.classList.contains('loading')) return;
                
                userElement.classList.add('loading');
                await this.startChat(user.username);
                userElement.classList.remove('loading');
            });

            chatsList.appendChild(userElement);
        });
    }

    async startChat(username) {
        if (!username || typeof username !== 'string') {
            ui.showToast('Invalid username', 'error');
            return;
        }

        const trimmedUsername = username.trim();
        if (trimmedUsername.length < 3) {
            ui.showToast('Username must be at least 3 characters', 'error');
            return;
        }

        const currentUser = authManager.getCurrentUser();
        if (currentUser && currentUser.username === trimmedUsername) {
            ui.showToast('Cannot start chat with yourself', 'warning');
            return;
        }

        try {
            ui.showLoading(true);
            
            const chat = await api.createOrGetChat(trimmedUsername);
            
            if (!chat || !chat.id) {
                throw new Error('Invalid chat response from server');
            }
            
            await this.selectChat(chat);
            
            await this.loadChats();
            
            ui.showToast(`Chat started with ${trimmedUsername}`, 'success');
            
        } catch (error) {
            console.error('Start chat error:', error);
            
            if (error.message.includes('User not found')) {
                ui.showToast('User not found', 'error');
            } else if (error.message.includes('Cannot create chat with yourself')) {
                ui.showToast('Cannot start chat with yourself', 'warning');
            } else if (error.message.includes('already exists')) {
                await this.loadChats();
                ui.showToast('Chat already exists', 'info');
            } else {
                ui.showToast(error.message || 'Failed to start chat', 'error');
            }
        } finally {
            ui.showLoading(false);
        }
    }

    async loadFiles(chatId) {
        try {
            const files = await api.getChatFiles(chatId);
            this.renderFiles(files);
        } catch (error) {
            console.error('Failed to load files:', error);
        }
    }

    renderFiles(files) {
        const filesList = document.getElementById('files-list');
        filesList.innerHTML = '';

        if (files.length === 0) {
            filesList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-file"></i>
                    <p>No files shared yet</p>
                </div>
            `;
            return;
        }

        files.forEach(file => {
            const fileElement = document.createElement('div');
            fileElement.className = 'file-item';
            fileElement.innerHTML = `
                <div class="file-icon">
                    <i class="fas fa-file"></i>
                </div>
                <div class="file-info">
                    <span class="file-name">${file.filename}</span>
                    <span class="file-size">${this.formatFileSize(file.file_size)}</span>
                </div>
                <div class="file-actions">
                    <a href="${file.download_url}" download class="icon-btn" title="Download">
                        <i class="fas fa-download"></i>
                    </a>
                </div>
            `;

            filesList.appendChild(fileElement);
        });
    }

    handleFileUploaded(file, chatId) {
        if (this.currentChat && this.currentChat.id === chatId) {
            this.loadFiles(chatId);
            ui.showToast(`New file: ${file.filename}`, 'success');
        }
    }

    toggleFilesPanel() {
        document.getElementById('files-panel').classList.toggle('hidden');
    }

    closeFilesPanel() {
        document.getElementById('files-panel').classList.add('hidden');
    }

    closeSearchResults() {
        const userSearch = document.getElementById('user-search');
        userSearch.value = '';
        this.renderChatsList();
    }

    markMessagesAsRead(messageIds = null) {
        if (!this.currentChat) return;
    }

    scrollToBottom() {
        const container = document.getElementById('messages-container');
        container.scrollTop = container.scrollHeight;
    }

    formatTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return diffMins + 'm ago';
        if (diffHours < 24) return diffHours + 'h ago';
        if (diffDays < 7) return diffDays + 'd ago';
        
        return date.toLocaleDateString();
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

const chatManager = new ChatManager();