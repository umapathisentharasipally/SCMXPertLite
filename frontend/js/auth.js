const API_BASE_URL = 'http://127.0.0.1:8000';

function setFormError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
        element.style.display = 'block';
    }
}

function clearFormError(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = '';
        element.style.display = 'none';
    }
}

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

            let message = 'API Error';

            if (response.status === 422 && error.detail && Array.isArray(error.detail)) {
                message = error.detail
                    .map(e => e.msg || e.message || JSON.stringify(e))
                    .join(', ');
            } else if (typeof error.detail === 'string') {
                message = error.detail;
            } else if (typeof error.error === 'string') {
                message = error.error;
            } else if (typeof error.message === 'string') {
                message = error.message;
            } else if (typeof error === 'string') {
                message = error;
            } else {
                message = JSON.stringify(error);
            }

            throw new Error(message || 'API Error');
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
        setFormError('signupError', 'Signup failed: ' + (error.message || 'Unknown error'));
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
        setFormError('signinError', 'Login failed: ' + (error.message || 'Unknown error'));
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
