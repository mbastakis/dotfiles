# Your First OAuth2 Implementation - From Theory to Practice

## 🎯 Learning Objectives

By the end of this document, you will:
- [ ] Build a complete OAuth2 implementation from scratch
- [ ] Handle the full authorization flow including callbacks
- [ ] Implement proper error handling and edge cases
- [ ] Add token refresh functionality
- [ ] Apply essential security measures
- [ ] Test your implementation thoroughly

**Estimated Time**: 4-5 hours  
**Prerequisites**: [OAuth2 Fundamentals](./01-oauth2-fundamentals.md), [Basic Flows](./02-basic-flows.md)

---

## 🏗️ What We're Building

We'll create a complete OAuth2 client that:
- Uses Authorization Code + PKCE flow
- Handles user login and logout
- Manages token lifecycle (refresh, expiration)
- Implements proper security measures
- Provides a clean user experience

### Project Structure
```
oauth2-demo/
├── index.html          # Main application page
├── js/
│   ├── oauth2-client.js # OAuth2 implementation
│   ├── token-manager.js # Token lifecycle management
│   └── api-client.js    # API calls with tokens
├── css/
│   └── styles.css       # Basic styling
└── config.js           # Configuration
```

---

## ⚙️ Configuration Setup

First, let's set up our OAuth2 configuration:

### config.js
```javascript
// OAuth2 Configuration
const OAUTH2_CONFIG = {
  // Replace with your OAuth2 provider details
  authServerUrl: 'https://your-auth-server.com',
  clientId: 'your-client-id',
  redirectUri: window.location.origin + '/callback',
  scope: 'openid profile email',
  
  // Endpoints
  endpoints: {
    authorization: '/authorize',
    token: '/token',
    userinfo: '/userinfo',
    revocation: '/revoke'
  },
  
  // Token settings
  tokenSettings: {
    storageKey: 'oauth2_tokens',
    refreshThreshold: 300 // Refresh 5 minutes before expiry
  }
};

// API Configuration
const API_CONFIG = {
  baseUrl: 'https://your-api.com',
  endpoints: {
    profile: '/api/profile',
    data: '/api/data'
  }
};
```

---

## 🔐 OAuth2 Client Implementation

