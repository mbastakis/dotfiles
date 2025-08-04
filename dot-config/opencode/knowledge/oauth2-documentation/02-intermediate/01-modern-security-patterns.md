# Modern OAuth2 Security Patterns - RFC 9700 and Beyond

## 🎯 Learning Objectives

By the end of this document, you will:
- [ ] Implement OAuth2 according to RFC 9700 security best practices
- [ ] Understand and apply advanced PKCE configurations
- [ ] Implement proper token binding and validation
- [ ] Apply modern security patterns for different client types
- [ ] Handle security edge cases and attack vectors
- [ ] Design secure OAuth2 architectures

**Estimated Time**: 4-5 hours  
**Prerequisites**: [First Implementation](../01-beginner/03-first-implementation.md)

---

## 📋 RFC 9700: OAuth2 Security Best Current Practice

RFC 9700 represents the current state-of-the-art in OAuth2 security. It consolidates years of security research and real-world attack patterns into actionable guidelines.

### 🔒 Core Security Requirements

#### 1. HTTPS Everywhere
**Requirement**: All OAuth2 endpoints MUST use TLS 1.2 or higher

```javascript
class SecureOAuth2Client {
  constructor(config) {
    this.validateSecureConfiguration(config);
    this.config = config;
  }

  validateSecureConfiguration(config) {
    // Enforce HTTPS for all endpoints
    const endpoints = [
      config.authServerUrl,
      config.redirectUri,
      config.apiBaseUrl
    ];

    endpoints.forEach(url => {
      if (url && !url.startsWith('https://')) {
        throw new Error(`Insecure endpoint detected: ${url}. All OAuth2 endpoints must use HTTPS.`);
      }
    });

    // Validate redirect URI security
    if (config.redirectUri.includes('*') || config.redirectUri.includes('..')) {
      throw new Error('Redirect URI must not contain wildcards or relative paths');
    }
  }
}
```

#### 2. PKCE for All Clients
**Requirement**: PKCE MUST be used by all OAuth2 clients, including confidential clients

```javascript
class EnhancedPKCE {
  constructor() {
    this.minVerifierLength = 43;
    this.maxVerifierLength = 128;
    this.challengeMethod = 'S256'; // Only SHA256 allowed
  }

  generateCodeVerifier() {
    // Generate cryptographically secure random string
    const length = 128; // Use maximum length for security
    const array = new Uint8Array(length);
    crypto.getRandomValues(array);
    
    // Convert to base64url
    return this.base64URLEncode(array);
  }

  async generateCodeChallenge(verifier) {
    // Validate verifier
    if (verifier.length < this.minVerifierLength || 
        verifier.length > this.maxVerifierLength) {
      throw new Error(`Code verifier length must be between ${this.minVerifierLength} and ${this.maxVerifierLength} characters`);
    }

    // Generate SHA256 challenge
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

  // Validate PKCE parameters
  validatePKCEParameters(codeVerifier, codeChallenge) {
    if (!codeVerifier || !codeChallenge) {
      throw new Error('Both code_verifier and code_challenge are required');
    }

    // Verify verifier format (base64url)
    const base64urlPattern = /^[A-Za-z0-9_-]+$/;
    if (!base64urlPattern.test(codeVerifier)) {
      throw new Error('Code verifier must be base64url encoded');
    }

    return true;
  }
}
```

#### 3. Short-Lived Authorization Codes
**Requirement**: Authorization codes MUST expire within 10 minutes

