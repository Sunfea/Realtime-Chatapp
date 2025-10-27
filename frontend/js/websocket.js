class WebSocketManager {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.currentChatId = null;
    }

    connect() {
        const user = authManager.getCurrentUser();
        if (!user || this.socket) return;

        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//localhost:8000/ws/${user.id}`;
            
            this.socket = new WebSocket(wsUrl);
            this.setupEventHandlers();
        } catch (error) {
            console.error('WebSocket connection failed:', error);
            this.scheduleReconnect();
        }
    }

    setupEventHandlers() {
        this.socket.onopen = () => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            ui.showToast('Connected', 'success');
        };

        this.socket.onmessage = (event) => {
            this.handleMessage(JSON.parse(event.data));
        };

        this.socket.onclose = (event) => {
            console.log('WebSocket disconnected:', event);
            this.isConnected = false;
            this.socket = null;
            
            if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
                this.scheduleReconnect();
            }
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            
            console.log(`Attempting reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
            setTimeout(() => this.connect(), delay);
        }
    }

    handleMessage(data) {
        switch (data.type) {
            case 'new_message':
                chatManager.handleNewMessage(data.message, data.chat_id);
                break;
                
            case 'message_read':
                chatManager.handleMessageRead(data.message_id, data.reader_id);
                break;
                
            case 'typing':
                chatManager.handleTypingIndicator(data.user_id, data.chat_id, data.is_typing);
                break;
                
            case 'file_uploaded':
                chatManager.handleFileUploaded(data.file, data.chat_id);
                break;
                
            case 'file_deleted':
                chatManager.handleFileDeleted(data.file_id, data.chat_id);
                break;
        }
    }

    send(data) {
        if (this.socket && this.isConnected) {
            this.socket.send(JSON.stringify(data));
        }
    }

    joinChat(chatId) {
        this.currentChatId = chatId;
        this.send({
            type: 'join_chat',
            chat_id: chatId
        });
    }

    sendTypingIndicator(chatId, isTyping) {
        this.send({
            type: 'typing',
            chat_id: chatId,
            is_typing: isTyping
        });
    }

    sendReadReceipt(messageId, chatId) {
        this.send({
            type: 'message_read',
            message_id: messageId,
            chat_id: chatId
        });
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        this.isConnected = false;
        this.currentChatId = null;
    }
}

// Create global WebSocket instance
const websocketManager = new WebSocketManager();