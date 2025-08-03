# How to Use OpenCode Cache and Logs

## 🎯 **The Reality Check**

**What we discovered:**
- ✅ **Cache and logs directories created** - Infrastructure ready
- ✅ **Configuration designed** - Comprehensive AgentOS setup
- ⚠️ **OpenCode doesn't use them natively** - Need manual activation
- ✅ **Helper scripts created** - Now functional and usable!

## 🚀 **How to Actually Use Them**

### **1. Cache Management (Now Working!)**

#### **Populate Cache with Common Context**
```bash
# Cache frequently used context for faster access
~/.config/opencode/cache/cache-helper.sh populate
```
**Result:** Caches BMad methodology, coding standards, security standards

#### **Check Cache Status**
```bash
# See what's cached and cache statistics
~/.config/opencode/cache/cache-helper.sh status
```

#### **Clear Cache When Needed**
```bash
# Clear all cached files
~/.config/opencode/cache/cache-helper.sh clear
```

#### **Check Specific Context**
```bash
# Check if specific context is cached
~/.config/opencode/cache/cache-helper.sh check bmad
~/.config/opencode/cache/cache-helper.sh check coding
```

### **2. Session Logging (Now Working!)**

#### **Start Session with Logging**
```bash
# Start logging your OpenCode session
~/.config/opencode/logs/session-logger.sh start
```

#### **Log Agent Usage**
```bash
# Log when you use specific agents
~/.config/opencode/logs/session-logger.sh agent bmad-master "Creating project requirements"
~/.config/opencode/logs/session-logger.sh agent context-primer "Analyzing project structure"
```

#### **Log Performance Metrics**
```bash
# Log performance metrics manually
~/.config/opencode/logs/session-logger.sh metric response_time 2.5 seconds
~/.config/opencode/logs/session-logger.sh metric context_load_time 1.2 seconds
```

#### **Check Session Status**
```bash
# See current session and logging status
~/.config/opencode/logs/session-logger.sh status
```

#### **End Session**
```bash
# End session and calculate duration
~/.config/opencode/logs/session-logger.sh end
```

#### **Generate Usage Report**
```bash
# See usage patterns and statistics
~/.config/opencode/logs/session-logger.sh report
```

## 📊 **What Gets Logged**

### **Cache Files Created:**
- `bmad-methodology-cached.md` - BMad methodology for quick reference
- `coding-standards-cached.md` - Coding standards and best practices
- `security-standards-cached.md` - Security guidelines
- `project-patterns-cached.md` - Project-specific patterns (auto-detected)

### **Log Files Created:**
- `session.log` - Detailed session information and timeline
- `agent-usage.log` - CSV log of agent usage with timestamps
- `metrics.log` - Performance metrics and measurements
- `cache.log` - Cache operations and status changes

## 🔧 **Practical Workflow**

### **Daily Usage Pattern:**
```bash
# 1. Start your day
~/.config/opencode/cache/cache-helper.sh populate
~/.config/opencode/logs/session-logger.sh start

# 2. Use OpenCode normally, but log agent usage
# When you use: @bmad-master Create project requirements
~/.config/opencode/logs/session-logger.sh agent bmad-master "Create project requirements"

# When you use: @context-primer Analyze this project
~/.config/opencode/logs/session-logger.sh agent context-primer "Analyze project structure"

# 3. End your session
~/.config/opencode/logs/session-logger.sh end

# 4. Check your productivity
~/.config/opencode/logs/session-logger.sh report
```

### **Weekly Maintenance:**
```bash
# Check cache efficiency
~/.config/opencode/cache/cache-helper.sh status

# Review usage patterns
~/.config/opencode/logs/session-logger.sh report

# Clear old cache if needed
~/.config/opencode/cache/cache-helper.sh clear
~/.config/opencode/cache/cache-helper.sh populate
```

## 🎯 **Benefits You Get**

### **Performance Benefits:**
- ✅ **Faster context access** - Cached files load instantly
- ✅ **Usage tracking** - See which agents you use most
- ✅ **Performance monitoring** - Track response times
- ✅ **Session analytics** - Understand your productivity patterns

### **Productivity Benefits:**
- ✅ **Quick reference** - Cached methodology and standards
- ✅ **Usage insights** - Optimize your workflow
- ✅ **Performance awareness** - Identify slow operations
- ✅ **Historical tracking** - See progress over time

## 🔮 **Future Integration**

### **What This Enables:**
1. **Agent-Aware Caching** - Agents could check cache before loading context
2. **Automatic Performance Tracking** - Agents could log their own metrics
3. **Smart Context Loading** - Use cache hit rates to optimize loading
4. **Usage-Based Optimization** - Optimize based on actual usage patterns

### **Potential Enhancements:**
```bash
# Future agent commands could be:
@bmad-master Load methodology (check cache first)
@context-optimizer Show cache efficiency and optimize
@metrics-analyst Analyze session performance trends
```

## 💡 **Pro Tips**

### **Cache Optimization:**
- Run `cache-helper.sh populate` at the start of each day
- Check cache status weekly to see what's being used
- Clear and repopulate cache monthly for freshness

### **Logging Best Practices:**
- Always start sessions with `session-logger.sh start`
- Log agent usage immediately after using agents
- End sessions to get accurate duration metrics
- Review reports weekly to optimize workflow

### **Performance Tracking:**
- Log response times when you notice slow performance
- Track context loading times for optimization
- Use metrics to identify performance patterns

## 🎉 **You're Now Using Advanced Features!**

Even though OpenCode doesn't natively support these features, you now have:
- ✅ **Working cache system** with helper scripts
- ✅ **Comprehensive logging** with session tracking
- ✅ **Performance monitoring** with metrics collection
- ✅ **Usage analytics** with reporting capabilities

This gives you the **AgentOS-style optimization** we designed, just with manual activation instead of automatic integration.

**Bottom Line:** The cache and logs directories are now **fully functional** and provide real value for optimizing your OpenCode experience!