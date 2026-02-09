
let
  # Inconsistent spacing
  myPackages=[
    pkgs.git
    pkgs.vim
    pkgs.curl
  ];

  # Unused variable
  unusedHelper = x: x * 2;

  # Very long line
  buildEnv=pkgs.buildEnv{name="my-env";paths=myPackages;pathsToLink=["/bin" "/share" "/lib" "/include"];ignoreCollisions=false;};

  # Inconsistent formatting
  myConfig = {
    enable=true;
    extraConfig="set -g mouse on";
    plugins  =  [
      "plugin1"

      "plugin2"

    ];
  };

in
{
  # Missing spacing
  home.packages=myPackages++[
    pkgs.ripgrep
    pkgs.fd
  ];

  programs.git={
    enable=true;
    userName="John Doe";
    userEmail  =  "john@example.com";
    extraConfig={
      core={editor="nvim";};
      init={defaultBranch="main";};
    };
  };

  # Inconsistent attribute formatting
  home.file.".config/test".source=./test;
  home.file.".config/test2".text = ''
    line1
    line2
  '';

  # Missing semicolon at end
  home.stateVersion="23.05"
};