### oauth2-client.js
```javascript
class OAuth2Client {
  constructor(config) {
    this.config = config;
    this.tokenManager = new TokenManager(config.tokenSettings);
  }

  // Generate PKCE parameters
  generatePKCE() {
    const codeVerifier = this._generateCodeVerifier();
    const codeChallenge = this._generateCodeChallenge(codeVerifier);
    return { codeVerifier, codeChallenge };
  }

  _generateCodeVerifier() {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return this._base64URLEncode(array);
  }

  async _generateCodeChallenge(verifier) {
    const encoder = new TextEncoder();
    const data = encoder.encode(verifier);
    const digest = await crypto.subtle.digest('SHA-256', data);
    return this._base64URLEncode(new Uint8Array(digest));
  }

  _base64URLEncode(buffer) {
    return btoa(String.fromCharCode(...buffer))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  }

  _generateState() {
    const array = new Uint8Array(16);
    crypto.getRandomValues(array);
    return this._base64URLEncode(array);
  }

  // Start OAuth2 authorization flow
  async authorize() {
    try {
      const { codeVerifier, codeChallenge } = this.generatePKCE();
      const state = this._generateState();

      // Store PKCE parameters and state
      sessionStorage.setItem('code_verifier', codeVerifier);
      sessionStorage.setItem('oauth_state', state);
      sessionStorage.setItem('auth_start_time', Date.now().toString());

      // Build authorization URL
      const authUrl = new URL(
        this.config.authServerUrl + this.config.endpoints.authorization
      );
      
      authUrl.searchParams.set('response_type', 'code');
      authUrl.searchParams.set('client_id', this.config.clientId);
      authUrl.searchParams.set('redirect_uri', this.config.redirectUri);
      authUrl.searchParams.set('scope', this.config.scope);
      authUrl.searchParams.set('code_challenge', codeChallenge);
      authUrl.searchParams.set('code_challenge_method', 'S256');
      authUrl.searchParams.set('state', state);

      console.log('Redirecting to authorization server...');
      window.location.href = authUrl.toString();

    } catch (error) {
      console.error('Authorization failed:', error);
      throw new Error('Failed to start authorization: ' + error.message);
    }
  }

  // Handle authorization callback
  async handleCallback() {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');
      const error = urlParams.get('error');
      const errorDescription = urlParams.get('error_description');

      // Check for authorization errors
      if (error) {
        throw new Error(`Authorization failed: ${error} - ${errorDescription || 'Unknown error'}`);
      }

      if (!code) {
        throw new Error('No authorization code received');
      }

      // Verify state parameter (CSRF protection)
      const storedState = sessionStorage.getItem('oauth_state');
      if (!state || state !== storedState) {
        throw new Error('Invalid state parameter - possible CSRF attack');
      }

      // Check if authorization took too long
      const authStartTime = sessionStorage.getItem('auth_start_time');
      if (authStartTime && Date.now() - parseInt(authStartTime) > 600000) { // 10 minutes
        throw new Error('Authorization took too long - please try again');
      }

      const codeVerifier = sessionStorage.getItem('code_verifier');
      if (!codeVerifier) {
        throw new Error('Code verifier not found - please restart authorization');
      }

      // Exchange authorization code for tokens
      const tokens = await this._exchangeCodeForTokens(code, codeVerifier);
      
      // Store tokens
      this.tokenManager.setTokens(tokens);

      // Clean up session storage
      this._cleanupSessionStorage();

      // Clear URL parameters
      window.history.replaceState({}, document.title, window.location.pathname);

      console.log('Authorization successful');
      return tokens;

    } catch (error) {
      this._cleanupSessionStorage();
      console.error('Callback handling failed:', error);
      throw error;
    }
  }

  // Exchange authorization code for tokens
  async _exchangeCodeForTokens(code, codeVerifier) {
    const tokenUrl = this.config.authServerUrl + this.config.endpoints.token;
    
    const response = await fetch(tokenUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
      },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        code: code,
        client_id: this.config.clientId,
        code_verifier: codeVerifier,
        redirect_uri: this.config.redirectUri
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        `Token exchange failed: ${response.status} - ${errorData.error || 'Unknown error'}`
      );
    }

    const tokens = await response.json();
    
    // Validate token response
    if (!tokens.access_token) {
      throw new Error('No access token received');
    }

    return tokens;
  }

  // Refresh access token
  async refreshToken() {
    const refreshToken = this.tokenManager.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const tokenUrl = this.config.authServerUrl + this.config.endpoints.token;
    
    const response = await fetch(tokenUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
      },
      body: new URLSearchParams({
        grant_type: 'refresh_token',
        refresh_token: refreshToken,
        client_id: this.config.clientId
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      
      if (response.status === 400 || response.status === 401) {
        // Refresh token is invalid - user needs to re-authenticate
        this.tokenManager.clearTokens();
        throw new Error('REFRESH_TOKEN_INVALID');
      }
      
      throw new Error(
        `Token refresh failed: ${response.status} - ${errorData.error || 'Unknown error'}`
      );
    }

    const tokens = await response.json();
    this.tokenManager.setTokens(tokens);
    
    return tokens;
  }

  // Logout user
  async logout() {
    try {
      const refreshToken = this.tokenManager.getRefreshToken();
      
      // Revoke tokens if revocation endpoint is available
      if (refreshToken && this.config.endpoints.revocation) {
        await this._revokeToken(refreshToken);
      }
    } catch (error) {
      console.warn('Token revocation failed:', error);
    } finally {
      // Always clear local tokens
      this.tokenManager.clearTokens();
      this._cleanupSessionStorage();
    }
  }

  // Revoke token
  async _revokeToken(token) {
    const revokeUrl = this.config.authServerUrl + this.config.endpoints.revocation;
    
    await fetch(revokeUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams({
        token: token,
        client_id: this.config.clientId
      })
    });
  }

  // Get current access token (with automatic refresh)
  async getAccessToken() {
    let accessToken = this.tokenManager.getAccessToken();
    
    if (!accessToken) {
      return null; // User not authenticated
    }

    // Check if token needs refresh
    if (this.tokenManager.needsRefresh()) {
      try {
        const tokens = await this.refreshToken();
        accessToken = tokens.access_token;
      } catch (error) {
        if (error.message === 'REFRESH_TOKEN_INVALID') {
          return null; // User needs to re-authenticate
        }
        throw error;
      }
    }

    return accessToken;
  }

  // Check if user is authenticated
  isAuthenticated() {
    return this.tokenManager.hasValidTokens();
  }

  // Clean up session storage
  _cleanupSessionStorage() {
    sessionStorage.removeItem('code_verifier');
    sessionStorage.removeItem('oauth_state');
    sessionStorage.removeItem('auth_start_time');
  }
}
```

