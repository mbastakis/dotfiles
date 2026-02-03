package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"time"
)

// Identity represents AWS caller identity
type Identity struct {
	UserID  string `json:"UserId"`
	Account string `json:"Account"`
	ARN     string `json:"Arn"`
}

// Credentials represents AWS credentials
type Credentials struct {
	AccessKeyID     string `json:"access_key_id"`
	SecretAccessKey string `json:"secret_access_key"`
	SessionToken    string `json:"session_token"`
}

// AuthResult represents the result of an authentication attempt
type AuthResult struct {
	Identity        *Identity
	Credentials     *Credentials
	ExpirationEpoch int64
	Region          string
}

// RemainingSeconds returns how many seconds until the credentials expire
func (r *AuthResult) RemainingSeconds() int64 {
	return r.ExpirationEpoch - time.Now().Unix()
}

// AuthMFA authenticates using MFA
func AuthMFA(cfg *Config, profileName string, profile ProfileConfig, mfaCode string) (*AuthResult, error) {
	// Get MFA code if not provided
	if mfaCode == "" {
		if cfg.Bitwarden.Enabled && profile.BitwardenItem != "" {
			LogVerbose("Fetching MFA code from Bitwarden...")
			var err error
			mfaCode, err = GetTOTPFromBitwarden(profile.BitwardenItem)
			if err != nil {
				return nil, fmt.Errorf("failed to get MFA code from Bitwarden: %w", err)
			}
		} else {
			return nil, fmt.Errorf("MFA code required (provide as argument or configure Bitwarden)")
		}
	} else {
		LogVerbose("Using manually provided MFA code...")
	}

	// Get base credentials from ~/.aws/credentials
	accessKey, secretKey, err := getAWSCredentials(profileName)
	if err != nil {
		return nil, err
	}

	// Get MFA serial from ~/.aws/config
	mfaSerial := profile.MFASerial
	if mfaSerial == "auto" || mfaSerial == "" {
		mfaSerial, err = getMFASerial(profileName)
		if err != nil {
			return nil, err
		}
	}

	// Get region
	region := profile.Region
	if region == "" {
		region = cfg.Defaults.Region
	}

	// Set up environment for STS call
	env := os.Environ()
	env = setEnv(env, "AWS_ACCESS_KEY_ID", accessKey)
	env = setEnv(env, "AWS_SECRET_ACCESS_KEY", secretKey)
	env = setEnv(env, "AWS_DEFAULT_REGION", region)
	// Remove session token if set
	env = removeEnv(env, "AWS_SESSION_TOKEN")

	// Get session token with MFA
	LogVerbose("Requesting session token from AWS STS...")
	cmd := exec.Command("aws", "sts", "get-session-token",
		"--serial-number", mfaSerial,
		"--token-code", mfaCode)
	cmd.Env = env

	output, err := cmd.Output()
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			return nil, fmt.Errorf("STS error: %s", string(exitErr.Stderr))
		}
		return nil, fmt.Errorf("failed to get session token: %w", err)
	}

	// Parse response
	var response struct {
		Credentials struct {
			AccessKeyID     string `json:"AccessKeyId"`
			SecretAccessKey string `json:"SecretAccessKey"`
			SessionToken    string `json:"SessionToken"`
			Expiration      string `json:"Expiration"`
		} `json:"Credentials"`
	}

	if err := json.Unmarshal(output, &response); err != nil {
		return nil, fmt.Errorf("failed to parse STS response: %w", err)
	}

	// Parse expiration
	expiration, err := time.Parse(time.RFC3339, response.Credentials.Expiration)
	if err != nil {
		return nil, fmt.Errorf("failed to parse expiration: %w", err)
	}

	// Verify identity with new credentials
	LogVerbose("Verifying identity...")
	identity, err := getCallerIdentity(&Credentials{
		AccessKeyID:     response.Credentials.AccessKeyID,
		SecretAccessKey: response.Credentials.SecretAccessKey,
		SessionToken:    response.Credentials.SessionToken,
	}, region)
	if err != nil {
		return nil, fmt.Errorf("failed to verify identity: %w", err)
	}

	return &AuthResult{
		Identity: identity,
		Credentials: &Credentials{
			AccessKeyID:     response.Credentials.AccessKeyID,
			SecretAccessKey: response.Credentials.SecretAccessKey,
			SessionToken:    response.Credentials.SessionToken,
		},
		ExpirationEpoch: expiration.Unix(),
		Region:          region,
	}, nil
}

