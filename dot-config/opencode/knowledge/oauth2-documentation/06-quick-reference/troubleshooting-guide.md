# OAuth2 Troubleshooting Guide - Common Issues and Solutions

## 🎯 Quick Diagnosis

### Symptom-Based Troubleshooting

| Symptom | Most Likely Cause | Quick Fix |
|---------|-------------------|-----------|
| "Invalid redirect URI" | URI mismatch | Check exact string matching |
| "Invalid grant" | Code expired/used | Generate new auth request |
| "Access denied" | User rejected | Handle gracefully, retry |
| "Invalid client" | Wrong credentials | Verify client ID/secret |
| Infinite redirect loops | State/PKCE issues | Check parameter validation |
| Tokens not working | Expired/invalid | Implement token refresh |

---

## 🔍 Authorization Flow Issues

### Issue: "Invalid Redirect URI"

**Symptoms:**
- Error during authorization redirect
- User sees error page instead of your app
- Authorization server rejects the request

**Common Causes:**
```javascript
// ❌ Common mistakes
const redirectUri = 'https://myapp.com/callback/'; // Extra slash
const redirectUri = 'http://myapp.com/callback';   // HTTP instead of HTTPS
const redirectUri = 'https://myapp.com/*';         // Wildcard not allowed
```

**Solutions:**
```javascript
// ✅ Correct patterns
const redirectUri = 'https://myapp.com/callback';  // Exact match required

// Validation function
function validateRedirectURI(configured, requested) {
  if (configured !== requested) {
    throw new Error(`Redirect URI mismatch: expected '${configured}', got '${requested}'`);
  }
  return true;
}

// Debug helper
function debugRedirectURI() {
  console.log('Configured:', REDIRECT_URI);
  console.log('Current URL:', window.location.origin + window.location.pathname);
  console.log('Match:', REDIRECT_URI === window.location.origin + window.location.pathname);
}
```

### Issue: "Invalid Grant" Error

**Symptoms:**
- Token exchange fails with 400 error
- "authorization_code is invalid" message
- User completes auth but app shows error

**Common Causes:**
1. Authorization code expired (>10 minutes)
2. Code already used (replay attack protection)
3. Wrong client credentials
4. PKCE verification failed

**Debugging Steps:**
```javascript
async function debugTokenExchange(code, codeVerifier) {
  console.log('Debug Token Exchange:');
  console.log('- Code:', code?.substring(0, 10) + '...');
  console.log('- Code Verifier:', codeVerifier?.substring(0, 10) + '...');
  console.log('- Client ID:', CLIENT_ID);
  console.log('- Redirect URI:', REDIRECT_URI);
  
  // Check timing
  const authStartTime = sessionStorage.getItem('auth_start_time');
  if (authStartTime) {
    const elapsed = Date.now() - parseInt(authStartTime);
    console.log('- Time elapsed:', Math.floor(elapsed / 1000), 'seconds');
    
    if (elapsed > 600000) { // 10 minutes
      console.error('❌ Authorization code likely expired');
    }
  }
  
  // Validate PKCE
  if (!codeVerifier) {
    console.error('❌ Missing code verifier');
  }
  
  try {
    const response = await fetch(`${AUTH_SERVER}/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        code: code,
        client_id: CLIENT_ID,
        code_verifier: codeVerifier,
        redirect_uri: REDIRECT_URI
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      console.error('Token exchange failed:', errorData);
      return null;
    }
    
    return await response.json();
  } catch (error) {
    console.error('Network error:', error);
    return null;
  }
}
```

### Issue: Infinite Redirect Loops

**Symptoms:**
- Browser keeps redirecting between app and auth server
- URL keeps changing but never completes
- Browser eventually shows "too many redirects" error

**Common Causes:**
```javascript
// ❌ Missing callback handling
window.addEventListener('load', () => {
  // Missing: check for authorization callback
  startOAuth2Flow(); // This causes infinite loop
});