---

## 🎫 Token Manager Implementation

### token-manager.js
```javascript
class TokenManager {
  constructor(config) {
    this.config = config;
    this.tokens = this._loadTokens();
    this._setupAutoRefresh();
  }

  // Set new tokens
  setTokens(tokens) {
    this.tokens = {
      access_token: tokens.access_token,
      refresh_token: tokens.refresh_token,
      expires_in: tokens.expires_in,
      token_type: tokens.token_type || 'Bearer',
      scope: tokens.scope,
      expires_at: Date.now() + (tokens.expires_in * 1000)
    };

    this._saveTokens();
    this._setupAutoRefresh();
  }

  // Get access token
  getAccessToken() {
    return this.tokens?.access_token || null;
  }

  // Get refresh token
  getRefreshToken() {
    return this.tokens?.refresh_token || null;
  }

  // Check if tokens exist and are valid
  hasValidTokens() {
    return !!(this.tokens?.access_token && !this.isExpired());
  }

  // Check if access token is expired
  isExpired() {
    if (!this.tokens?.expires_at) {
      return true;
    }
    return Date.now() >= this.tokens.expires_at;
  }

  // Check if token needs refresh (before expiration)
  needsRefresh() {
    if (!this.tokens?.expires_at) {
      return false;
    }
    
    const refreshThreshold = this.config.refreshThreshold * 1000; // Convert to ms
    return Date.now() >= (this.tokens.expires_at - refreshThreshold);
  }

  // Clear all tokens
  clearTokens() {
    this.tokens = null;
    this._clearStoredTokens();
    this._clearAutoRefresh();
  }

  // Get time until token expires (in seconds)
  getTimeUntilExpiry() {
    if (!this.tokens?.expires_at) {
      return 0;
    }
    return Math.max(0, Math.floor((this.tokens.expires_at - Date.now()) / 1000));
  }

  // Load tokens from storage
  _loadTokens() {
    try {
      const stored = sessionStorage.getItem(this.config.storageKey);
      if (stored) {
        const tokens = JSON.parse(stored);
        
        // Check if tokens are expired
        if (tokens.expires_at && Date.now() >= tokens.expires_at) {
          this._clearStoredTokens();
          return null;
        }
        
        return tokens;
      }
    } catch (error) {
      console.warn('Failed to load tokens from storage:', error);
      this._clearStoredTokens();
    }
    return null;
  }

  // Save tokens to storage
  _saveTokens() {
    try {
      sessionStorage.setItem(this.config.storageKey, JSON.stringify(this.tokens));
    } catch (error) {
      console.error('Failed to save tokens to storage:', error);
    }
  }

  // Clear tokens from storage
  _clearStoredTokens() {
    try {
      sessionStorage.removeItem(this.config.storageKey);
    } catch (error) {
      console.warn('Failed to clear tokens from storage:', error);
    }
  }

  // Setup automatic token refresh
  _setupAutoRefresh() {
    this._clearAutoRefresh();
    
    if (!this.tokens?.expires_at) {
      return;
    }

    const refreshThreshold = this.config.refreshThreshold * 1000;
    const timeUntilRefresh = this.tokens.expires_at - Date.now() - refreshThreshold;

    if (timeUntilRefresh > 0) {
      this.refreshTimer = setTimeout(() => {
        this._triggerRefresh();
      }, timeUntilRefresh);
    }
  }

  // Clear automatic refresh timer
  _clearAutoRefresh() {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  // Trigger token refresh (override this method)
  _triggerRefresh() {
    // This should be overridden by the OAuth2Client
    console.log('Token refresh needed');
  }
}
```

---

## 🌐 API Client Implementation

