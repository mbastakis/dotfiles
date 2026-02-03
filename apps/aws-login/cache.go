package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"time"
)

// CachedSession represents a cached AWS session
type CachedSession struct {
	Profile         string       `json:"profile"`
	Identity        *Identity    `json:"identity"`
	Credentials     *Credentials `json:"credentials,omitempty"`
	ExpirationEpoch int64        `json:"expiration_epoch"`
	Region          string       `json:"region,omitempty"`
}

// RemainingSeconds returns how many seconds until the cached session expires
func (c *CachedSession) RemainingSeconds() int64 {
	return c.ExpirationEpoch - time.Now().Unix()
}

// ToAuthResult converts a cached session to an auth result
func (c *CachedSession) ToAuthResult() *AuthResult {
	return &AuthResult{
		Identity:        c.Identity,
		Credentials:     c.Credentials,
		ExpirationEpoch: c.ExpirationEpoch,
		Region:          c.Region,
	}
}

// LoadCache attempts to load a cached session for the given profile
func LoadCache(cfg *Config, profileName string) (*AuthResult, error) {
	cacheFile := filepath.Join(cfg.Cache.Directory, profileName+".cache")

	data, err := os.ReadFile(cacheFile)
	if err != nil {
		return nil, err
	}

	var cached CachedSession
	if err := json.Unmarshal(data, &cached); err != nil {
		return nil, err
	}

	// Check if expired or expiring soon
	remaining := cached.RemainingSeconds()
	bufferSeconds := int64(cfg.Defaults.CacheTTLBuffer.Seconds())

	if remaining <= bufferSeconds {
		LogVerbose("Cache expired or expiring soon, refreshing...")
		return nil, os.ErrNotExist
	}

	// For MFA profiles, ensure credentials are present
	profile, ok := cfg.Profiles[profileName]
	if ok && profile.Type == "mfa" && cached.Credentials == nil {
		LogVerbose("Cache missing credentials, refreshing...")
		return nil, os.ErrNotExist
	}

	return cached.ToAuthResult(), nil
}

// SaveCache saves a session to the cache
func SaveCache(cfg *Config, profileName string, result *AuthResult) error {
	// Ensure cache directory exists
	if err := os.MkdirAll(cfg.Cache.Directory, 0700); err != nil {
		return err
	}

	cached := CachedSession{
		Profile:         profileName,
		Identity:        result.Identity,
		Credentials:     result.Credentials,
		ExpirationEpoch: result.ExpirationEpoch,
		Region:          result.Region,
	}

	data, err := json.MarshalIndent(cached, "", "  ")
	if err != nil {
		return err
	}

	cacheFile := filepath.Join(cfg.Cache.Directory, profileName+".cache")

	// Write with restricted permissions
	if err := os.WriteFile(cacheFile, data, 0600); err != nil {
		return err
	}

	return nil
}