```javascript
class AuthorizationCodeManager {
  constructor() {
    this.maxCodeLifetime = 10 * 60 * 1000; // 10 minutes in milliseconds
    this.usedCodes = new Set(); // Track used codes
  }

  generateAuthorizationCode() {
    const code = {
      value: this.generateSecureRandomString(32),
      createdAt: Date.now(),
      used: false
    };

    // Set automatic expiration
    setTimeout(() => {
      this.expireCode(code.value);
    }, this.maxCodeLifetime);

    return code;
  }

  validateAuthorizationCode(code, receivedAt = Date.now()) {
    // Check if code has been used (replay attack prevention)
    if (this.usedCodes.has(code.value)) {
      throw new Error('Authorization code has already been used');
    }

    // Check expiration
    const age = receivedAt - code.createdAt;
    if (age > this.maxCodeLifetime) {
      throw new Error('Authorization code has expired');
    }

    // Mark as used
    this.usedCodes.add(code.value);
    code.used = true;

    return true;
  }

  expireCode(codeValue) {
    this.usedCodes.add(codeValue);
  }

  generateSecureRandomString(length) {
    const array = new Uint8Array(length);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }
}
```

#### 4. Exact Redirect URI Matching
**Requirement**: Redirect URIs MUST be validated using exact string matching

```javascript
class RedirectURIValidator {
  constructor(registeredURIs) {
    this.registeredURIs = new Set(registeredURIs);
    this.validateRegisteredURIs();
  }

  validateRegisteredURIs() {
    this.registeredURIs.forEach(uri => {
      // Must be HTTPS (except localhost for development)
      if (!uri.startsWith('https://') && !uri.startsWith('http://localhost')) {
        throw new Error(`Redirect URI must use HTTPS: ${uri}`);
      }

      // No wildcards allowed
      if (uri.includes('*')) {
        throw new Error(`Wildcard not allowed in redirect URI: ${uri}`);
      }

      // No fragments allowed
      if (uri.includes('#')) {
        throw new Error(`Fragment not allowed in redirect URI: ${uri}`);
      }

      // Validate URL format
      try {
        new URL(uri);
      } catch (error) {
        throw new Error(`Invalid redirect URI format: ${uri}`);
      }
    });
  }

  validateRedirectURI(requestedURI) {
    // Exact string matching - no normalization
    if (!this.registeredURIs.has(requestedURI)) {
      throw new Error(`Redirect URI not registered: ${requestedURI}`);
    }

    return true;
  }

  // For development environments only
  addLocalhostURI(port) {
    const localhostURI = `http://localhost:${port}`;
    this.registeredURIs.add(localhostURI);
    console.warn(`Added localhost URI for development: ${localhostURI}`);
  }
}
```

---

## 🛡️ Advanced Security Patterns

### 1. Token Binding

Token binding cryptographically binds tokens to the client, preventing token theft attacks.

#### Demonstrating Proof of Possession (DPoP) - RFC 9449

```javascript
class DPoPTokenBinding {
  constructor() {
    this.keyPair = null;
    this.algorithm = 'ES256'; // ECDSA with SHA-256
  }

  async initialize() {
    // Generate key pair for token binding
    this.keyPair = await crypto.subtle.generateKey(
      {
        name: 'ECDSA',
        namedCurve: 'P-256'
      },
      false, // Not extractable for security
      ['sign', 'verify']
    );
  }

  async createDPoPProof(httpMethod, url, accessToken = null) {
    if (!this.keyPair) {
      throw new Error('DPoP key pair not initialized');
    }

    // Create JWK for public key
    const publicKeyJWK = await this.exportPublicKeyAsJWK();

    // Create DPoP JWT header
    const header = {
      typ: 'dpop+jwt',
      alg: this.algorithm,
      jwk: publicKeyJWK
    };

    // Create DPoP JWT payload
    const payload = {
      jti: crypto.randomUUID(), // Unique identifier
      htm: httpMethod.toUpperCase(), // HTTP method
      htu: this.normalizeURL(url), // HTTP URI
      iat: Math.floor(Date.now() / 1000), // Issued at
      exp: Math.floor(Date.now() / 1000) + 60 // Expires in 1 minute
    };

    // Add access token hash if provided
    if (accessToken) {
      payload.ath = await this.sha256Hash(accessToken);
    }

    // Sign the JWT
    return await this.signJWT(header, payload);
  }

