// API configuration
const API_BASE_URL = 'http://localhost:8000';

class API {
    constructor() {
        this.token = localStorage.getItem('chat_token');
    }

    async request(endpoint, options = {}) {
        // Don't make API calls if no token (except for auth endpoints)
        if (!this.token && !endpoint.includes('/auth/')) {
            console.log('Skipping API call - no authentication token');
            throw new Error('Authentication required');
        }

        const url = `${API_BASE_URL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };

        // Add authorization header if token exists
        if (this.token) {
            config.headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, config);
            
            if (response.status === 401) {
                // Token expired or invalid
                this.handleUnauthorized();
                throw new Error('Authentication required');
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            // For 204 No Content responses
            if (response.status === 204) {
                return null;
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('chat_token', token);
        } else {
            localStorage.removeItem('chat_token');
        }
    }

    handleUnauthorized() {
        this.setToken(null);
        window.location.reload();
    }

    // Auth endpoints
    async register(userData) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
    }

    async login(credentials) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify(credentials),
        });
    }

    // User endpoints
    async getCurrentUser() {
        return this.request('/users/me');
    }

    async updateProfile(fullName) {
        return this.request('/users/me', {
            method: 'PUT',
            body: JSON.stringify({ full_name: fullName }),
        });
    }

    async searchUsers(query) {
        return this.request(`/users/search?q=${encodeURIComponent(query)}`);
    }

    // Chat endpoints
    async getChats() {
        return this.request('/chats/');
    }

    async createOrGetChat(recipientUsername) {
        if (!recipientUsername || typeof recipientUsername !== 'string') {
            throw new Error('Valid username is required');
        }
        
        const encodedUsername = encodeURIComponent(recipientUsername.trim());
        
        return this.request(`/chats/?recipient_username=${encodedUsername}`, {
            method: 'POST',
        });
    }

    async getChatMessages(chatId) {
        return this.request(`/chats/${chatId}/messages`);
    }

    async sendMessage(chatId, content) {
        return this.request(`/chats/${chatId}/messages`, {
            method: 'POST',
            body: JSON.stringify({ content }),
        });
    }

    async markMessagesRead(messageIds) {
        return this.request('/chats/messages/read', {
            method: 'PUT',
            body: JSON.stringify({ message_ids: messageIds }),
        });
    }

    async getUnreadCount() {
        return this.request('/chats/unread-count');
    }

    // File endpoints
    async uploadFile(chatId, file) {
        // Don't proceed if no token
        if (!this.token) {
            throw new Error('Authentication required');
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${API_BASE_URL}/chats/${chatId}/files`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                },
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Upload failed! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('File upload failed:', error);
            throw error;
        }
    }

    async getChatFiles(chatId) {
        return this.request(`/chats/${chatId}/files`);
    }

    async deleteFile(fileId) {
        return this.request(`/files/${fileId}`, {
            method: 'DELETE',
        });
    }

    getFileUrl(filePath) {
        return `${API_BASE_URL}/files/${filePath}`;
    }

    // Utility method to check if user is authenticated
    isAuthenticated() {
        return !!this.token;
    }

    // Clear all stored data (for logout)
    clearAuth() {
        this.token = null;
        localStorage.removeItem('chat_token');
    }
}

// Create global API instance
const api = new API();