### api-client.js
```javascript
class APIClient {
  constructor(oauth2Client, apiConfig) {
    this.oauth2Client = oauth2Client;
    this.apiConfig = apiConfig;
  }

  // Make authenticated API request
  async request(endpoint, options = {}) {
    const accessToken = await this.oauth2Client.getAccessToken();
    
    if (!accessToken) {
      throw new Error('USER_NOT_AUTHENTICATED');
    }

    const url = this.apiConfig.baseUrl + endpoint;
    const requestOptions = {
      ...options,
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    };

    try {
      const response = await fetch(url, requestOptions);
      
      if (response.status === 401) {
        // Token might be expired, try refresh
        const newToken = await this.oauth2Client.getAccessToken();
        if (newToken && newToken !== accessToken) {
          // Retry with new token
          requestOptions.headers['Authorization'] = `Bearer ${newToken}`;
          return await fetch(url, requestOptions);
        } else {
          throw new Error('AUTHENTICATION_FAILED');
        }
      }

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else {
        return await response.text();
      }

    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Convenience methods
  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }

  // Get user profile
  async getUserProfile() {
    return this.get(this.apiConfig.endpoints.profile);
  }

  // Get user data
  async getUserData() {
    return this.get(this.apiConfig.endpoints.data);
  }
}
```

---

## 🎨 User Interface

### index.html
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OAuth2 Demo Application</title>
    <link rel="stylesheet" href="css/styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>OAuth2 Demo Application</h1>
            <div id="auth-status" class="auth-status"></div>
        </header>

        <main>
            <!-- Login Section -->
            <section id="login-section" class="section hidden">
                <h2>Welcome</h2>
                <p>Please log in to access your data.</p>
                <button id="login-btn" class="btn btn-primary">Login with OAuth2</button>
            </section>

            <!-- Loading Section -->
            <section id="loading-section" class="section hidden">
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Processing authentication...</p>
                </div>
            </section>

            <!-- Dashboard Section -->
            <section id="dashboard-section" class="section hidden">
                <h2>Dashboard</h2>
                
                <div class="user-info">
                    <h3>User Information</h3>
                    <div id="user-profile" class="profile-card">
                        <!-- User profile will be loaded here -->
                    </div>
                </div>

                <div class="token-info">
                    <h3>Token Information</h3>
                    <div id="token-status" class="token-status">
                        <!-- Token status will be displayed here -->
                    </div>
                </div>

                <div class="actions">
                    <button id="refresh-data-btn" class="btn btn-secondary">Refresh Data</button>
                    <button id="logout-btn" class="btn btn-danger">Logout</button>
                </div>
            </section>

            <!-- Error Section -->
            <section id="error-section" class="section hidden">
                <h2>Error</h2>
                <div id="error-message" class="error-message"></div>
                <button id="retry-btn" class="btn btn-primary">Try Again</button>
            </section>
        </main>
    </div>

    <!-- Scripts -->
    <script src="config.js"></script>
    <script src="js/token-manager.js"></script>
    <script src="js/oauth2-client.js"></script>
    <script src="js/api-client.js"></script>
    <script src="js/app.js"></script>
</body>
</html>
```

### css/styles.css
```css
/* Basic styling for the OAuth2 demo */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f5f5f5;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}

