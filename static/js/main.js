// 全局变量
let currentUser = null;
let accessToken = localStorage.getItem('access_token');
let socket = null;
let selectedUserId = null;
let typingTimer = null;

// DOM 元素
const authSection = document.getElementById('auth-section');
const mainSection = document.getElementById('main-section');
const authForm = document.getElementById('auth-form');
const authTitle = document.getElementById('auth-title');
const authBtn = document.getElementById('auth-btn');
const authSwitchLink = document.getElementById('auth-switch-link');
const authSwitchText = document.getElementById('auth-switch-text');
const emailGroup = document.getElementById('email-group');
const authMessage = document.getElementById('auth-message');
const logoutBtn = document.getElementById('logout-btn');
const currentUserSpan = document.getElementById('current-user');
const userRoleSpan = document.getElementById('user-role');

// 初始化
async function init() {
    if (accessToken) {
        try {
            const response = await fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            });
            
            if (response.ok) {
                currentUser = await response.json();
                showMainSection();
                initSocket();
                loadUsersList();
                checkUnreadMessages();
            } else {
                localStorage.removeItem('access_token');
                accessToken = null;
            }
        } catch (error) {
            console.error('验证登录状态失败:', error);
        }
    }
}

// 显示主界面
function showMainSection() {
    authSection.style.display = 'none';
    mainSection.style.display = 'flex';
    currentUserSpan.textContent = currentUser.username;
    userRoleSpan.textContent = currentUser.role === 'admin' ? '管理员' : '普通用户';
    userRoleSpan.className = `role-badge ${currentUser.role}`;
    
    // 如果是管理员，显示用户管理菜单
    if (currentUser.role === 'admin') {
        document.querySelectorAll('.admin-only').forEach(el => {
            el.style.display = 'flex';
        });
    }
    
    renderProfile();
}

// 显示认证界面
function showAuthSection() {
    authSection.style.display = 'flex';
    mainSection.style.display = 'none';
    currentUser = null;
    selectedUserId = null;
}

// 切换登录/注册
let isLoginMode = true;
authSwitchLink.addEventListener('click', (e) => {
    e.preventDefault();
    isLoginMode = !isLoginMode;
    
    if (isLoginMode) {
        authTitle.textContent = '用户登录';
        authBtn.textContent = '登录';
        authSwitchText.textContent = '还没有账号？';
        authSwitchLink.textContent = '立即注册';
        emailGroup.style.display = 'none';
        document.getElementById('email').required = false;
    } else {
        authTitle.textContent = '用户注册';
        authBtn.textContent = '注册';
        authSwitchText.textContent = '已有账号？';
        authSwitchLink.textContent = '立即登录';
        emailGroup.style.display = 'block';
        document.getElementById('email').required = true;
    }
    
    authMessage.style.display = 'none';
    authForm.reset();
});

// 表单提交
authForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    const url = isLoginMode ? '/api/auth/login' : '/api/auth/register';
    const body = isLoginMode 
        ? { username, password }
        : { 
            username, 
            password, 
            email: document.getElementById('email').value 
        };
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            if (isLoginMode) {
                accessToken = data.access_token;
                localStorage.setItem('access_token', accessToken);
                currentUser = data.user;
                showMainSection();
                initSocket();
                loadUsersList();
            } else {
                showMessage('注册成功，请登录', 'success');
                // 切换到登录模式
                authSwitchLink.click();
            }
        } else {
            showMessage(data.error || '操作失败', 'error');
        }
    } catch (error) {
        showMessage('网络错误，请重试', 'error');
    }
});

// 显示消息
function showMessage(message, type) {
    authMessage.textContent = message;
    authMessage.className = type;
}

// 退出登录
logoutBtn.addEventListener('click', () => {
    if (socket) {
        socket.emit('leave', { user_id: currentUser.id });
        socket.disconnect();
    }
    localStorage.removeItem('access_token');
    accessToken = null;
    showAuthSection();
});

// 初始化 WebSocket
function initSocket() {
    socket = io();
    
    socket.on('connect', () => {
        console.log('WebSocket 已连接');
        socket.emit('join', { user_id: currentUser.id });
    });
    
    socket.on('disconnect', () => {
        console.log('WebSocket 已断开');
    });
    
    socket.on('new_message', (data) => {
        if (selectedUserId === data.sender_id) {
            appendMessage(data, false);
            scrollToBottom();
        } else {
            // 更新未读消息数
            checkUnreadMessages();
            // 刷新用户列表显示未读标记
            loadUsersList();
        }
    });
    
    socket.on('message_sent', (data) => {
        appendMessage(data, true);
        scrollToBottom();
    });
    
    socket.on('user_typing', (data) => {
        if (selectedUserId === data.sender_id) {
            showTypingIndicator(data.sender_username);
        }
    });
    
    socket.on('user_online', (data) => {
        loadUsersList();
    });
    
    socket.on('user_offline', (data) => {
        loadUsersList();
    });
}