  async exportPublicKeyAsJWK() {
    const publicKey = await crypto.subtle.exportKey('jwk', this.keyPair.publicKey);
    
    return {
      kty: publicKey.kty,
      crv: publicKey.crv,
      x: publicKey.x,
      y: publicKey.y
    };
  }

  async signJWT(header, payload) {
    const headerB64 = this.base64URLEncode(JSON.stringify(header));
    const payloadB64 = this.base64URLEncode(JSON.stringify(payload));
    const signingInput = `${headerB64}.${payloadB64}`;

    const signature = await crypto.subtle.sign(
      { name: 'ECDSA', hash: 'SHA-256' },
      this.keyPair.privateKey,
      new TextEncoder().encode(signingInput)
    );

    const signatureB64 = this.base64URLEncode(new Uint8Array(signature));
    return `${signingInput}.${signatureB64}`;
  }

  async sha256Hash(input) {
    const encoder = new TextEncoder();
    const data = encoder.encode(input);
    const digest = await crypto.subtle.digest('SHA-256', data);
    return this.base64URLEncode(new Uint8Array(digest));
  }

  normalizeURL(url) {
    const urlObj = new URL(url);
    // Remove query parameters and fragments for DPoP
    return `${urlObj.protocol}//${urlObj.host}${urlObj.pathname}`;
  }

  base64URLEncode(data) {
    if (typeof data === 'string') {
      data = new TextEncoder().encode(data);
    }
    return btoa(String.fromCharCode(...data))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  }
}

// Usage example
class DPoPEnabledAPIClient {
  constructor(oauth2Client) {
    this.oauth2Client = oauth2Client;
    this.dpop = new DPoPTokenBinding();
  }

  async initialize() {
    await this.dpop.initialize();
  }

  async makeRequest(method, url, options = {}) {
    const accessToken = await this.oauth2Client.getAccessToken();
    if (!accessToken) {
      throw new Error('No access token available');
    }

    // Create DPoP proof
    const dpopProof = await this.dpop.createDPoPProof(method, url, accessToken);

    const requestOptions = {
      ...options,
      method,
      headers: {
        'Authorization': `DPoP ${accessToken}`,
        'DPoP': dpopProof,
        ...options.headers
      }
    };

    return fetch(url, requestOptions);
  }
}
```

### 2. Enhanced State Parameter Security

```javascript
class EnhancedStateManager {
  constructor() {
    this.stateStore = new Map();
    this.maxStateAge = 10 * 60 * 1000; // 10 minutes
  }

  generateState(additionalData = {}) {
    const state = {
      value: this.generateSecureRandomString(32),
      createdAt: Date.now(),
      nonce: crypto.randomUUID(),
      clientData: additionalData,
      used: false
    };

    // Store state with automatic cleanup
    this.stateStore.set(state.value, state);
    
    setTimeout(() => {
      this.stateStore.delete(state.value);
    }, this.maxStateAge);

    return state.value;
  }

  validateState(stateValue, receivedAt = Date.now()) {
    const state = this.stateStore.get(stateValue);
    
    if (!state) {
      throw new Error('Invalid or expired state parameter');
    }

    if (state.used) {
      throw new Error('State parameter has already been used');
    }

    const age = receivedAt - state.createdAt;
    if (age > this.maxStateAge) {
      this.stateStore.delete(stateValue);
      throw new Error('State parameter has expired');
    }

    // Mark as used and remove from store
    state.used = true;
    this.stateStore.delete(stateValue);

    return state.clientData;
  }

  generateSecureRandomString(length) {
    const array = new Uint8Array(length);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }

  // Clean up expired states
  cleanup() {
    const now = Date.now();
    for (const [key, state] of this.stateStore.entries()) {
      if (now - state.createdAt > this.maxStateAge) {
        this.stateStore.delete(key);
      }
    }
  }
}
```

### 3. Advanced Token Management

```javascript
class SecureTokenManager {
  constructor(config) {
    this.config = config;
    this.tokens = null;
    this.refreshPromise = null; // Prevent concurrent refresh attempts
    this.setupSecurityFeatures();
  }