header {
    text-align: center;
    margin-bottom: 40px;
    padding: 20px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.auth-status {
    margin-top: 10px;
    padding: 8px 16px;
    border-radius: 4px;
    font-size: 14px;
}

.auth-status.authenticated {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.auth-status.unauthenticated {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.section {
    background: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

.hidden {
    display: none;
}

.btn {
    padding: 12px 24px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    transition: background-color 0.2s;
    text-decoration: none;
    display: inline-block;
}

.btn-primary {
    background-color: #007bff;
    color: white;
}

.btn-primary:hover {
    background-color: #0056b3;
}

.btn-secondary {
    background-color: #6c757d;
    color: white;
}

.btn-secondary:hover {
    background-color: #545b62;
}

.btn-danger {
    background-color: #dc3545;
    color: white;
}

.btn-danger:hover {
    background-color: #c82333;
}

.loading {
    text-align: center;
    padding: 40px;
}

.spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #007bff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 20px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.profile-card {
    background-color: #f8f9fa;
    padding: 20px;
    border-radius: 4px;
    margin: 10px 0;
}

.token-status {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 4px;
    font-family: monospace;
    font-size: 14px;
}

.error-message {
    background-color: #f8d7da;
    color: #721c24;
    padding: 15px;
    border-radius: 4px;
    border: 1px solid #f5c6cb;
    margin-bottom: 20px;
}

.actions {
    margin-top: 30px;
}

.actions .btn {
    margin-right: 10px;
    margin-bottom: 10px;
}

@media (max-width: 600px) {
    .container {
        padding: 10px;
    }
    
    .section {
        padding: 20px;
    }
    
    .actions .btn {
        display: block;
        width: 100%;
        margin-right: 0;
    }
}
```

---

## 🎮 Application Logic

### js/app.js
```javascript
class OAuth2DemoApp {
  constructor() {
    this.oauth2Client = new OAuth2Client(OAUTH2_CONFIG);
    this.apiClient = new APIClient(this.oauth2Client, API_CONFIG);
    this.init();
  }

  init() {
    this.bindEvents();
    this.checkAuthenticationStatus();
    this.handleCallback();
  }

  bindEvents() {
    document.getElementById('login-btn').addEventListener('click', () => this.login());
    document.getElementById('logout-btn').addEventListener('click', () => this.logout());
    document.getElementById('refresh-data-btn').addEventListener('click', () => this.refreshData());
    document.getElementById('retry-btn').addEventListener('click', () => this.retry());
  }

  async checkAuthenticationStatus() {
    if (this.oauth2Client.isAuthenticated()) {
      await this.showDashboard();
    } else {
      this.showLogin();
    }
  }

  async handleCallback() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('code') || urlParams.has('error')) {
      this.showLoading();
      
      try {
        await this.oauth2Client.handleCallback();
        await this.showDashboard();
      } catch (error) {
        this.showError('Authentication failed: ' + error.message);
      }
    }
  }

  async login() {
    try {
      this.showLoading();
      await this.oauth2Client.authorize();
    } catch (error) {
      this.showError('Login failed: ' + error.message);
    }
  }

  async logout() {
    try {
      await this.oauth2Client.logout();
      this.showLogin();
    } catch (error) {
      console.error('Logout error:', error);
      // Still show login even if logout failed
      this.showLogin();
    }
  }

  async refreshData() {
    try {
      const refreshBtn = document.getElementById('refresh-data-btn');
      refreshBtn.disabled = true;
      refreshBtn.textContent = 'Refreshing...';

      await this.loadUserData();
      this.updateTokenStatus();

      refreshBtn.disabled = false;
      refreshBtn.textContent = 'Refresh Data';
    } catch (error) {
      this.showError('Failed to refresh data: ' + error.message);
    }
  }

  retry() {
    this.checkAuthenticationStatus();
  }

  async showDashboard() {
    try {
      this.hideAllSections();
      this.showLoading();

      await this.loadUserData();
      this.updateTokenStatus();
      this.updateAuthStatus(true);

      document.getElementById('dashboard-section').classList.remove('hidden');
    } catch (error) {
      if (error.message === 'USER_NOT_AUTHENTICATED' || 
          error.message === 'AUTHENTICATION_FAILED') {
        this.showLogin();
      } else {
        this.showError('Failed to load dashboard: ' + error.message);
      }
    }
  }

  async loadUserData() {
    try {
      const profile = await this.apiClient.getUserProfile();
      this.displayUserProfile(profile);
    } catch (error) {
      console.error('Failed to load user profile:', error);
      document.getElementById('user-profile').innerHTML = 
        '<p class="error">Failed to load user profile</p>';
    }
  }

  displayUserProfile(profile) {
    const profileElement = document.getElementById('user-profile');
    profileElement.innerHTML = `
      <h4>${profile.name || 'Unknown User'}</h4>
      <p><strong>Email:</strong> ${profile.email || 'Not provided'}</p>
      <p><strong>ID:</strong> ${profile.sub || profile.id || 'Unknown'}</p>
      <p><strong>Last Updated:</strong> ${new Date().toLocaleString()}</p>
    `;
  }

  updateTokenStatus() {
    const tokenManager = this.oauth2Client.tokenManager;
    const statusElement = document.getElementById('token-status');
    
    if (tokenManager.hasValidTokens()) {
      const timeUntilExpiry = tokenManager.getTimeUntilExpiry();
      const expiryTime = new Date(Date.now() + (timeUntilExpiry * 1000));
      
      statusElement.innerHTML = `
        <p><strong>Status:</strong> Valid</p>
        <p><strong>Expires in:</strong> ${Math.floor(timeUntilExpiry / 60)} minutes</p>
        <p><strong>Expires at:</strong> ${expiryTime.toLocaleString()}</p>
        <p><strong>Needs refresh:</strong> ${tokenManager.needsRefresh() ? 'Yes' : 'No'}</p>
      `;
    } else {
      statusElement.innerHTML = '<p><strong>Status:</strong> No valid tokens</p>';
    }
  }

  showLogin() {
    this.hideAllSections();
    this.updateAuthStatus(false);
    document.getElementById('login-section').classList.remove('hidden');
  }

  showLoading() {
    this.hideAllSections();
    document.getElementById('loading-section').classList.remove('hidden');
  }

  showError(message) {
    this.hideAllSections();
    document.getElementById('error-message').textContent = message;
    document.getElementById('error-section').classList.remove('hidden');
  }

  hideAllSections() {
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => section.classList.add('hidden'));
  }

  updateAuthStatus(isAuthenticated) {
    const statusElement = document.getElementById('auth-status');
    if (isAuthenticated) {
      statusElement.textContent = 'Authenticated';
      statusElement.className = 'auth-status authenticated';
    } else {
      statusElement.textContent = 'Not Authenticated';
      statusElement.className = 'auth-status unauthenticated';
    }
  }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new OAuth2DemoApp();
});
```

---

## 🧪 Testing Your Implementation

### Manual Testing Checklist

#### Basic Flow Testing
- [ ] **Login Flow**: Click login button, complete authorization, return to app
- [ ] **Token Storage**: Refresh page, verify user stays logged in
- [ ] **API Calls**: Verify authenticated API requests work
- [ ] **Logout**: Click logout, verify tokens are cleared

#### Error Handling Testing
- [ ] **Invalid State**: Manually modify state parameter in callback URL
- [ ] **Expired Code**: Wait 10+ minutes before completing authorization
- [ ] **Network Errors**: Disconnect internet during token exchange
- [ ] **Invalid Tokens**: Manually corrupt stored tokens

#### Security Testing
- [ ] **CSRF Protection**: Verify state parameter is validated
- [ ] **PKCE Validation**: Verify code_verifier is required
- [ ] **Token Expiration**: Wait for token to expire, verify refresh works
- [ ] **Secure Storage**: Verify tokens are not in localStorage

### Automated Testing Example

```javascript
// Simple test suite for OAuth2 implementation
class OAuth2Tests {
  constructor() {
    this.oauth2Client = new OAuth2Client(OAUTH2_CONFIG);
  }