// 加载用户列表
async function loadUsersList() {
    try {
        const response = await fetch('/api/users/list', {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        if (response.ok) {
            const users = await response.json();
            renderUserList(users);
        }
    } catch (error) {
        console.error('加载用户列表失败:', error);
    }
}

// 渲染用户列表
function renderUserList(users) {
    const userListEl = document.getElementById('user-list');
    userListEl.innerHTML = '';
    
    users.forEach(user => {
        const userItem = document.createElement('div');
        userItem.className = `user-item ${user.id === selectedUserId ? 'active' : ''}`;
        userItem.dataset.userId = user.id;
        userItem.innerHTML = `
            <span class="online-status"></span>
            <span>${user.username}</span>
        `;
        
        userItem.addEventListener('click', () => selectUser(user));
        userListEl.appendChild(userItem);
    });
}

// 选择用户进行聊天
async function selectUser(user) {
    selectedUserId = user.id;
    
    // 更新选中状态
    document.querySelectorAll('.user-item').forEach(item => {
        item.classList.remove('active');
        if (parseInt(item.dataset.userId) === user.id) {
            item.classList.add('active');
        }
    });
    
    // 更新聊天头部
    document.getElementById('chat-header').innerHTML = `
        <span>与 ${user.username} 聊天中</span>
    `;
    
    // 启用输入框
    document.getElementById('message-input').disabled = false;
    document.getElementById('send-btn').disabled = false;
    
    // 加载聊天记录
    await loadMessages(user.id);
}

// 加载聊天记录
async function loadMessages(userId) {
    try {
        const response = await fetch(`/api/messages/${userId}`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        if (response.ok) {
            const messages = await response.json();
            renderMessages(messages);
            scrollToBottom();
        }
    } catch (error) {
        console.error('加载消息失败:', error);
    }
}

// 渲染消息
function renderMessages(messages) {
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.innerHTML = '';
    
    messages.forEach(message => {
        const isSent = message.sender_id === currentUser.id;
        appendMessage(message, isSent);
    });
}

// 添加单条消息
function appendMessage(message, isSent) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageEl = document.createElement('div');
    messageEl.className = `message ${isSent ? 'sent' : 'received'}`;
    
    const time = new Date(message.created_at).toLocaleString();
    messageEl.innerHTML = `
        <div>${message.content}</div>
        <div class="message-time">${time}</div>
    `;
    
    messagesContainer.appendChild(messageEl);
}

// 滚动到底部
function scrollToBottom() {
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// 发送消息
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');

sendBtn.addEventListener('click', sendMessage);

messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    } else {
        // 发送正在输入状态
        if (selectedUserId && socket) {
            clearTimeout(typingTimer);
            socket.emit('typing', {
                sender_id: currentUser.id,
                receiver_id: selectedUserId,
                sender_username: currentUser.username
            });
            
            typingTimer = setTimeout(() => {
                // 停止输入状态
            }, 2000);
        }
    }
});

function sendMessage() {
    const content = messageInput.value.trim();
    
    if (!content || !selectedUserId || !socket) return;
    
    socket.emit('send_message', {
        sender_id: currentUser.id,
        receiver_id: selectedUserId,
        content: content
    });
    
    messageInput.value = '';
}

// 显示正在输入提示
let typingTimeout;
function showTypingIndicator(username) {
    const indicator = document.getElementById('typing-indicator');
    indicator.textContent = `${username} 正在输入...`;
    
    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(() => {
        indicator.textContent = '';
    }, 2000);
}

// 检查未读消息
async function checkUnreadMessages() {
    try {
        const response = await fetch('/api/messages/unread-count', {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            const badge = document.getElementById('unread-badge');
            
            if (data.unread_count > 0) {
                badge.textContent = data.unread_count;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('检查未读消息失败:', error);
    }
}

// 导航切换
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const section = item.dataset.section;
        
        // 更新导航状态
        document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
        item.classList.add('active');
        
        // 显示对应区域
        document.querySelectorAll('.section').forEach(sec => sec.style.display = 'none');
        document.getElementById(`${section}-section`).style.display = 'block';
        
        // 如果是用户管理页面，加载用户列表
        if (section === 'users') {
            loadAllUsers();
        }
    });
});

