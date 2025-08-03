# Enable OpenCode Caching and Logging

## 🎯 Purpose
This task explains how to actually use the cache and logs directories with OpenCode, since they're not automatically used by default.

## 🔍 Current Reality

**OpenCode Native Behavior:**
- OpenCode loads context fresh each session
- No persistent caching between sessions
- No automatic logging to files
- Context is managed in memory during sessions

**Our AgentOS Enhancement:**
- Designed advanced caching and logging system
- Created directory structure and configuration
- But needs manual activation to work with OpenCode

## 🚀 Practical Implementation Options

### **Option 1: Manual Context Caching (Immediate)**

Create a simple caching system that agents can use:

```bash
# Cache frequently used context manually
@opencode-configurator Create context cache for current project type
```

This would:
1. Identify frequently loaded context (BMad methodology, coding standards)
2. Create cached versions in the cache directory
3. Provide quick access commands for agents

### **Option 2: Session Logging (Immediate)**

Enable session logging for performance tracking:

```bash
# Start session with logging
@metrics-analyst Start performance logging for this session
```

This would:
1. Track context loading times
2. Monitor agent response times
3. Log quality gate results
4. Save metrics to logs directory

### **Option 3: Enhanced Agent Behaviors (Medium-term)**

Modify agent behaviors to use caching:

```bash
# Agents check cache before loading context
@bmad-master Load BMad methodology (check cache first)
```

This would:
1. Check cache directory for existing context
2. Load from cache if available and fresh
3. Load from source and cache if not available
4. Log cache hit/miss statistics

## 🔧 **Immediate Actions You Can Take**

### **1. Enable Basic Logging**

Create a simple logging mechanism:

```bash
# Create a session log
echo "OpenCode Session Started: $(date)" >> ~/.config/opencode/logs/session.log

# Log agent usage
echo "Agent Used: @bmad-master - $(date)" >> ~/.config/opencode/logs/agent-usage.log
```

### **2. Manual Context Caching**

Cache frequently used context:

```bash
# Cache BMad methodology
cp ~/.config/opencode/standards/bmad/methodology-lite.md ~/.config/opencode/cache/bmad-methodology-cached.md

# Cache coding standards
cp ~/.config/opencode/standards/coding/style-guides.md ~/.config/opencode/cache/coding-standards-cached.md
```

### **3. Performance Tracking**

Start tracking basic metrics:

```bash
# Track session start time
echo "Session Start: $(date +%s)" > ~/.config/opencode/metrics/session-start.txt

# Track context loading (manual timing)
time @context-primer Analyze this project
```

## 🤖 **Agent-Assisted Implementation**

Let me create agents that can actually use these directories:

### **Cache Management Agent Commands**

```bash
# Check cache status
@opencode-configurator Show cache directory status and usage

# Manually populate cache
@opencode-configurator Populate cache with frequently used context

# Clear cache
@opencode-configurator Clear and rebuild context cache
```

### **Logging Agent Commands**

```bash
# Start session logging
@metrics-analyst Start logging for this OpenCode session

# Show session metrics
@metrics-analyst Show current session performance metrics

# Generate session report
@metrics-analyst Generate session performance report
```

## 📊 **What Actually Gets Used**

### **OpenCode Native Features:**
1. **Instructions loading** from `opencode.json`
2. **Agent definitions** from `agent/` directory
3. **MCP server connections** for external tools
4. **Session-based context** loaded per conversation

### **Our Enhancement Opportunities:**
1. **Manual caching** of frequently used context
2. **Session logging** for performance tracking
3. **Metrics collection** for optimization
4. **Agent coordination** tracking

## 🎯 **Realistic Implementation Plan**

### **Phase 1: Manual Usage (This Week)**
1. **Create cache helpers** - Scripts to manually cache context
2. **Enable session logging** - Simple logging of agent usage
3. **Basic metrics** - Track session performance manually

### **Phase 2: Agent Integration (Next Month)**
1. **Cache-aware agents** - Agents that check cache first
2. **Automatic logging** - Agents log their performance
3. **Metrics collection** - Automated performance tracking

### **Phase 3: Full Integration (Future)**
1. **OpenCode plugin** - If OpenCode adds plugin support
2. **MCP server** - Custom MCP server for caching/logging
3. **External tools** - Separate tools that integrate with OpenCode

## 🔧 **Immediate Practical Steps**

### **1. Create Cache Helper Script**
```bash
# Create a simple cache management script
cat > ~/.config/opencode/cache/cache-helper.sh << 'EOF'
#!/bin/bash
# Simple cache management for OpenCode

case "$1" in
  "populate")
    echo "Populating cache with common context..."
    cp ~/.config/opencode/standards/bmad/methodology-lite.md ~/.config/opencode/cache/
    cp ~/.config/opencode/standards/coding/style-guides.md ~/.config/opencode/cache/
    echo "Cache populated: $(date)" >> ~/.config/opencode/logs/cache.log
    ;;
  "clear")
    echo "Clearing cache..."
    rm -f ~/.config/opencode/cache/*.md
    echo "Cache cleared: $(date)" >> ~/.config/opencode/logs/cache.log
    ;;
  "status")
    echo "Cache status:"
    ls -la ~/.config/opencode/cache/
    ;;
esac
EOF

chmod +x ~/.config/opencode/cache/cache-helper.sh
```

### **2. Create Session Logger**
```bash
# Create session logging helper
cat > ~/.config/opencode/logs/session-logger.sh << 'EOF'
#!/bin/bash
# Simple session logging for OpenCode

LOG_FILE="$HOME/.config/opencode/logs/session.log"

case "$1" in
  "start")
    echo "=== OpenCode Session Started: $(date) ===" >> "$LOG_FILE"
    echo "Session ID: $$" >> "$LOG_FILE"
    ;;
  "agent")
    echo "Agent Used: $2 - $(date)" >> "$LOG_FILE"
    ;;
  "end")
    echo "=== Session Ended: $(date) ===" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"
    ;;
esac
EOF

chmod +x ~/.config/opencode/logs/session-logger.sh
```

### **3. Use the Helpers**
```bash
# Start a session with logging
~/.config/opencode/logs/session-logger.sh start

# Populate cache
~/.config/opencode/cache/cache-helper.sh populate

# Check cache status
~/.config/opencode/cache/cache-helper.sh status

# Log agent usage (manual)
~/.config/opencode/logs/session-logger.sh agent "bmad-master"
```

## 💡 **Key Insight**

The cache and logs directories are **infrastructure for future enhancements**, not currently active OpenCode features. They represent our **vision for advanced context optimization** but need manual activation or custom implementation to actually work.

**Bottom Line:** 
- ✅ **Directories created** - Ready for use
- ✅ **Configuration designed** - Comprehensive setup
- ⚠️ **Manual activation needed** - Not automatic with OpenCode
- 🚀 **Future enhancement ready** - Foundation for advanced features

Would you like me to implement the practical helpers above so you can start using these directories immediately?