// AuthIAM authenticates using IAM credentials (no MFA)
func AuthIAM(cfg *Config, profileName string, profile ProfileConfig) (*AuthResult, error) {
	LogVerbose("Verifying AWS identity for profile '%s'...", profileName)

	// Get region
	region := profile.Region
	if region == "" {
		region = cfg.Defaults.Region
	}

	// Unset env credentials and use profile
	env := os.Environ()
	env = removeEnv(env, "AWS_ACCESS_KEY_ID")
	env = removeEnv(env, "AWS_SECRET_ACCESS_KEY")
	env = removeEnv(env, "AWS_SESSION_TOKEN")

	cmd := exec.Command("aws", "sts", "get-caller-identity", "--profile", profileName)
	cmd.Env = env

	output, err := cmd.Output()
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			return nil, fmt.Errorf("AWS error: %s", string(exitErr.Stderr))
		}
		return nil, fmt.Errorf("failed to verify identity: %w", err)
	}

	var identity Identity
	if err := json.Unmarshal(output, &identity); err != nil {
		return nil, fmt.Errorf("failed to parse identity: %w", err)
	}

	// Estimate expiration (4 hours for assumed roles)
	expirationEpoch := time.Now().Unix() + 4*3600

	return &AuthResult{
		Identity:        &identity,
		Credentials:     nil, // IAM profiles don't need env var credentials
		ExpirationEpoch: expirationEpoch,
		Region:          region,
	}, nil
}

// Helper functions

func getAWSCredentials(profile string) (accessKey, secretKey string, err error) {
	homeDir, _ := os.UserHomeDir()
	credsFile := homeDir + "/.aws/credentials"

	data, err := os.ReadFile(credsFile)
	if err != nil {
		return "", "", fmt.Errorf("failed to read ~/.aws/credentials: %w", err)
	}

	content := string(data)
	profileSection := fmt.Sprintf("[%s]", profile)
	inProfile := false

	for _, line := range strings.Split(content, "\n") {
		line = strings.TrimSpace(line)

		if strings.HasPrefix(line, "[") {
			inProfile = line == profileSection
			continue
		}

		if !inProfile {
			continue
		}

		if strings.HasPrefix(line, "aws_access_key_id") {
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 {
				accessKey = strings.TrimSpace(parts[1])
			}
		} else if strings.HasPrefix(line, "aws_secret_access_key") {
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 {
				secretKey = strings.TrimSpace(parts[1])
			}
		}
	}

	if accessKey == "" || secretKey == "" {
		return "", "", fmt.Errorf("could not find credentials for profile [%s]", profile)
	}

	return accessKey, secretKey, nil
}

func getMFASerial(profile string) (string, error) {
	homeDir, _ := os.UserHomeDir()
	configFile := homeDir + "/.aws/config"

	data, err := os.ReadFile(configFile)
	if err != nil {
		return "", fmt.Errorf("failed to read ~/.aws/config: %w", err)
	}

	content := string(data)
	profileSection := fmt.Sprintf("[profile %s]", profile)
	inProfile := false

	for _, line := range strings.Split(content, "\n") {
		line = strings.TrimSpace(line)

		if strings.HasPrefix(line, "[") {
			inProfile = line == profileSection
			continue
		}

		if !inProfile {
			continue
		}

		if strings.HasPrefix(line, "mfa_serial") {
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 {
				return strings.TrimSpace(parts[1]), nil
			}
		}
	}

	return "", fmt.Errorf("could not find mfa_serial for profile [%s]", profile)
}

func getCallerIdentity(creds *Credentials, region string) (*Identity, error) {
	env := os.Environ()
	env = setEnv(env, "AWS_ACCESS_KEY_ID", creds.AccessKeyID)
	env = setEnv(env, "AWS_SECRET_ACCESS_KEY", creds.SecretAccessKey)
	if creds.SessionToken != "" {
		env = setEnv(env, "AWS_SESSION_TOKEN", creds.SessionToken)
	}
	env = setEnv(env, "AWS_DEFAULT_REGION", region)

	cmd := exec.Command("aws", "sts", "get-caller-identity")
	cmd.Env = env

	output, err := cmd.Output()
	if err != nil {
		return nil, err
	}

	var identity Identity
	if err := json.Unmarshal(output, &identity); err != nil {
		return nil, err
	}

	return &identity, nil
}

func setEnv(env []string, key, value string) []string {
	prefix := key + "="
	for i, e := range env {
		if strings.HasPrefix(e, prefix) {
			env[i] = prefix + value
			return env
		}
	}
	return append(env, prefix+value)
}

func removeEnv(env []string, key string) []string {
	prefix := key + "="
	result := make([]string, 0, len(env))
	for _, e := range env {
		if !strings.HasPrefix(e, prefix) {
			result = append(result, e)
		}
	}
	return result
}
