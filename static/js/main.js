const API_URL = '/api/users';
let editingUserId = null;

document.addEventListener('DOMContentLoaded', () => {
    loadUsers();
    
    document.getElementById('user-form').addEventListener('submit', handleSubmit);
    document.getElementById('cancel-btn').addEventListener('click', resetForm);
});

async function loadUsers() {
    try {
        const response = await fetch(API_URL);
        const users = await response.json();
        renderUsers(users);
    } catch (error) {
        console.error('加载用户失败:', error);
        alert('加载用户失败');
    }
}

function renderUsers(users) {
    const tbody = document.getElementById('user-table-body');
    tbody.innerHTML = '';
    
    users.forEach(user => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${user.id}</td>
            <td>${user.name}</td>
            <td>${user.email}</td>
            <td>${user.age}</td>
            <td class="action-buttons">
                <button onclick="editUser(${user.id})">编辑</button>
                <button onclick="deleteUser(${user.id})" class="delete-btn">删除</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function handleSubmit(e) {
    e.preventDefault();
    
    const userData = {
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        age: parseInt(document.getElementById('age').value)
    };

    try {
        let response;
        if (editingUserId) {
            response = await fetch(`${API_URL}/${editingUserId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(userData)
            });
        } else {
            response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(userData)
            });
        }

        if (response.ok) {
            resetForm();
            loadUsers();
        } else {
            alert('操作失败');
        }
    } catch (error) {
        console.error('提交失败:', error);
        alert('提交失败');
    }
}

async function editUser(id) {
    try {
        const response = await fetch(API_URL);
        const userList = await response.json();
        const user = userList.find(u => u.id === id);
        
        if (user) {
            editingUserId = id;
            document.getElementById('user-id').value = id;
            document.getElementById('name').value = user.name;
            document.getElementById('email').value = user.email;
            document.getElementById('age').value = user.age;
            
            document.getElementById('form-title').textContent = '编辑用户';
            document.getElementById('submit-btn').textContent = '更新';
            document.getElementById('cancel-btn').style.display = 'inline-block';
        }
    } catch (error) {
        console.error('获取用户信息失败:', error);
    }
}

async function deleteUser(id) {
    if (!confirm('确定要删除这个用户吗？')) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            loadUsers();
        } else {
            alert('删除失败');
        }
    } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败');
    }
}

function resetForm() {
    editingUserId = null;
    document.getElementById('user-form').reset();
    document.getElementById('form-title').textContent = '添加用户';
    document.getElementById('submit-btn').textContent = '添加';
    document.getElementById('cancel-btn').style.display = 'none';
}
