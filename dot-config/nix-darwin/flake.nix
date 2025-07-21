{
  description = "nix-darwin flake for Mac";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    nix-darwin.url = "github:nix-darwin/nix-darwin/master";
    nix-darwin.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = inputs@{ self, nix-darwin, nixpkgs }:
  let
    configuration = { pkgs, ... }: {
      # List packages installed in system profile. To search by name, run:
      # $ nix-env -qaP | bat
      environment.systemPackages =
        [ 
          pkgs.vim
          pkgs.direnv
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
        universalaccess.closeViewScrollWheelToggle = true;
      };

      # Homebrew configuration.
      homebrew.enable = true;
      homebrew.taps = [
        "felixkratz/formulae"
        "nikitabobko/tap"
        "oven-sh/bun"
        "yakitrak/yakitrak"
      	"sst/tap"
      ];
      homebrew.casks = [
	      "raycast"
        "rectangle"
        "font-sketchybar-app-font"
        "font-sf-pro"
        "font-jetbrains-mono"
        "font-jetbrains-mono-nerd-font"
        "aerospace" 
        "obsidian" 
        "steermouse"
        "finicky"
        "stats"
        "karabiner-elements" 
        "warp" 
        "ghostty"
        "chatgpt"
        "claude" 
        "vivaldi"
        "discord"
        "spotify"
        "the-unarchiver" 
        "appcleaner"
      	"betterdisplay"
      ];
      homebrew.brews = [
	      "stow" 
        "git"
        "starship" 
        "coreutils"
        "gnu-sed"
        "grep" 
        "wget"
        "curl" 
        "fzf"
        "ripgrep"
        "mas"
        "sketchybar"
        "zinit"
        "zoxide" 
        "diff-so-fancy"
        "jq" 
        "navi" 
        "yamllint" 
        "iproute2mac"
        "tldr" 
        "as-tree"
        "bat"
        "tree" 
        "eza"
        "yazi" 
        "atuin"
        "sshs" 
        "age"
        "btop" 
        "git-delta"
        "thefuck"
        "p7zip"
        "poppler"
        "fd"
        "node"
        "oven-sh/bun/bun"
        "go"
        "rust"
        "openjdk"
        "lua"
        "git-filter-repo"
        "gh"
        "glab"
        "git-lfs"
        "lazygit"
        "docker"
        "docker-compose"
        "docker-credential-helper"
        "colima"
        "lazydocker"
        "ctop"
        "kubernetes-cli"
        "kubectx"
        "k9s"
        "helm"
        "kind"
        "awscli"
        "azure-cli"
        "terraform"
        "postgresql@14"
        "mysql"
        "jq"
        "yq"
        "httpie"
        "uv"
        "pyenv"
        "neovim"
        "sops"
        "opencode"
        "zellij"
        "yakitrak/yakitrak/obsidian-cli"
        "duti"
      ];
      homebrew.masApps = 
        { 
          "Amphetamine" = 937984704;
          "Quick Sticky Notes" = 6740142714;
          "Microsoft Outlook" = 985367838;
          "Mark And Scribble" = 1635403801;
          "Hidden Bar" = 1452453066;
          "Bitwarden"  = 1352778147;
        };
      system.primaryUser = "mbastakis";
    };
  in
  {
    # Build darwin flake using:
    # $ darwin-rebuild build --flake .#simple
    darwinConfigurations."simple" = nix-darwin.lib.darwinSystem {
      modules = [ configuration ];
    };
  };
}
