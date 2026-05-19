const API_BASE_URL = 'http://127.0.0.1:8000';

// Helper function for API calls
async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        }
    };

    // Add token if available
    const token = localStorage.getItem('access_token');
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }

    if (body) {
        options.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        
        if (!response.ok) {
            const error = await response.json();
            console.error('Full error response:', error);
            
            // Handle validation errors (422)
            if (response.status === 422 && error.detail && Array.isArray(error.detail)) {
                const messages = error.detail.map(e => e.msg).join(', ');
                throw new Error(messages);
            }
            
            throw new Error(error.detail || JSON.stringify(error) || 'API Error');
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// SIGNUP
async function signup(userData) {
    try {
        const response = await apiCall('/api/auth/signup', 'POST', {
            full_name: userData.fullName,
            email: userData.email,
            phone_number: userData.phoneNumber,
            password: userData.password,
            confirm_password: userData.confirmPassword
        });
        
        // Store token
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('user', JSON.stringify(response.user));
        
        alert('Signup successful!');
        window.location.href = 'dashboard.html';
    } catch (error) {
        alert('Signup failed: ' + error.message);
    }
}

// LOGIN
async function login(email, password) {
    try {
        const response = await apiCall('/api/auth/login', 'POST', {
            email,
            password
        });
        
        // Store token
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('user', JSON.stringify(response.user));
        
        alert('Login successful!');
        window.location.href = 'dashboard.html';
    } catch (error) {
        alert('Login failed: ' + error.message);
    }
}

// LOGOUT
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = 'signin.html';
}

// GET CURRENT USER
async function getCurrentUser() {
    try {
        return await apiCall('/api/auth/me', 'GET');
    } catch (error) {
        console.error('Failed to get user:', error);
        return null;
    }
}