  async runTests() {
    console.log('Running OAuth2 tests...');
    
    try {
      await this.testPKCEGeneration();
      await this.testStateGeneration();
      await this.testTokenManager();
      console.log('✅ All tests passed!');
    } catch (error) {
      console.error('❌ Test failed:', error);
    }
  }

  async testPKCEGeneration() {
    const { codeVerifier, codeChallenge } = this.oauth2Client.generatePKCE();
    
    // Test code verifier length and format
    if (codeVerifier.length < 43 || codeVerifier.length > 128) {
      throw new Error('Code verifier length invalid');
    }
    
    // Test code challenge is different from verifier
    if (codeChallenge === codeVerifier) {
      throw new Error('Code challenge should be different from verifier');
    }
    
    console.log('✅ PKCE generation test passed');
  }

  async testStateGeneration() {
    const state1 = this.oauth2Client._generateState();
    const state2 = this.oauth2Client._generateState();
    
    // Test uniqueness
    if (state1 === state2) {
      throw new Error('State values should be unique');
    }
    
    // Test length
    if (state1.length < 16) {
      throw new Error('State should be at least 16 characters');
    }
    
    console.log('✅ State generation test passed');
  }

  async testTokenManager() {
    const tokenManager = new TokenManager(OAUTH2_CONFIG.tokenSettings);
    
    // Test initial state
    if (tokenManager.hasValidTokens()) {
      throw new Error('Should not have valid tokens initially');
    }
    
    // Test token setting
    const mockTokens = {
      access_token: 'test_access_token',
      refresh_token: 'test_refresh_token',
      expires_in: 3600
    };
    
    tokenManager.setTokens(mockTokens);
    
    if (!tokenManager.hasValidTokens()) {
      throw new Error('Should have valid tokens after setting');
    }
    
    if (tokenManager.getAccessToken() !== 'test_access_token') {
      throw new Error('Access token not stored correctly');
    }
    
    console.log('✅ Token manager test passed');
  }
}