// ❌ Incorrect state validation
function handleCallback() {
  const urlParams = new URLSearchParams(window.location.search);
  const state = urlParams.get('state');
  
  // Missing or incorrect state validation
  if (!state) {
    startOAuth2Flow(); // Causes loop
  }
}
```

**Solutions:**
```javascript
// ✅ Proper callback detection
window.addEventListener('load', () => {
  const urlParams = new URLSearchParams(window.location.search);
  
  if (urlParams.has('code') || urlParams.has('error')) {
    // This is a callback - handle it
    handleOAuth2Callback();
  } else if (!isAuthenticated()) {
    // Not authenticated and not a callback - start flow
    startOAuth2Flow();
  } else {
    // Already authenticated - show app
    showApplication();
  }
});

// ✅ Robust callback handling
async function handleOAuth2Callback() {
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    const error = urlParams.get('error');
    
    if (error) {
      throw new Error(`Authorization failed: ${error}`);
    }
    
    if (!code) {
      throw new Error('No authorization code received');
    }
    
    // Validate state
    const storedState = sessionStorage.getItem('oauth_state');
    if (!state || state !== storedState) {
      throw new Error('Invalid state parameter');
    }
    
    // Exchange code for tokens
    const tokens = await exchangeCodeForTokens(code);
    
    // Clear URL parameters
    window.history.replaceState({}, document.title, window.location.pathname);
    
    // Show authenticated app
    showApplication();
    
  } catch (error) {
    console.error('Callback handling failed:', error);
    showError(error.message);
  }
}
```

---

## 🎫 Token Management Issues

### Issue: "Token Expired" Errors

**Symptoms:**
- API calls return 401 Unauthorized
- User suddenly logged out
- "Token has expired" messages

**Debugging:**
```javascript
class TokenDebugger {
  static analyzeToken(token) {
    if (!token) {
      console.error('❌ No token provided');
      return;
    }
    
    // Check if JWT
    if (token.includes('.')) {
      this.analyzeJWT(token);
    } else {
      this.analyzeOpaqueToken(token);
    }
  }
  
  static analyzeJWT(token) {
    try {
      const parts = token.split('.');
      const header = JSON.parse(atob(parts[0]));
      const payload = JSON.parse(atob(parts[1]));
      
      console.log('JWT Analysis:');
      console.log('- Algorithm:', header.alg);
      console.log('- Type:', header.typ);
      
      if (payload.exp) {
        const expiry = new Date(payload.exp * 1000);
        const now = new Date();
        const timeLeft = expiry.getTime() - now.getTime();
        
        console.log('- Expires:', expiry.toISOString());
        console.log('- Time left:', Math.floor(timeLeft / 1000), 'seconds');
        
        if (timeLeft <= 0) {
          console.error('❌ Token is expired');
        } else if (timeLeft < 300000) { // 5 minutes
          console.warn('⚠️ Token expires soon');
        } else {
          console.log('✅ Token is valid');
        }
      }
      
      if (payload.aud) {
        console.log('- Audience:', payload.aud);
      }
      
      if (payload.scope) {
        console.log('- Scopes:', payload.scope);
      }
      
    } catch (error) {
      console.error('❌ Invalid JWT format:', error);
    }
  }
  
  static analyzeOpaqueToken(token) {
    console.log('Opaque Token Analysis:');
    console.log('- Length:', token.length);
    console.log('- Format:', /^[A-Za-z0-9_-]+$/.test(token) ? 'Base64URL' : 'Unknown');
    console.log('- Note: Use token introspection endpoint for details');
  }
}

// Usage
TokenDebugger.analyzeToken(accessToken);
```

**Solutions:**
```javascript
// ✅ Automatic token refresh
class SmartTokenManager {
  constructor() {
    this.refreshThreshold = 300; // 5 minutes
    this.refreshPromise = null;
  }
  
  async getValidToken() {
    const token = this.getStoredToken();
    
    if (!token) {
      throw new Error('NO_TOKEN');
    }
    
    if (this.isExpired(token)) {
      return await this.refreshToken();
    }
    
    if (this.needsRefresh(token)) {
      // Refresh in background
      this.refreshToken().catch(console.error);
    }
    
    return token.access_token;
  }
  
