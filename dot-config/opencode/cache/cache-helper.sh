#!/bin/bash
# OpenCode Cache Management Helper
# Usage: ./cache-helper.sh [populate|clear|status|check]

CACHE_DIR="$HOME/.config/opencode/cache"
LOG_FILE="$HOME/.config/opencode/logs/cache.log"

# Ensure log file exists
mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"

case "$1" in
  "populate")
    echo "🔄 Populating OpenCode cache with common context..."
    
    # Cache BMad methodology (lite version for performance)
    if [ -f "$HOME/.config/opencode/standards/bmad/methodology-lite.md" ]; then
      cp "$HOME/.config/opencode/standards/bmad/methodology-lite.md" "$CACHE_DIR/bmad-methodology-cached.md"
      echo "✅ Cached BMad methodology"
    fi
    
    # Cache coding standards
    if [ -f "$HOME/.config/opencode/standards/coding/style-guides.md" ]; then
      cp "$HOME/.config/opencode/standards/coding/style-guides.md" "$CACHE_DIR/coding-standards-cached.md"
      echo "✅ Cached coding standards"
    fi
    
    # Cache security standards
    if [ -f "$HOME/.config/opencode/standards/security/secure-coding.md" ]; then
      cp "$HOME/.config/opencode/standards/security/secure-coding.md" "$CACHE_DIR/security-standards-cached.md"
      echo "✅ Cached security standards"
    fi
    
    # Cache current project patterns (auto-detect)
    if [ -f "package.json" ]; then
      if [ -f "$HOME/.config/opencode/products/web-apps/patterns.md" ]; then
        cp "$HOME/.config/opencode/products/web-apps/patterns.md" "$CACHE_DIR/project-patterns-cached.md"
        echo "✅ Cached web app patterns"
      fi
    elif [ -d "api" ] || [ -f "openapi.yaml" ]; then
      if [ -f "$HOME/.config/opencode/products/apis/patterns.md" ]; then
        cp "$HOME/.config/opencode/products/apis/patterns.md" "$CACHE_DIR/project-patterns-cached.md"
        echo "✅ Cached API patterns"
      fi
    fi
    
    # Log cache population
    echo "Cache populated: $(date) - $(ls "$CACHE_DIR"/*.md 2>/dev/null | wc -l) files cached" >> "$LOG_FILE"
    echo "🎉 Cache population complete!"
    ;;
    
  "clear")
    echo "🧹 Clearing OpenCode cache..."
    rm -f "$CACHE_DIR"/*.md
    rm -f "$CACHE_DIR"/*.cache
    echo "Cache cleared: $(date)" >> "$LOG_FILE"
    echo "✅ Cache cleared!"
    ;;
    
  "status")
    echo "📊 OpenCode Cache Status:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Count cached files
    CACHED_FILES=$(ls "$CACHE_DIR"/*.md 2>/dev/null | wc -l)
    echo "📁 Cached files: $CACHED_FILES"
    
    # Show cache size
    if command -v du >/dev/null 2>&1; then
      CACHE_SIZE=$(du -sh "$CACHE_DIR" 2>/dev/null | cut -f1)
      echo "💾 Cache size: $CACHE_SIZE"
    fi
    
    # List cached files
    if [ "$CACHED_FILES" -gt 0 ]; then
      echo ""
      echo "📋 Cached files:"
      ls -la "$CACHE_DIR"/*.md 2>/dev/null | while read -r line; do
        filename=$(echo "$line" | awk '{print $9}' | xargs basename)
        size=$(echo "$line" | awk '{print $5}')
        date=$(echo "$line" | awk '{print $6, $7, $8}')
        echo "  • $filename ($size bytes) - $date"
      done
    fi
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ;;
    
  "check")
    # Check if specific context is cached
    CONTEXT="$2"
    if [ -z "$CONTEXT" ]; then
      echo "Usage: $0 check [bmad|coding|security|patterns]"
      exit 1
    fi
    
    case "$CONTEXT" in
      "bmad")
        if [ -f "$CACHE_DIR/bmad-methodology-cached.md" ]; then
          echo "✅ BMad methodology is cached"
          exit 0
        else
          echo "❌ BMad methodology not cached"
          exit 1
        fi
        ;;
      "coding")
        if [ -f "$CACHE_DIR/coding-standards-cached.md" ]; then
          echo "✅ Coding standards are cached"
          exit 0
        else
          echo "❌ Coding standards not cached"
          exit 1
        fi
        ;;
      "security")
        if [ -f "$CACHE_DIR/security-standards-cached.md" ]; then
          echo "✅ Security standards are cached"
          exit 0
        else
          echo "❌ Security standards not cached"
          exit 1
        fi
        ;;
      "patterns")
        if [ -f "$CACHE_DIR/project-patterns-cached.md" ]; then
          echo "✅ Project patterns are cached"
          exit 0
        else
          echo "❌ Project patterns not cached"
          exit 1
        fi
        ;;
      *)
        echo "❌ Unknown context: $CONTEXT"
        exit 1
        ;;
    esac
    ;;
    
  *)
    echo "OpenCode Cache Management Helper"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  populate  - Cache common context files for faster access"
    echo "  clear     - Clear all cached files"
    echo "  status    - Show cache status and contents"
    echo "  check     - Check if specific context is cached"
    echo ""
    echo "Examples:"
    echo "  $0 populate              # Cache common files"
    echo "  $0 status                # Show cache status"
    echo "  $0 check bmad            # Check if BMad is cached"
    echo "  $0 clear                 # Clear cache"
    ;;
esac