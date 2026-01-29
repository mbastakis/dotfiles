{
  description = "nix-darwin flake for Mac";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    nix-darwin.url = "github:nix-darwin/nix-darwin/master";
    nix-darwin.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = {
    self,
    nix-darwin,
    nixpkgs,
  }: let
    configuration = {pkgs, ...}: {
      # List packages installed in system profile. To search by name, run:
      # $ nix-env -qaP | bat
      environment.systemPackages = [
        pkgs.vim
        pkgs.sshs
        pkgs.glow
        pkgs.nushell
        pkgs.carapace
        pkgs.claude-code
        pkgs.gemini-cli
        pkgs.vsce
      ];
      nixpkgs.config.allowUnfree = true;
      # Necessary for using flakes on this system.
      nix.settings.experimental-features = "nix-command flakes";
      programs.zsh.enable = true;

      # Set Git commit hash for darwin-version.
      system.configurationRevision = self.rev or self.dirtyRev or null;

      # Used for backwards compatibility, please read the changelog before changing.
      # $ darwin-rebuild changelog
      system.stateVersion = 6;

      # The platform the configuration will be used on.
      nixpkgs.hostPlatform = "aarch64-darwin";

      # System configuration.
      system.defaults = {
        dock.autohide = true;
        dock.orientation = "right";
        dock.mru-spaces = false;
        finder.AppleShowAllExtensions = true;
        finder.FXPreferredViewStyle = "clmv";
        loginwindow.LoginwindowText = "mbastakis";
        screencapture.location = "~/Pictures/screenshots";
        screensaver.askForPasswordDelay = 10;
        NSGlobalDomain.AppleICUForce24HourTime = true;
        NSGlobalDomain.AppleShowAllExtensions = true;
        NSGlobalDomain.AppleShowAllFiles = true;
        NSGlobalDomain.NSAutomaticCapitalizationEnabled = false;
        controlcenter.BatteryShowPercentage = true;
      };

      # Homebrew configuration.
      homebrew.enable = true;
      homebrew.taps = [
        "felixkratz/formulae"
        "nikitabobko/tap"
        "oven-sh/bun"
        "yakitrak/yakitrak"
        "sst/tap"
        "browsh-org/homebrew-browsh"
      ];
      homebrew.casks = [
        "aerospace"
        "appcleaner"
        "atuin-desktop"
        "betterdisplay"
        "chatgpt"
        "claude"
        "discord"
        "finicky"
        "font-jetbrains-mono"
        "font-jetbrains-mono-nerd-font"
        "font-sf-pro"
        "font-sketchybar-app-font"
        "ghostty"
        "kap"
        "karabiner-elements"
        "keyclu"
        "obsidian"
        "opencode-desktop"
        "raycast"
        "rectangle"
        "soundsource"
        "spotify"
        "stats"
        "steermouse"
        "the-unarchiver"
        "unity-hub"
        "vivaldi"
        "warp"
      ];
      homebrew.brews = [
        "age"
        "argocd"
        "as-tree"
        "atuin"
        "awscli"
        "azure-cli"
        "bagels"
        "bat"
        "bitwarden-cli"
        "browsh"
        "btop"
        "chafa"
        "colima"
        "coreutils"
        "ctop"
        "curl"
        "diff-so-fancy"
        "direnv"
        "docker"
        "docker-buildx"
        "docker-completion"
        "docker-compose"
        "docker-credential-helper"
        "dockerfmt"
        "dua-cli"
        "duti"
        "eza"
        "fabric-ai"
        "fd"
        "ffmpeg"
        "fzf"
        "gh"
        "git"
        "git-delta"
        "git-filter-repo"
        "git-lfs"
        "glab"
        "gnu-sed"
        "go"
        "graphicsmagick"
        "grep"
        "helm"
        "httpie"
        "imagemagick"
        "iproute2mac"
        "jj"
        "jq"
        "jq"
        "k9s"
        "kind"
        "kubectx"
        "kubernetes-cli"
        "lazydocker"
        "lazygit"
        "lazyjj"
        "lua"
        "mas"
        "mise"
        "mysql"
        "navi"
        "neovim"
        "nixfmt"
        "node"
        "ollama"
        "opencode"
        "openjdk"
        "opentofu"
        "oven-sh/bun/bun"
        "p7zip"
        "pandoc"
        "parallel-disk-usage"
        "poppler"
        "postgresql@17"
        "pyenv"
        "ripgrep"
        "rust"
        "serie"
        "sketchybar"
        "sops"
        "sox"
        "sshs"
        "starship"
        "statix"
        "stow"
        "tealdeer"
        "thefuck"
        "tree"
        "tree-sitter-cli"
        "uv"
        "watch"
        "wget"
        "whisper-cpp"
        "yakitrak/yakitrak/obsidian-cli"
        "yamllint"
        "yazi"
        "yq"
        "zellij"
        "zinit"
        "zoxide"
      ];
      homebrew.masApps = {
        "Amphetamine" = 937984704;
        "Quick Sticky Notes" = 6740142714;
        "Microsoft Outlook" = 985367838;
        "Mark And Scribble" = 1635403801;
        "Hidden Bar" = 1452453066;
        "Bitwarden" = 1352778147;
      };
      system.primaryUser = "mbastakis";
    };
  in {
    # Build darwin flake using:
    # $ darwin-rebuild build --flake .#simple
    darwinConfigurations."simple" = nix-darwin.lib.darwinSystem {
      modules = [configuration];
    };
  };
}