  setupSecurityFeatures() {
    // Token rotation on refresh
    this.rotateRefreshTokens = true;
    
    // Maximum token lifetime
    this.maxAccessTokenLifetime = 3600; // 1 hour
    this.maxRefreshTokenLifetime = 86400 * 30; // 30 days
    
    // Refresh threshold
    this.refreshThreshold = 300; // 5 minutes before expiry
  }

  setTokens(tokens) {
    // Validate token response
    this.validateTokenResponse(tokens);

    this.tokens = {
      access_token: tokens.access_token,
      refresh_token: tokens.refresh_token,
      expires_in: Math.min(tokens.expires_in, this.maxAccessTokenLifetime),
      token_type: tokens.token_type || 'Bearer',
      scope: tokens.scope,
      expires_at: Date.now() + (Math.min(tokens.expires_in, this.maxAccessTokenLifetime) * 1000),
      refresh_expires_at: Date.now() + this.maxRefreshTokenLifetime * 1000
    };

    this.storeTokensSecurely();
    this.scheduleTokenRefresh();
  }

  validateTokenResponse(tokens) {
    if (!tokens.access_token) {
      throw new Error('Missing access_token in token response');
    }

    if (!tokens.expires_in || tokens.expires_in <= 0) {
      throw new Error('Invalid expires_in value');
    }

    // Validate token format if JWT
    if (tokens.access_token.includes('.')) {
      this.validateJWTFormat(tokens.access_token);
    }

    // Check for suspicious token lifetimes
    if (tokens.expires_in > this.maxAccessTokenLifetime) {
      console.warn(`Access token lifetime (${tokens.expires_in}s) exceeds maximum (${this.maxAccessTokenLifetime}s)`);
    }
  }

  validateJWTFormat(token) {
    const parts = token.split('.');
    if (parts.length !== 3) {
      throw new Error('Invalid JWT format');
    }

    try {
      // Validate header
      const header = JSON.parse(atob(parts[0].replace(/-/g, '+').replace(/_/g, '/')));
      if (!header.alg || header.alg === 'none') {
        throw new Error('JWT must have a valid algorithm');
      }

      // Validate payload structure
      const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
      if (!payload.exp) {
        console.warn('JWT missing expiration claim');
      }

    } catch (error) {
      throw new Error('Invalid JWT structure: ' + error.message);
    }
  }

  async refreshTokens() {
    // Prevent concurrent refresh attempts
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this._performTokenRefresh();
    
    try {
      const result = await this.refreshPromise;
      return result;
    } finally {
      this.refreshPromise = null;
    }
  }

  async _performTokenRefresh() {
    const refreshToken = this.tokens?.refresh_token;
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    // Check if refresh token is expired
    if (this.tokens.refresh_expires_at && Date.now() >= this.tokens.refresh_expires_at) {
      this.clearTokens();
      throw new Error('REFRESH_TOKEN_EXPIRED');
    }

    const response = await fetch(this.config.tokenEndpoint, {
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
        this.clearTokens();
        throw new Error('REFRESH_TOKEN_INVALID');
      }
      
      throw new Error(`Token refresh failed: ${response.status} - ${errorData.error || 'Unknown error'}`);
    }

    const newTokens = await response.json();
    this.setTokens(newTokens);
    
    return newTokens;
  }

  scheduleTokenRefresh() {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    if (!this.tokens?.expires_at) {
      return;
    }

    const refreshTime = this.tokens.expires_at - (this.refreshThreshold * 1000) - Date.now();
    
    if (refreshTime > 0) {
      this.refreshTimer = setTimeout(async () => {
        try {
          await this.refreshTokens();
        } catch (error) {
          console.error('Automatic token refresh failed:', error);
          // Emit event for application to handle
          this.emitTokenRefreshError(error);
        }
      }, refreshTime);
    }
  }