  async refreshToken() {
    // Prevent concurrent refresh attempts
    if (this.refreshPromise) {
      return this.refreshPromise;
    }
    
    this.refreshPromise = this._performRefresh();
    
    try {
      return await this.refreshPromise;
    } finally {
      this.refreshPromise = null;
    }
  }
  
  async _performRefresh() {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      throw new Error('NO_REFRESH_TOKEN');
    }
    
    try {
      const response = await fetch(`${AUTH_SERVER}/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          grant_type: 'refresh_token',
          refresh_token: refreshToken,
          client_id: CLIENT_ID
        })
      });
      
      if (!response.ok) {
        if (response.status === 400 || response.status === 401) {
          this.clearTokens();
          throw new Error('REFRESH_TOKEN_INVALID');
        }
        throw new Error(`Refresh failed: ${response.status}`);
      }
      
      const tokens = await response.json();
      this.setTokens(tokens);
      return tokens.access_token;
      
    } catch (error) {
      console.error('Token refresh failed:', error);
      throw error;
    }
  }
}
```

### Issue: Tokens Not Persisting

**Symptoms:**
- User logged out after page refresh
- Tokens disappear unexpectedly
- Have to login repeatedly

**Common Causes:**
```javascript
// ❌ Storing in wrong location
let accessToken = null; // Lost on page refresh

// ❌ Using localStorage incorrectly
localStorage.setItem('token', token); // Security risk

// ❌ Not handling storage errors
sessionStorage.setItem('tokens', JSON.stringify(tokens)); // May fail silently
```

**Solutions:**
```javascript
// ✅ Robust token storage
class SecureTokenStorage {
  constructor(storageKey = 'oauth2_tokens') {
    this.storageKey = storageKey;
    this.fallbackStorage = new Map(); // In-memory fallback
  }
  
  setTokens(tokens) {
    const tokenData = {
      ...tokens,
      stored_at: Date.now(),
      expires_at: Date.now() + (tokens.expires_in * 1000)
    };
    
    try {
      sessionStorage.setItem(this.storageKey, JSON.stringify(tokenData));
    } catch (error) {
      console.warn('SessionStorage failed, using memory storage:', error);
      this.fallbackStorage.set(this.storageKey, tokenData);
    }
  }
  
  getTokens() {
    try {
      const stored = sessionStorage.getItem(this.storageKey);
      if (stored) {
        const tokens = JSON.parse(stored);
        
        // Check expiration
        if (tokens.expires_at && Date.now() >= tokens.expires_at) {
          this.clearTokens();
          return null;
        }
        
        return tokens;
      }
    } catch (error) {
      console.warn('Failed to read from sessionStorage:', error);
    }
    
    // Try fallback storage
    const fallback = this.fallbackStorage.get(this.storageKey);
    if (fallback && fallback.expires_at && Date.now() < fallback.expires_at) {
      return fallback;
    }
    
    return null;
  }
  
  clearTokens() {
    try {
      sessionStorage.removeItem(this.storageKey);
    } catch (error) {
      console.warn('Failed to clear sessionStorage:', error);
    }
    
    this.fallbackStorage.delete(this.storageKey);
  }
}
```

---

## 🔒 PKCE Issues

### Issue: "Invalid Code Challenge"

**Symptoms:**
- Token exchange fails with PKCE error
- "code_challenge does not match" message
- Authorization works but token exchange fails

**Debugging PKCE:**
```javascript
class PKCEDebugger {
  static async validatePKCE(codeVerifier, codeChallenge) {
    console.log('PKCE Validation:');
    console.log('- Code Verifier:', codeVerifier?.substring(0, 10) + '...');
    console.log('- Code Challenge:', codeChallenge?.substring(0, 10) + '...');
    
    // Validate verifier format
    if (!codeVerifier) {
      console.error('❌ Missing code verifier');
      return false;
    }
    
    if (codeVerifier.length < 43 || codeVerifier.length > 128) {
      console.error('❌ Code verifier length invalid:', codeVerifier.length);
      return false;
    }
    
    const base64urlPattern = /^[A-Za-z0-9_-]+$/;
    if (!base64urlPattern.test(codeVerifier)) {
      console.error('❌ Code verifier not base64url encoded');
      return false;
    }
    
    // Validate challenge
    if (!codeChallenge) {
      console.error('❌ Missing code challenge');
      return false;
    }
    
    // Verify challenge matches verifier
    try {
      const expectedChallenge = await this.generateCodeChallenge(codeVerifier);
      if (expectedChallenge === codeChallenge) {
        console.log('✅ PKCE parameters are valid');
        return true;
      } else {
        console.error('❌ Code challenge does not match verifier');
        console.log('- Expected:', expectedChallenge);
        console.log('- Actual:', codeChallenge);
        return false;
      }
    } catch (error) {
      console.error('❌ Error validating PKCE:', error);
      return false;
    }
  }
  
  static async generateCodeChallenge(verifier) {
    const encoder = new TextEncoder();
    const data = encoder.encode(verifier);
    const digest = await crypto.subtle.digest('SHA-256', data);
    return btoa(String.fromCharCode(...new Uint8Array(digest)))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  }
}

// Usage
const codeVerifier = sessionStorage.getItem('code_verifier');
const codeChallenge = sessionStorage.getItem('code_challenge');
PKCEDebugger.validatePKCE(codeVerifier, codeChallenge);
```

**Common PKCE Fixes:**
```javascript
// ✅ Correct PKCE implementation
class RobustPKCE {
  generateCodeVerifier() {
    // Use maximum length for security
    const array = new Uint8Array(96); // 128 chars when base64url encoded
    crypto.getRandomValues(array);
    return this.base64URLEncode(array);
  }
  
  async generateCodeChallenge(verifier) {
    const encoder = new TextEncoder();
    const data = encoder.encode(verifier);
    const digest = await crypto.subtle.digest('SHA-256', data);
    return this.base64URLEncode(new Uint8Array(digest));
  }
  
  base64URLEncode(buffer) {
    return btoa(String.fromCharCode(...buffer))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  }
  
  // Store PKCE parameters securely
  storePKCEParameters(codeVerifier, codeChallenge) {
    try {
      sessionStorage.setItem('code_verifier', codeVerifier);
      sessionStorage.setItem('code_challenge', codeChallenge);
      sessionStorage.setItem('pkce_created_at', Date.now().toString());
    } catch (error) {
      console.error('Failed to store PKCE parameters:', error);
      throw new Error('Cannot store PKCE parameters');
    }
  }
  
  // Retrieve and validate PKCE parameters
  retrievePKCEParameters() {
    const codeVerifier = sessionStorage.getItem('code_verifier');
    const createdAt = sessionStorage.getItem('pkce_created_at');
    
    if (!codeVerifier) {
      throw new Error('Code verifier not found');
    }
    
    // Check if PKCE parameters are too old (10 minutes)
    if (createdAt && Date.now() - parseInt(createdAt) > 600000) {
      this.clearPKCEParameters();
      throw new Error('PKCE parameters expired');
    }
    
    return codeVerifier;
  }
  
  clearPKCEParameters() {
    sessionStorage.removeItem('code_verifier');
    sessionStorage.removeItem('code_challenge');
    sessionStorage.removeItem('pkce_created_at');
  }
}
```

---

## 🌐 Network and CORS Issues

### Issue: CORS Errors

**Symptoms:**
- "Access to fetch blocked by CORS policy"
- Network requests fail in browser
- Works in Postman but not in browser

**Common Causes:**
```javascript
// ❌ Wrong origin in CORS configuration
// Server allows: https://myapp.com
// Client runs on: https://localhost:3000

// ❌ Missing credentials in request
fetch('/api/data', {
  // Missing: credentials: 'include'
});

// ❌ Preflight request issues
fetch('/api/data', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json', // Triggers preflight
    'Authorization': `Bearer ${token}`
  }
});
```

**Solutions:**
```javascript
// ✅ Proper CORS handling
class CORSAwareAPIClient {
  constructor(baseURL, options = {}) {
    this.baseURL = baseURL;
    this.defaultOptions = {
      credentials: 'include', // Include cookies
      mode: 'cors',
      ...options
    };
  }
  
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const requestOptions = {
      ...this.defaultOptions,
      ...options,
      headers: {
        'Accept': 'application/json',
        ...this.defaultOptions.headers,
        ...options.headers
      }
    };
    
    try {
      const response = await fetch(url, requestOptions);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      if (error.name === 'TypeError' && error.message.includes('CORS')) {
        console.error('CORS Error - Check server configuration');
        console.log('Request URL:', url);
        console.log('Request Origin:', window.location.origin);
      }
      throw error;
    }
  }
}

// ✅ Development CORS proxy
// For development only - use a proxy to avoid CORS issues
const isDevelopment = process.env.NODE_ENV === 'development';
const apiBaseURL = isDevelopment 
  ? '/api-proxy'  // Proxy configured in webpack/vite
  : 'https://api.production.com';
```

### Issue: Network Timeouts

**Symptoms:**
- Requests hang indefinitely
- "Network request failed" errors
- Slow or unreliable connections

**Solutions:**
```javascript
// ✅ Robust network handling
class NetworkResilientClient {
  constructor(baseURL, options = {}) {
    this.baseURL = baseURL;
    this.defaultTimeout = options.timeout || 30000; // 30 seconds
    this.retryAttempts = options.retryAttempts || 3;
    this.retryDelay = options.retryDelay || 1000; // 1 second
  }
  
  async requestWithRetry(endpoint, options = {}) {
    let lastError;
    
    for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
      try {
        return await this.requestWithTimeout(endpoint, options);
      } catch (error) {
        lastError = error;
        
        // Don't retry on client errors (4xx)
        if (error.status >= 400 && error.status < 500) {
          throw error;
        }
        
        if (attempt < this.retryAttempts) {
          console.warn(`Request failed (attempt ${attempt}), retrying...`, error);
          await this.delay(this.retryDelay * attempt);
        }
      }
    }
    
    throw lastError;
  }
  
  async requestWithTimeout(endpoint, options = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.defaultTimeout);
    
    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        ...options,
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
        error.status = response.status;
        throw error;
      }
      
      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      
      throw error;
    }
  }
  
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

---

## 🔧 Development and Testing Issues

### Issue: Testing OAuth2 Flows

**Challenge:** OAuth2 flows are hard to test because they involve external services and user interaction.

**Solutions:**

#### Mock OAuth2 Server for Testing
```javascript
// ✅ Mock OAuth2 server for unit tests
class MockOAuth2Server {
  constructor() {
    this.codes = new Map();
    this.tokens = new Map();
  }
  
  // Mock authorization endpoint
  authorize(clientId, redirectUri, state, codeChallenge) {
    const code = 'mock_auth_code_' + Date.now();
    
    this.codes.set(code, {
      clientId,
      redirectUri,
      state,
      codeChallenge,
      createdAt: Date.now()
    });
    
    // Simulate redirect
    const callbackUrl = new URL(redirectUri);
    callbackUrl.searchParams.set('code', code);
    callbackUrl.searchParams.set('state', state);
    
    return callbackUrl.toString();
  }
  
  // Mock token endpoint
  async token(grantType, code, clientId, codeVerifier, redirectUri) {
    if (grantType !== 'authorization_code') {
      throw new Error('unsupported_grant_type');
    }
    
    const codeData = this.codes.get(code);
    if (!codeData) {
      throw new Error('invalid_grant');
    }
    
    // Validate PKCE
    if (codeData.codeChallenge) {
      const expectedChallenge = await this.generateCodeChallenge(codeVerifier);
      if (expectedChallenge !== codeData.codeChallenge) {
        throw new Error('invalid_grant');
      }
    }
    
    // Generate tokens
    const accessToken = 'mock_access_token_' + Date.now();
    const refreshToken = 'mock_refresh_token_' + Date.now();
    
    this.tokens.set(accessToken, {
      clientId,
      scope: 'read write',
      expiresAt: Date.now() + 3600000 // 1 hour
    });
    
    // Remove used code
    this.codes.delete(code);
    
    return {
      access_token: accessToken,
      refresh_token: refreshToken,
      token_type: 'Bearer',
      expires_in: 3600,
      scope: 'read write'
    };
  }
  
  async generateCodeChallenge(verifier) {
    const encoder = new TextEncoder();
    const data = encoder.encode(verifier);
    const digest = await crypto.subtle.digest('SHA-256', data);
    return btoa(String.fromCharCode(...new Uint8Array(digest)))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  }
}

// Usage in tests
describe('OAuth2 Flow', () => {
  let mockServer;
  let oauth2Client;
  
  beforeEach(() => {
    mockServer = new MockOAuth2Server();
    oauth2Client = new OAuth2Client({
      authServerUrl: 'mock://auth-server',
      clientId: 'test-client',
      redirectUri: 'http://localhost:3000/callback'
    });
    
    // Mock fetch to use mock server
    global.fetch = jest.fn().mockImplementation(mockFetch);
  });
  
  test('should complete authorization flow', async () => {
    // Test implementation
  });
});
```

#### Integration Testing with Real Providers
```javascript
// ✅ Integration test helper
class OAuth2TestHelper {
  constructor(provider = 'test') {
    this.config = this.getTestConfig(provider);
  }
  
  getTestConfig(provider) {
    const configs = {
      test: {
        authServerUrl: process.env.TEST_AUTH_SERVER_URL,
        clientId: process.env.TEST_CLIENT_ID,
        clientSecret: process.env.TEST_CLIENT_SECRET,
        redirectUri: 'http://localhost:3000/test-callback'
      },
      google: {
        authServerUrl: 'https://accounts.google.com',
        clientId: process.env.GOOGLE_TEST_CLIENT_ID,
        clientSecret: process.env.GOOGLE_TEST_CLIENT_SECRET,
        redirectUri: 'http://localhost:3000/test-callback'
      }
    };
    
    return configs[provider];
  }
  
  async testAuthorizationFlow() {
    const oauth2Client = new OAuth2Client(this.config);
    
    // Start authorization (this would open browser in real test)
    const authUrl = await oauth2Client.getAuthorizationUrl();
    console.log('Visit this URL to authorize:', authUrl);
    
    // In automated tests, you'd use a headless browser
    // to complete the authorization flow
    
    return authUrl;
  }
  
  async testTokenExchange(authorizationCode) {
    const oauth2Client = new OAuth2Client(this.config);
    
    try {
      const tokens = await oauth2Client.exchangeCodeForTokens(authorizationCode);
      console.log('✅ Token exchange successful');
      return tokens;
    } catch (error) {
      console.error('❌ Token exchange failed:', error);
      throw error;
    }
  }
}
```

---

## 📊 Monitoring and Debugging Tools

### OAuth2 Debug Dashboard

```javascript
// ✅ Debug dashboard for development
class OAuth2DebugDashboard {
  constructor(oauth2Client) {
    this.oauth2Client = oauth2Client;
    this.logs = [];
    this.setupEventListeners();
  }
  
  setupEventListeners() {
    // Listen for OAuth2 events
    window.addEventListener('oauth2AuthStart', (e) => {
      this.log('AUTH_START', 'Authorization flow started', e.detail);
    });
    
    window.addEventListener('oauth2AuthComplete', (e) => {
      this.log('AUTH_COMPLETE', 'Authorization completed', e.detail);
    });
    
    window.addEventListener('oauth2TokenRefresh', (e) => {
      this.log('TOKEN_REFRESH', 'Token refreshed', e.detail);
    });
    
    window.addEventListener('oauth2Error', (e) => {
      this.log('ERROR', 'OAuth2 error occurred', e.detail);
    });
  }
  
  log(type, message, data = {}) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      type,
      message,
      data
    };
    
    this.logs.push(logEntry);
    console.log(`[OAuth2 ${type}]`, message, data);
    
    // Update debug UI if present
    this.updateDebugUI();
  }
  
  updateDebugUI() {
    const debugElement = document.getElementById('oauth2-debug');
    if (!debugElement) return;
    
    const tokenManager = this.oauth2Client.tokenManager;
    const tokens = tokenManager.getTokens();
    
    debugElement.innerHTML = `
      <div class="oauth2-debug-panel">
        <h3>OAuth2 Debug Info</h3>
        
        <div class="debug-section">
          <h4>Authentication Status</h4>
          <p>Authenticated: ${this.oauth2Client.isAuthenticated() ? '✅' : '❌'}</p>
          ${tokens ? `
            <p>Access Token: ${tokens.access_token?.substring(0, 20)}...</p>
            <p>Expires: ${new Date(tokens.expires_at).toLocaleString()}</p>
            <p>Time Left: ${Math.floor((tokens.expires_at - Date.now()) / 1000)}s</p>
          ` : '<p>No tokens</p>'}
        </div>
        
        <div class="debug-section">
          <h4>Recent Events</h4>
          <div class="debug-logs">
            ${this.logs.slice(-10).reverse().map(log => `
              <div class="debug-log-entry ${log.type.toLowerCase()}">
                <span class="timestamp">${log.timestamp}</span>
                <span class="type">${log.type}</span>
                <span class="message">${log.message}</span>
              </div>
            `).join('')}
          </div>
        </div>
        
        <div class="debug-actions">
          <button onclick="oauth2Debug.clearLogs()">Clear Logs</button>
          <button onclick="oauth2Debug.exportLogs()">Export Logs</button>
          <button onclick="oauth2Debug.testConnection()">Test Connection</button>
        </div>
      </div>
    `;
  }
  
  clearLogs() {
    this.logs = [];
    this.updateDebugUI();
  }
  
  exportLogs() {
    const data = JSON.stringify(this.logs, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `oauth2-debug-${Date.now()}.json`;
    a.click();
    
    URL.revokeObjectURL(url);
  }
  
  async testConnection() {
    try {
      this.log('TEST', 'Testing OAuth2 connection...');
      
      const token = await this.oauth2Client.getAccessToken();
      if (token) {
        this.log('TEST', 'Connection test successful');
      } else {
        this.log('TEST', 'No valid token available');
      }
    } catch (error) {
      this.log('ERROR', 'Connection test failed', { error: error.message });
    }
  }
}

// Initialize debug dashboard in development
if (process.env.NODE_ENV === 'development') {
  window.oauth2Debug = new OAuth2DebugDashboard(oauth2Client);
}
```

---

## 🚨 Emergency Procedures

### Complete OAuth2 Reset

When everything goes wrong and you need to start fresh:

```javascript
// ✅ Nuclear option - complete reset
function emergencyOAuth2Reset() {
  console.warn('🚨 Performing emergency OAuth2 reset');
  
  // Clear all storage
  try {
    sessionStorage.clear();
    localStorage.removeItem('oauth2_tokens');
    localStorage.removeItem('oauth2_state');
    localStorage.removeItem('code_verifier');
    
    // Clear any other OAuth2-related storage
    Object.keys(localStorage).forEach(key => {
      if (key.includes('oauth') || key.includes('token') || key.includes('auth')) {
        localStorage.removeItem(key);
      }
    });
  } catch (error) {
    console.error('Failed to clear storage:', error);
  }
  
  // Clear URL parameters
  if (window.location.search.includes('code') || window.location.search.includes('error')) {
    window.history.replaceState({}, document.title, window.location.pathname);
  }
  
  // Reset any global state
  if (window.oauth2Client) {
    window.oauth2Client.tokenManager?.clearTokens();
  }
  
  // Force page reload
  setTimeout(() => {
    window.location.reload();
  }, 1000);
}

// Add to global scope for emergency use
window.emergencyOAuth2Reset = emergencyOAuth2Reset;
```

---

*This troubleshooting guide covers the most common OAuth2 issues you'll encounter. Keep it handy during development and refer to specific sections when problems arise.*