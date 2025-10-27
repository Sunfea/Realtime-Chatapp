class AuthManager {
    constructor() {
        this.currentUser = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkAuthStatus();
    }

    bindEvents() {
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Form submissions
        document.getElementById('login-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        document.getElementById('register-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleRegister();
        });

        // Logout
        document.getElementById('logout-btn').addEventListener('click', () => {
            this.handleLogout();
        });
    }

    switchTab(tab) {
        // Update active tab button
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tab);
        });

        // Show active form
        document.querySelectorAll('.auth-form').forEach(form => {
            form.classList.toggle('active', form.id === `${tab}-form`);
        });
    }

    async handleLogin() {
        const form = document.getElementById('login-form');
        const button = form.querySelector('button');
        const btnText = button.querySelector('.btn-text');
        const btnLoader = button.querySelector('.btn-loader');

        const credentials = {
            username: document.getElementById('login-username').value.trim(),
            password: document.getElementById('login-password').value
        };

        if (!credentials.username || !credentials.password) {
            ui.showToast('Please fill in all fields', 'error');
            return;
        }

        try {
            this.setButtonLoading(button, true);
            
            const response = await api.login(credentials);
            api.setToken(response.access_token);
            
            await this.loadCurrentUser();
            this.showChatApp();
            
            ui.showToast('Login successful!', 'success');
        } catch (error) {
            ui.showToast(error.message || 'Login failed', 'error');
        } finally {
            this.setButtonLoading(button, false);
        }
    }

    async handleRegister() {
        const form = document.getElementById('register-form');
        const button = form.querySelector('button');
        
        const userData = {
            full_name: document.getElementById('register-fullname').value.trim(),
            username: document.getElementById('register-username').value.trim().toLowerCase(),
            email: document.getElementById('register-email').value.trim(),
            password: document.getElementById('register-password').value
        };

        // Basic validation
        if (Object.values(userData).some(value => !value)) {
            ui.showToast('Please fill in all fields', 'error');
            return;
        }

        if (userData.username.length < 3) {
            ui.showToast('Username must be at least 3 characters', 'error');
            return;
        }

        try {
            this.setButtonLoading(button, true);
            
            await api.register(userData);
            ui.showToast('Registration successful! Please login.', 'success');
            
            // Switch to login tab
            this.switchTab('login');
            form.reset();
        } catch (error) {
            ui.showToast(error.message || 'Registration failed', 'error');
        } finally {
            this.setButtonLoading(button, false);
        }
    }

    setButtonLoading(button, loading) {
        const btnText = button.querySelector('.btn-text');
        const btnLoader = button.querySelector('.btn-loader');
        
        if (loading) {
            btnText.classList.add('hidden');
            btnLoader.classList.remove('hidden');
            button.disabled = true;
        } else {
            btnText.classList.remove('hidden');
            btnLoader.classList.add('hidden');
            button.disabled = false;
        }
    }

    async checkAuthStatus() {
        const token = localStorage.getItem('chat_token');
        if (token) {
            try {
                api.setToken(token);
                await this.loadCurrentUser();
                this.showChatApp();
            } catch (error) {
                console.error('Auth check failed:', error);
                this.handleLogout();
            }
        }
    }

    async loadCurrentUser() {
        try {
            this.currentUser = await api.getCurrentUser();
            this.updateUserUI();
        } catch (error) {
            throw new Error('Failed to load user data');
        }
    }

    updateUserUI() {
        if (this.currentUser) {
            // Update user info in sidebar
            document.getElementById('user-name').textContent = this.currentUser.full_name;
            
            // Update avatar
            const avatar = document.getElementById('user-avatar');
            avatar.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(this.currentUser.full_name)}&background=6366f1&color=fff`;
        }
    }

    showChatApp() {
    document.getElementById('auth-screen').classList.remove('active');
    document.getElementById('chat-app').classList.add('active');
    
    // Initialize chat functionality ONLY after login
    chatManager.init();                    // ← Sets up event listeners
    chatManager.initializeForUser();       // ← NEW: Load chats only after auth
    websocketManager.connect();            // ← Connect WebSocket
    }

    handleLogout() {
        api.setToken(null);
        this.currentUser = null;
        
        // Close WebSocket connection
        websocketManager.disconnect();
        
        // Reset forms
        document.getElementById('login-form').reset();
        document.getElementById('register-form').reset();
        
        // Show auth screen
        document.getElementById('chat-app').classList.remove('active');
        document.getElementById('auth-screen').classList.add('active');
        
        // Switch to login tab
        this.switchTab('login');
        
        ui.showToast('Logged out successfully', 'success');
    }

    getCurrentUser() {
        return this.currentUser;
    }
}

// Create global auth instance
const authManager = new AuthManager();