  storeTokensSecurely() {
    // Use sessionStorage with additional security measures
    try {
      const tokenData = {
        ...this.tokens,
        stored_at: Date.now(),
        checksum: this.calculateChecksum(this.tokens)
      };

      sessionStorage.setItem(this.config.storageKey, JSON.stringify(tokenData));
    } catch (error) {
      console.error('Failed to store tokens:', error);
    }
  }

  loadTokensSecurely() {
    try {
      const stored = sessionStorage.getItem(this.config.storageKey);
      if (!stored) return null;

      const tokenData = JSON.parse(stored);
      
      // Verify checksum
      const expectedChecksum = this.calculateChecksum({
        access_token: tokenData.access_token,
        refresh_token: tokenData.refresh_token,
        expires_at: tokenData.expires_at
      });

      if (tokenData.checksum !== expectedChecksum) {
        console.warn('Token checksum mismatch - possible tampering');
        this.clearTokens();
        return null;
      }

      // Check if tokens are expired
      if (tokenData.expires_at && Date.now() >= tokenData.expires_at) {
        this.clearTokens();
        return null;
      }

      return tokenData;
    } catch (error) {
      console.error('Failed to load tokens:', error);
      this.clearTokens();
      return null;
    }
  }

  calculateChecksum(tokens) {
    // Simple checksum to detect tampering
    const data = `${tokens.access_token}:${tokens.refresh_token}:${tokens.expires_at}`;
    return btoa(data).slice(0, 16);
  }

  emitTokenRefreshError(error) {
    // Emit custom event for application to handle
    window.dispatchEvent(new CustomEvent('oauth2TokenRefreshError', {
      detail: { error }
    }));
  }

  clearTokens() {
    this.tokens = null;
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
    
    try {
      sessionStorage.removeItem(this.config.storageKey);
    } catch (error) {
      console.warn('Failed to clear stored tokens:', error);
    }
  }
}
```

---

## 🏗️ Client Type Security Profiles

### 1. Single Page Application (SPA) Security Profile

```javascript
class SPASecurityProfile {
  constructor() {
    this.clientType = 'public';
    this.requiresPKCE = true;
    this.canStoreSecrets = false;
    this.tokenStorage = 'memory'; // Never localStorage
  }

  getSecurityConfiguration() {
    return {
      // PKCE is mandatory
      pkce: {
        required: true,
        codeVerifierLength: 128, // Maximum length
        challengeMethod: 'S256'
      },

      // Token security
      tokens: {
        storage: 'sessionStorage', // Or memory only
        maxLifetime: 3600, // 1 hour max
        refreshThreshold: 300, // 5 minutes
        rotateRefreshTokens: true
      },

      // Request security
      requests: {
        requireHTTPS: true,
        validateState: true,
        maxAuthorizationAge: 600, // 10 minutes
        requireExactRedirectMatch: true
      },

      // Additional security measures
      security: {
        enableCSP: true,
        enableSRI: true,
        preventXSS: true,
        validateOrigin: true
      }
    };
  }

  validateEnvironment() {
    // Check if running in secure context
    if (!window.isSecureContext) {
      throw new Error('OAuth2 requires a secure context (HTTPS)');
    }

    // Validate CSP if available
    if (this.hasContentSecurityPolicy()) {
      this.validateCSP();
    }

    // Check for XSS protection
    this.validateXSSProtection();
  }

  hasContentSecurityPolicy() {
    const metaTags = document.querySelectorAll('meta[http-equiv="Content-Security-Policy"]');
    return metaTags.length > 0 || this.hasCSPHeader();
  }

  hasCSPHeader() {
    // This would need to be checked server-side
    // For client-side, we can only check meta tags
    return false;
  }

  validateCSP() {
    // Validate that CSP allows necessary OAuth2 operations
    console.log('CSP validation would be implemented here');
  }

  validateXSSProtection() {
    // Check for basic XSS protection measures
    if (typeof window.DOMPurify === 'undefined') {
      console.warn('Consider using DOMPurify for XSS protection');
    }
  }
}
```

### 2. Server-Side Application Security Profile

```javascript
class ServerSideSecurityProfile {
  constructor() {
    this.clientType = 'confidential';
    this.requiresPKCE = true; // Recommended even for confidential clients
    this.canStoreSecrets = true;
    this.tokenStorage = 'server-session';
  }

