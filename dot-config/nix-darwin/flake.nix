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
        pkgs.claude-code
        pkgs.gemini-cli
        pkgs.glow
        pkgs.nushell
        pkgs.sshs
        pkgs.vim
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
        "linear-linear"
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
        "oven-sh/bun/bun"
        "carapace"
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
        "gnupg"
        "go"
        "go-task"
        "graphicsmagick"
        "grep"
        "hadolint"
        "helm"
        "httpie"
        "imagemagick"
        "iproute2mac"
        "jj"
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
        "yakitrak/yakitrak/obsidian-cli"
        "ollama"
        "opencode"
        "openjdk"
        "opentofu"
        "p7zip"
        "pandoc"
        "parallel-disk-usage"
        "poppler"
        "postgresql@17"
        "pyenv"
        "qrencode"
        "ripgrep"
        "rust"
        "serie"
        "shellcheck"
        "sketchybar"
        "sops"
        "sox"
        "sshs"
        "starship"
        "statix"
        "stow"
        "tealdeer"
        "tfenv"
        "thefuck"
        "tree"
        "tree-sitter-cli"
        "uv"
        "watch"
        "wget"
        "whisper-cpp"
        "yamllint"
        "yazi"
        "yq"
        "zellij"
        "zinit"
        "zoxide"
      ];
      homebrew.masApps = {
        "Amphetamine" = 937984704;
        "Bitwarden" = 1352778147;
        "Hidden Bar" = 1452453066;
        "Mark And Scribble" = 1635403801;
        "Microsoft Outlook" = 985367838;
        "Quick Sticky Notes" = 6740142714;
        "Say No to Notch" = 1639306886;
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
