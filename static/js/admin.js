const token = localStorage.getItem('token');
const user = JSON.parse(localStorage.getItem('user') || '{}');

if (!token || user.role !== 'admin') {
    window.location.href = '/login';
}

let editingUserId = null;

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('admin-name').textContent = `管理员: ${user.username}`;
    loadUsers();
    
    document.getElementById('user-form').addEventListener('submit', handleSubmit);
    document.getElementById('cancel-btn').addEventListener('click', resetForm);
});

async function loadUsers() {
    try {
        const response = await fetch('/api/users', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        renderUsers(data.users);
    } catch (error) {
        console.error('加载用户失败:', error);
        alert('加载用户失败');
    }
}

function renderUsers(users) {
    const tbody = document.getElementById('user-table-body');
    tbody.innerHTML = '';
    
    users.forEach(u => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${u.id}</td>
            <td>${u.username}</td>
            <td>${u.email}</td>
            <td>${u.role === 'admin' ? '管理员' : '普通用户'}</td>
            <td>${u.is_active ? '启用' : '禁用'}</td>
            <td>${u.created_at ? new Date(u.created_at).toLocaleString() : '-'}</td>
            <td class="action-buttons">
                <button onclick="editUser(${u.id})">编辑</button>
                <button onclick="deleteUser(${u.id})" class="delete-btn" ${u.id === user.id ? 'disabled' : ''}>删除</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function handleSubmit(e) {
    e.preventDefault();
    
    const userData = {
        username: document.getElementById('username').value,
        email: document.getElementById('email').value,
        password: document.getElementById('password').value || undefined,
        role: document.getElementById('role').value,
        is_active: document.getElementById('is-active').checked
    };

    try {
        let response;
        if (editingUserId) {
            response = await fetch(`/api/users/${editingUserId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(userData)
            });
        } else {
            if (!userData.password) {
                alert('创建用户必须设置密码');
                return;
            }
            response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(userData)
            });
        }

        if (response.ok) {
            resetForm();
            loadUsers();
        } else {
            const data = await response.json();
            alert(data.error || '操作失败');
        }
    } catch (error) {
        console.error('提交失败:', error);
        alert('提交失败');
    }
}

async function editUser(id) {
    try {
        const response = await fetch(`/api/users/${id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        const u = data.user;
        
        if (u) {
            editingUserId = id;
            document.getElementById('user-id').value = id;
            document.getElementById('username').value = u.username;
            document.getElementById('email').value = u.email;
            document.getElementById('password').value = '';
            document.getElementById('role').value = u.role;
            document.getElementById('is-active').checked = u.is_active;
            
            document.getElementById('form-title').textContent = '编辑用户';
            document.getElementById('submit-btn').textContent = '更新';
            document.getElementById('cancel-btn').style.display = 'inline-block';
        }
    } catch (error) {
        console.error('获取用户信息失败:', error);
    }
}

async function deleteUser(id) {
    if (id === user.id) {
        alert('不能删除自己');
        return;
    }
    
    if (!confirm('确定要删除这个用户吗？')) {
        return;
    }

    try {
        const response = await fetch(`/api/users/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            loadUsers();
        } else {
            const data = await response.json();
            alert(data.error || '删除失败');
        }
    } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败');
    }
}

function resetForm() {
    editingUserId = null;
    document.getElementById('user-form').reset();
    document.getElementById('is-active').checked = true;
    document.getElementById('form-title').textContent = '添加用户';
    document.getElementById('submit-btn').textContent = '添加';
    document.getElementById('cancel-btn').style.display = 'none';
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
}