  getSecurityConfiguration() {
    return {
      // Client authentication
      clientAuth: {
        method: 'client_secret_basic', // Or client_secret_post
        secretRotation: true,
        secretMinLength: 32
      },

      // PKCE (recommended)
      pkce: {
        required: true,
        codeVerifierLength: 128,
        challengeMethod: 'S256'
      },

      // Token security
      tokens: {
        storage: 'encrypted-session',
        maxLifetime: 3600,
        refreshThreshold: 300,
        rotateRefreshTokens: true,
        bindToSession: true
      },

      // Server security
      server: {
        requireHTTPS: true,
        validateOrigin: true,
        enableCSRFProtection: true,
        secureSessionCookies: true,
        httpOnlyCookies: true
      }
    };
  }

  // Server-side token storage implementation
  storeTokensSecurely(tokens, sessionId) {
    // Encrypt tokens before storage
    const encryptedTokens = this.encryptTokens(tokens);
    
    // Store in secure session storage
    return this.sessionStore.set(sessionId, {
      tokens: encryptedTokens,
      createdAt: Date.now(),
      lastAccessed: Date.now()
    });
  }

  encryptTokens(tokens) {
    // Implementation would use server-side encryption
    // This is a placeholder for the concept
    return {
      encrypted: true,
      data: 'encrypted_token_data',
      iv: 'initialization_vector',
      tag: 'authentication_tag'
    };
  }
}
```

### 3. Mobile Application Security Profile

```javascript
class MobileSecurityProfile {
  constructor() {
    this.clientType = 'public';
    this.requiresPKCE = true;
    this.canStoreSecrets = false;
    this.tokenStorage = 'secure-keychain';
  }

  getSecurityConfiguration() {
    return {
      // PKCE is mandatory
      pkce: {
        required: true,
        codeVerifierLength: 128,
        challengeMethod: 'S256'
      },

      // Mobile-specific security
      mobile: {
        useCustomSchemes: true,
        validateAppSignature: true,
        enableAppAttestation: true,
        preventScreenshots: true
      },

      // Token security
      tokens: {
        storage: 'keychain', // iOS Keychain / Android Keystore
        maxLifetime: 3600,
        refreshThreshold: 300,
        rotateRefreshTokens: true,
        bindToDevice: true
      },

      // Network security
      network: {
        enableCertificatePinning: true,
        requireHTTPS: true,
        validateHostname: true,
        timeoutSettings: {
          connect: 10000,
          read: 30000
        }
      }
    };
  }

  // Mobile-specific redirect handling
  handleCustomSchemeRedirect(url) {
    // Validate the custom scheme
    if (!url.startsWith(this.config.customScheme)) {
      throw new Error('Invalid redirect scheme');
    }

    // Extract parameters
    const urlObj = new URL(url);
    const params = new URLSearchParams(urlObj.search);

    // Validate app signature (platform-specific)
    this.validateAppSignature();

    return {
      code: params.get('code'),
      state: params.get('state'),
      error: params.get('error')
    };
  }

  validateAppSignature() {
    // Platform-specific implementation
    // iOS: Validate app bundle signature
    // Android: Validate APK signature
    console.log('App signature validation would be implemented here');
  }
}
```

---

## 🧪 Security Testing and Validation

### Automated Security Testing

```javascript
class OAuth2SecurityTester {
  constructor(oauth2Client) {
    this.oauth2Client = oauth2Client;
    this.testResults = [];
  }

  async runSecurityTests() {
    console.log('Running OAuth2 security tests...');
    
    const tests = [
      this.testPKCEImplementation,
      this.testStateValidation,
      this.testTokenSecurity,
      this.testRedirectURIValidation,
      this.testCSRFProtection,
      this.testTokenExpiration
    ];

    for (const test of tests) {
      try {
        await test.call(this);
        this.addTestResult(test.name, 'PASS');
      } catch (error) {
        this.addTestResult(test.name, 'FAIL', error.message);
      }
    }

    return this.generateReport();
  }

