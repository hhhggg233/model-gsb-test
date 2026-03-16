const token = localStorage.getItem('token');
const user = JSON.parse(localStorage.getItem('user') || '{}');

if (!token) {
    window.location.href = '/login';
}

let socket;
let currentChatUser = null;

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('current-user').textContent = `欢迎, ${user.username}`;
    
    initSocket();
    loadConversations();
    loadUsers();
    
    document.getElementById('send-btn').addEventListener('click', sendMessage);
    document.getElementById('message-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});

function initSocket() {
    socket = io();
    
    socket.on('connect', () => {
        socket.emit('join', { user_id: user.id });
    });
    
    socket.on('new_message', (data) => {
        if (currentChatUser && data.sender_id === currentChatUser.id) {
            appendMessage(data, false);
        }
        loadConversations();
    });
    
    socket.on('message_sent', (data) => {
        appendMessage(data, true);
    });
}

async function loadConversations() {
    try {
        const response = await fetch('/api/chat/conversations', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        renderConversations(data.conversations);
    } catch (error) {
        console.error('加载会话失败:', error);
    }
}

async function loadUsers() {
    try {
        const response = await fetch('/api/users', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
            const data = await response.json();
            renderUsers(data.users);
        }
    } catch (error) {
        console.error('加载用户失败:', error);
    }
}

function renderConversations(conversations) {
    const list = document.getElementById('conversation-list');
    list.innerHTML = '';
    
    conversations.forEach(conv => {
        const li = document.createElement('li');
        li.textContent = conv.username;
        li.onclick = () => startChat(conv.user_id, conv.username);
        list.appendChild(li);
    });
}

function renderUsers(users) {
    const list = document.getElementById('user-list');
    list.innerHTML = '';
    
    users.filter(u => u.id !== user.id).forEach(u => {
        const li = document.createElement('li');
        li.textContent = u.username;
        li.onclick = () => startChat(u.id, u.username);
        list.appendChild(li);
    });
}

async function startChat(userId, username) {
    currentChatUser = { id: userId, username };
    document.getElementById('chat-with').textContent = `与 ${username} 聊天`;
    document.getElementById('message-input').disabled = false;
    document.getElementById('send-btn').disabled = false;
    
    document.getElementById('messages').innerHTML = '';
    
    try {
        const response = await fetch(`/api/chat/messages?user_id=${userId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        
        data.messages.forEach(msg => {
            appendMessage(msg, msg.sender_id === user.id);
        });
    } catch (error) {
        console.error('加载消息失败:', error);
    }
}

function appendMessage(msg, isSent) {
    const messagesDiv = document.getElementById('messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${isSent ? 'sent' : 'received'}`;
    msgDiv.innerHTML = `
        <div class="message-content">${escapeHtml(msg.content)}</div>
        <div class="message-time">${new Date(msg.created_at).toLocaleString()}</div>
    `;
    messagesDiv.appendChild(msgDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function sendMessage() {
    const input = document.getElementById('message-input');
    const content = input.value.trim();
    
    if (!content || !currentChatUser) return;
    
    socket.emit('send_message', {
        sender_id: user.id,
        receiver_id: currentChatUser.id,
        content: content
    });
    
    input.value = '';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
}
