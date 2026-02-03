package main

import (
	"os"
	"path/filepath"
	"time"

	"gopkg.in/yaml.v3"
)

// Config represents the aws-login configuration
type Config struct {
	Defaults  DefaultsConfig           `yaml:"defaults"`
	Cache     CacheConfig              `yaml:"cache"`
	Starship  StarshipConfig           `yaml:"starship"`
	Bitwarden BitwardenConfig          `yaml:"bitwarden"`
	Profiles  map[string]ProfileConfig `yaml:"profiles"`
}

// DefaultsConfig holds default settings
type DefaultsConfig struct {
	Region         string        `yaml:"region"`
	CacheTTLBuffer time.Duration `yaml:"cache_ttl_buffer"`
}

// CacheConfig holds cache settings
type CacheConfig struct {
	Directory string `yaml:"directory"`
}

// StarshipConfig holds starship integration settings
type StarshipConfig struct {
	Enabled     bool   `yaml:"enabled"`
	TimerPrefix string `yaml:"timer_prefix"`
}

// BitwardenConfig holds bitwarden integration settings
type BitwardenConfig struct {
	Enabled bool `yaml:"enabled"`
}

// ProfileConfig holds a single profile's configuration
type ProfileConfig struct {
	Type            string        `yaml:"type"`
	Description     string        `yaml:"description"`
	BitwardenItem   string        `yaml:"bitwarden_item"`
	MFASerial       string        `yaml:"mfa_serial"`
	SessionDuration time.Duration `yaml:"session_duration"`
	Region          string        `yaml:"region"`
}

// LoadConfig loads the configuration from ~/.config/aws-login/config.yaml
func LoadConfig() (*Config, error) {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return nil, err
	}

	configPath := filepath.Join(homeDir, ".config", "aws-login", "config.yaml")

	data, err := os.ReadFile(configPath)
	if err != nil {
		if os.IsNotExist(err) {
			return defaultConfig(), nil
		}
		return nil, err
	}

	cfg := defaultConfig()
	if err := yaml.Unmarshal(data, cfg); err != nil {
		return nil, err
	}

	// Expand ~ in cache directory
	if cfg.Cache.Directory != "" && cfg.Cache.Directory[0] == '~' {
		cfg.Cache.Directory = filepath.Join(homeDir, cfg.Cache.Directory[1:])
	}

	return cfg, nil
}

// defaultConfig returns the default configuration
func defaultConfig() *Config {
	homeDir, _ := os.UserHomeDir()
	return &Config{
		Defaults: DefaultsConfig{
			Region:         "eu-central-1",
			CacheTTLBuffer: 5 * time.Minute,
		},
		Cache: CacheConfig{
			Directory: filepath.Join(homeDir, ".config", "aws-login", "cache"),
		},
		Starship: StarshipConfig{
			Enabled:     true,
			TimerPrefix: "aws-session-",
		},
		Bitwarden: BitwardenConfig{
			Enabled: true,
		},
		Profiles: make(map[string]ProfileConfig),
	}
}

// UnmarshalYAML implements custom unmarshaling for ProfileConfig to handle duration parsing
func (d *DefaultsConfig) UnmarshalYAML(value *yaml.Node) error {
	type rawDefaults struct {
		Region         string `yaml:"region"`
		CacheTTLBuffer int    `yaml:"cache_ttl_buffer"`
	}

	var raw rawDefaults
	if err := value.Decode(&raw); err != nil {
		return err
	}

	d.Region = raw.Region
	d.CacheTTLBuffer = time.Duration(raw.CacheTTLBuffer) * time.Second
	return nil
}

// UnmarshalYAML implements custom unmarshaling for ProfileConfig to handle duration parsing
func (p *ProfileConfig) UnmarshalYAML(value *yaml.Node) error {
	type rawProfile struct {
		Type            string `yaml:"type"`
		Description     string `yaml:"description"`
		BitwardenItem   string `yaml:"bitwarden_item"`
		MFASerial       string `yaml:"mfa_serial"`
		SessionDuration string `yaml:"session_duration"`
		Region          string `yaml:"region"`
	}

	var raw rawProfile
	if err := value.Decode(&raw); err != nil {
		return err
	}

	p.Type = raw.Type
	p.Description = raw.Description
	p.BitwardenItem = raw.BitwardenItem
	p.MFASerial = raw.MFASerial
	p.Region = raw.Region

	// Parse duration (e.g., "12h", "4h")
	if raw.SessionDuration != "" {
		dur, err := time.ParseDuration(raw.SessionDuration)
		if err == nil {
			p.SessionDuration = dur
		}
	}
	if p.SessionDuration == 0 {
		p.SessionDuration = 12 * time.Hour
	}

	return nil
}