  async testPKCEImplementation() {
    // Test PKCE parameter generation
    const { codeVerifier, codeChallenge } = this.oauth2Client.generatePKCE();
    
    if (!codeVerifier || codeVerifier.length < 43) {
      throw new Error('Code verifier too short');
    }

    if (!codeChallenge || codeChallenge === codeVerifier) {
      throw new Error('Invalid code challenge');
    }

    // Test that PKCE is required
    try {
      await this.oauth2Client.authorize({ skipPKCE: true });
      throw new Error('PKCE should be required');
    } catch (error) {
      if (!error.message.includes('PKCE')) {
        throw new Error('PKCE validation not implemented');
      }
    }
  }

  async testStateValidation() {
    // Test state parameter generation
    const state1 = this.oauth2Client._generateState();
    const state2 = this.oauth2Client._generateState();
    
    if (state1 === state2) {
      throw new Error('State values should be unique');
    }

    // Test state validation
    sessionStorage.setItem('oauth_state', 'test_state');
    
    try {
      await this.oauth2Client.handleCallback('?code=test&state=wrong_state');
      throw new Error('Invalid state should be rejected');
    } catch (error) {
      if (!error.message.includes('state')) {
        throw new Error('State validation not implemented');
      }
    }
  }

  async testTokenSecurity() {
    // Test that tokens are not stored in localStorage
    const tokenManager = this.oauth2Client.tokenManager;
    
    // Mock tokens
    const mockTokens = {
      access_token: 'test_token',
      refresh_token: 'test_refresh',
      expires_in: 3600
    };

    tokenManager.setTokens(mockTokens);

    // Check localStorage
    const localStorageKeys = Object.keys(localStorage);
    const hasTokensInLocalStorage = localStorageKeys.some(key => 
      localStorage.getItem(key)?.includes('test_token')
    );

    if (hasTokensInLocalStorage) {
      throw new Error('Tokens found in localStorage - security risk');
    }
  }

  async testRedirectURIValidation() {
    // Test that redirect URI validation is strict
    const validator = new RedirectURIValidator(['https://app.example.com/callback']);
    
    // Test valid URI
    try {
      validator.validateRedirectURI('https://app.example.com/callback');
    } catch (error) {
      throw new Error('Valid redirect URI rejected');
    }

    // Test invalid URI
    try {
      validator.validateRedirectURI('https://evil.com/callback');
      throw new Error('Invalid redirect URI accepted');
    } catch (error) {
      // Expected
    }

    // Test wildcard rejection
    try {
      validator.validateRedirectURI('https://app.example.com/*');
      throw new Error('Wildcard redirect URI accepted');
    } catch (error) {
      // Expected
    }
  }

  async testCSRFProtection() {
    // Test that state parameter provides CSRF protection
    const stateManager = new EnhancedStateManager();
    const state = stateManager.generateState();
    
    // Test valid state
    try {
      stateManager.validateState(state);
    } catch (error) {
      throw new Error('Valid state rejected');
    }

    // Test replay attack protection
    try {
      stateManager.validateState(state);
      throw new Error('State reuse should be prevented');
    } catch (error) {
      // Expected
    }
  }

  async testTokenExpiration() {
    // Test token expiration handling
    const tokenManager = this.oauth2Client.tokenManager;
    
    // Mock expired tokens
    const expiredTokens = {
      access_token: 'expired_token',
      refresh_token: 'refresh_token',
      expires_in: -1, // Already expired
      expires_at: Date.now() - 1000
    };

    tokenManager.setTokens(expiredTokens);

    if (tokenManager.hasValidTokens()) {
      throw new Error('Expired tokens reported as valid');
    }
  }

  addTestResult(testName, status, error = null) {
    this.testResults.push({
      test: testName,
      status,
      error,
      timestamp: new Date().toISOString()
    });
  }