// 渲染个人资料
function renderProfile() {
    const profileInfo = document.getElementById('profile-info');
    profileInfo.innerHTML = `
        <div class="profile-item">
            <span class="profile-label">用户名</span>
            <span class="profile-value">${currentUser.username}</span>
        </div>
        <div class="profile-item">
            <span class="profile-label">邮箱</span>
            <span class="profile-value">${currentUser.email}</span>
        </div>
        <div class="profile-item">
            <span class="profile-label">角色</span>
            <span class="profile-value">${currentUser.role === 'admin' ? '管理员' : '普通用户'}</span>
        </div>
        <div class="profile-item">
            <span class="profile-label">注册时间</span>
            <span class="profile-value">${new Date(currentUser.created_at).toLocaleString()}</span>
        </div>
        <div class="profile-item">
            <span class="profile-label">账号状态</span>
            <span class="profile-value">${currentUser.is_active ? '正常' : '已禁用'}</span>
        </div>
    `;
}

// ==================== 管理员功能 ====================

// 加载所有用户（管理员）
async function loadAllUsers() {
    try {
        const response = await fetch('/api/users', {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        if (response.ok) {
            const users = await response.json();
            renderUsersTable(users);
        } else if (response.status === 403) {
            alert('权限不足');
        }
    } catch (error) {
        console.error('加载用户列表失败:', error);
    }
}

// 渲染用户表格
function renderUsersTable(users) {
    const tbody = document.getElementById('users-table-body');
    tbody.innerHTML = '';
    
    users.forEach(user => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${user.id}</td>
            <td>${user.username}</td>
            <td>${user.email}</td>
            <td class="role-${user.role}">${user.role === 'admin' ? '管理员' : '普通用户'}</td>
            <td class="${user.is_active ? 'status-active' : 'status-inactive'}">
                ${user.is_active ? '正常' : '已禁用'}
            </td>
            <td>${new Date(user.created_at).toLocaleString()}</td>
            <td>
                <button class="btn btn-small btn-secondary" onclick="editUser(${user.id}, '${user.username}', '${user.email}', '${user.role}')">编辑</button>
                <button class="btn btn-small ${user.is_active ? 'btn-danger' : 'btn-success'}" 
                        onclick="toggleUserStatus(${user.id})">
                    ${user.is_active ? '禁用' : '启用'}
                </button>
                <button class="btn btn-small btn-danger" onclick="deleteUser(${user.id})">删除</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// 刷新用户列表
document.getElementById('refresh-users-btn').addEventListener('click', loadAllUsers);

// 编辑用户
function editUser(id, username, email, role) {
    document.getElementById('edit-user-id').value = id;
    document.getElementById('edit-username').value = username;
    document.getElementById('edit-email').value = email;
    document.getElementById('edit-role').value = role;
    document.getElementById('edit-password').value = '';
    
    document.getElementById('edit-user-modal').style.display = 'flex';
}

// 关闭模态框
document.querySelector('.close-btn').addEventListener('click', () => {
    document.getElementById('edit-user-modal').style.display = 'none';
});

// 提交编辑表单
document.getElementById('edit-user-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const userId = document.getElementById('edit-user-id').value;
    const data = {
        username: document.getElementById('edit-username').value,
        email: document.getElementById('edit-email').value,
        role: document.getElementById('edit-role').value
    };
    
    const password = document.getElementById('edit-password').value;
    if (password) {
        data.password = password;
    }
    
    try {
        const response = await fetch(`/api/users/${userId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            document.getElementById('edit-user-modal').style.display = 'none';
            loadAllUsers();
        } else {
            const result = await response.json();
            alert(result.error || '更新失败');
        }
    } catch (error) {
        alert('网络错误');
    }
});

// 切换用户状态
async function toggleUserStatus(userId) {
    if (!confirm('确定要切换该用户的状态吗？')) return;
    
    try {
        const response = await fetch(`/api/users/${userId}/toggle-status`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        if (response.ok) {
            loadAllUsers();
        } else {
            const result = await response.json();
            alert(result.error || '操作失败');
        }
    } catch (error) {
        alert('网络错误');
    }
}

// 删除用户
async function deleteUser(userId) {
    if (!confirm('确定要删除该用户吗？此操作不可恢复！')) return;
    
    try {
        const response = await fetch(`/api/users/${userId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        if (response.ok) {
            loadAllUsers();
        } else {
            const result = await response.json();
            alert(result.error || '删除失败');
        }
    } catch (error) {
        alert('网络错误');
    }
}

// 点击模态框外部关闭
window.addEventListener('click', (e) => {
    const modal = document.getElementById('edit-user-modal');
    if (e.target === modal) {
        modal.style.display = 'none';
    }
});

// 启动应用
init();
