# Neovim Test Files

Test files for LSP, formatting, and linting configuration.

## Directory Structure

```tree
test/
├── web/                    # Web development (HTML, CSS, JS, TS)
│   ├── index.html
│   ├── style.css
│   ├── index.js
│   ├── main.ts
│   ├── package.json        # Node.js project with ESLint
│   ├── eslint.config.js    # ESLint v9+ config
│   ├── .stylelintrc.json   # Stylelint config
│   ├── .htmlhintrc         # HTMLHint config
│   └── README.md
│
├── Other language files...
└── README.md (this file)
```

## Web Development Setup

The `web/` directory contains a complete web development setup with all configs.

### Quick Start

```bash
# Install dependencies
cd test/web
npm install

# Test in Neovim
nvim test/web/index.html
nvim test/web/index.js
nvim test/web/main.ts
```

See [web/README.md](web/README.md) for details.

## Important: ESLint Requirement

The ESLint LSP server needs ESLint installed locally in the project:

```bash
cd test/web
npm install
```

Without this, you'll see: `[lspconfig] Unable to find ESLint library.`

This is now set up in the web/ directory! ✅