// Run tests in development
if (window.location.hostname === 'localhost') {
  const tests = new OAuth2Tests();
  tests.runTests();
}
```

---

## 🔒 Security Considerations

### Essential Security Measures

1. **HTTPS Everywhere**
   ```javascript
   // Ensure all OAuth2 URLs use HTTPS
   if (!this.config.authServerUrl.startsWith('https://')) {
     throw new Error('Authorization server must use HTTPS');
   }
   ```

2. **State Parameter Validation**
   ```javascript
   // Always validate state parameter
   if (state !== storedState) {
     throw new Error('Invalid state parameter - possible CSRF attack');
   }
   ```

3. **Secure Token Storage**
   ```javascript
   // Use sessionStorage, not localStorage
   sessionStorage.setItem('oauth2_tokens', JSON.stringify(tokens));
   ```

4. **Token Expiration Handling**
   ```javascript
   // Check token expiration before use
   if (this.tokenManager.isExpired()) {
     await this.refreshToken();
   }
   ```

### Common Security Mistakes to Avoid

❌ **Don't store tokens in localStorage**
```javascript
// VULNERABLE - XSS can steal tokens
localStorage.setItem('access_token', token);
```

❌ **Don't skip state parameter validation**
```javascript
// VULNERABLE - CSRF attacks possible
const code = urlParams.get('code');
// Missing state validation
```

❌ **Don't ignore token expiration**
```javascript
// VULNERABLE - Using expired tokens
const token = this.getStoredToken();
// Missing expiration check
```

---

## 🎯 Knowledge Check

Before moving to intermediate topics, ensure you can:

- [ ] Build a complete OAuth2 implementation from scratch
- [ ] Handle all aspects of the authorization flow
- [ ] Implement proper error handling for edge cases
- [ ] Manage token lifecycle including refresh
- [ ] Apply essential security measures
- [ ] Test your implementation thoroughly

### Practical Exercise

**Challenge**: Modify the implementation to:
1. Add automatic token refresh in the background
2. Implement proper loading states for all operations
3. Add retry logic for failed API requests
4. Store user preferences across sessions (without storing tokens)

### Self-Assessment Questions

1. **What happens if the authorization code expires before token exchange?**
2. **How does PKCE protect against authorization code interception?**
3. **Why should tokens be stored in sessionStorage instead of localStorage?**
4. **What should happen if a refresh token becomes invalid?**

<details>
<summary>Click for answers</summary>

1. **Expired authorization code**: The token exchange will fail with an `invalid_grant` error, and the user needs to restart the authorization flow.

2. **PKCE protection**: Even if an attacker intercepts the authorization code, they can't exchange it for tokens without the `code_verifier`, which is stored securely in the client.

3. **sessionStorage vs localStorage**: sessionStorage is cleared when the tab closes and isn't shared across tabs, reducing the attack surface for XSS attacks.

4. **Invalid refresh token**: Clear all stored tokens and redirect the user to login again, as they need to re-authenticate.

</details>

---

## 🚀 What's Next?

Congratulations! You've built a complete OAuth2 implementation. You're now ready for:

**Next Level**: [Modern Security Patterns](../02-intermediate/01-modern-security-patterns.md)
- Advanced PKCE configurations
- RFC 9700 security best practices
- Token binding and advanced security features

**Practical Guides**:
- [JavaScript SPA Guide](../04-implementation-guides/javascript-spa-guide.md) - Production-ready SPA implementation
- [Security Checklist](../05-security/security-checklist.md) - Validate your implementation

---

## 📚 Additional Resources

### Testing Tools
- [OAuth2 Debugger](https://oauthdebugger.com/) - Test OAuth2 flows
- [Postman OAuth2](https://learning.postman.com/docs/sending-requests/authorization/#oauth-20) - API testing

### Security Resources
- [OAuth2 Security Best Practices](https://tools.ietf.org/html/draft-ietf-oauth-security-topics)
- [OWASP OAuth2 Security](https://owasp.org/www-community/vulnerabilities/OAuth2_Common_Vulnerabilities)

---

*You've now built a solid foundation in OAuth2 implementation. The patterns and security measures you've learned here will serve you well as you tackle more advanced OAuth2 scenarios.*