  generateReport() {
    const passed = this.testResults.filter(r => r.status === 'PASS').length;
    const failed = this.testResults.filter(r => r.status === 'FAIL').length;
    
    const report = {
      summary: {
        total: this.testResults.length,
        passed,
        failed,
        score: Math.round((passed / this.testResults.length) * 100)
      },
      results: this.testResults,
      recommendations: this.generateRecommendations()
    };

    console.log('Security Test Report:', report);
    return report;
  }

  generateRecommendations() {
    const failedTests = this.testResults.filter(r => r.status === 'FAIL');
    const recommendations = [];

    failedTests.forEach(test => {
      switch (test.test) {
        case 'testPKCEImplementation':
          recommendations.push('Implement PKCE with proper code verifier generation');
          break;
        case 'testStateValidation':
          recommendations.push('Add state parameter validation for CSRF protection');
          break;
        case 'testTokenSecurity':
          recommendations.push('Store tokens in sessionStorage or memory, never localStorage');
          break;
        case 'testRedirectURIValidation':
          recommendations.push('Implement strict redirect URI validation');
          break;
        default:
          recommendations.push(`Fix security issue in ${test.test}`);
      }
    });

    return recommendations;
  }
}
```

---

## 🎯 Knowledge Check

Before moving to practical implementations, ensure you can:

- [ ] Implement OAuth2 according to RFC 9700 requirements
- [ ] Apply appropriate security profiles for different client types
- [ ] Implement advanced security patterns like DPoP
- [ ] Validate OAuth2 implementations for security vulnerabilities
- [ ] Handle security edge cases and attack scenarios

### Practical Exercise

**Challenge**: Enhance your OAuth2 implementation with:
1. DPoP token binding
2. Enhanced state management with additional security
3. Comprehensive security testing
4. Client type-specific security profiles

### Security Assessment Questions

1. **Why is PKCE now required for all OAuth2 clients, not just public ones?**
2. **How does DPoP prevent token theft attacks?**
3. **What are the security implications of storing tokens in localStorage vs sessionStorage?**
4. **How can you detect and prevent authorization code replay attacks?**

<details>
<summary>Click for answers</summary>

1. **PKCE for all clients**: Even confidential clients can be compromised, and PKCE provides defense-in-depth against authorization code interception attacks.

2. **DPoP protection**: DPoP cryptographically binds tokens to the client's key pair, so even if tokens are stolen, they can't be used without the private key.

3. **Token storage**: localStorage persists across browser sessions and is accessible to all scripts, while sessionStorage is cleared when the tab closes and provides better isolation.

4. **Replay attack prevention**: Track used authorization codes and reject any code that's been used before, combined with short expiration times.

</details>

---

## 🚀 What's Next?

You've mastered modern OAuth2 security patterns. Continue with:

**Next Document**: [Practical Implementations](./02-practical-implementations.md)
- Real-world implementation patterns
- Framework-specific integrations
- Production deployment considerations

**Related Reading**:
- [Security Checklist](../05-security/security-checklist.md) - Comprehensive security validation
- [Advanced Security](../03-advanced/03-advanced-security.md) - Enterprise security patterns

---

## 📚 Additional Resources

### Specifications
- [RFC 9700: OAuth 2.0 Security Best Current Practice](https://tools.ietf.org/html/rfc9700)
- [RFC 9449: OAuth 2.0 Demonstrating Proof-of-Possession](https://tools.ietf.org/html/rfc9449)
- [RFC 9126: OAuth 2.0 Pushed Authorization Requests](https://tools.ietf.org/html/rfc9126)

### Security Resources
- [OWASP OAuth2 Security](https://owasp.org/www-community/vulnerabilities/OAuth2_Common_Vulnerabilities)
- [OAuth2 Threat Model](https://tools.ietf.org/html/rfc6819)

---

*Modern OAuth2 security is about defense-in-depth. Layer multiple security measures to create robust protection against evolving attack vectors.*