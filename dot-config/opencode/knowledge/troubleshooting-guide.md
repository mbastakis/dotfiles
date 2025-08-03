# OpenCode Troubleshooting Guide

## 🔧 Common Issues & Solutions

This guide helps you quickly resolve common issues with OpenCode, BMad methodology, and AgentOS integration.

## 🚨 Quick Diagnostics

### **System Health Check**
```bash
@opencode-configurator Run system diagnostics and health check
```

### **Performance Check**
```bash
@metrics-analyst Show current performance metrics and identify issues
```

### **Context Validation**
```bash
@context-optimizer Validate context loading and optimization status
```

## 🔍 Context Loading Issues

### **Problem: Context Not Loading**
**Symptoms:**
- Agents seem unaware of project context
- Generic responses instead of project-specific guidance
- Missing methodology or standards references

**Solutions:**
1. **Check Project Detection**
   ```bash
   @context-primer Analyze project type detection and context loading
   ```

2. **Verify Configuration**
   - Ensure `agentos-config.yaml` is properly configured
   - Check that project files match detection patterns
   - Verify directory structure is complete

3. **Clear Cache**
   ```bash
   # Clear context cache (if cache corruption suspected)
   rm -rf ~/.config/opencode/cache/*
   ```

4. **Manual Context Loading**
   ```bash
   @bmad-master Load BMad methodology context for [project-type] project
   ```

### **Problem: Slow Context Loading**
**Symptoms:**
- Long delays before agent responses
- Timeout errors during context loading
- High memory usage

**Solutions:**
1. **Check Cache Status**
   ```bash
   @metrics-analyst Show context loading performance metrics
   ```

2. **Optimize Cache Settings**
   - Review cache configuration in `agentos-config.yaml`
   - Increase cache duration for stable content
   - Enable compression for large context files

3. **Reduce Context Size**
   ```bash
   @context-optimizer Analyze and optimize context size for current project
   ```

## 🤖 Agent Coordination Issues

### **Problem: Agents Not Coordinating**
**Symptoms:**
- Subagents not spawning automatically
- Inconsistent responses between agents
- Missing specialized expertise

**Solutions:**
1. **Check Subagent Configuration**
   ```bash
   @opencode-configurator Validate subagent configuration and auto-spawn conditions
   ```

2. **Verify Agent Enhancement**
   - Ensure all agents have AgentOS integration enabled
   - Check YAML frontmatter in agent files
   - Validate subagent definitions

3. **Manual Subagent Coordination**
   ```bash
   @bmad-master Coordinate with @context-optimizer and @quality-enforcer for [task]
   ```

### **Problem: Agent Responses Inconsistent**
**Symptoms:**
- Different agents provide conflicting guidance
- Methodology compliance varies between agents
- Quality standards not consistently applied

**Solutions:**
1. **Validate Quality Gates**
   ```bash
   @quality-enforcer Run comprehensive quality validation across all agents
   ```

2. **Check Standards Alignment**
   ```bash
   @bmad-master Validate BMad methodology compliance across agent responses
   ```

3. **Update Agent Configuration**
   - Review agent YAML frontmatter for consistency
   - Ensure all agents reference same standards
   - Validate quality gate configurations

## 📊 Performance Issues

### **Problem: High Token Usage**
**Symptoms:**
- Rapid token consumption
- Expensive API costs
- Context window overflow errors

**Solutions:**
1. **Enable Context Optimization**
   ```bash
   @context-optimizer Analyze and optimize token usage for current session
   ```

2. **Review Context Settings**
   - Check token reduction target (should be 60%)
   - Enable context compression
   - Use lite versions of methodology docs

3. **Monitor Usage Patterns**
   ```bash
   @metrics-analyst Show token usage patterns and optimization opportunities
   ```

### **Problem: Slow Response Times**
**Symptoms:**
- Long delays between request and response
- Timeout errors
- Poor user experience

**Solutions:**
1. **Check System Performance**
   ```bash
   @metrics-analyst Show response time metrics and performance bottlenecks
   ```

2. **Optimize Context Loading**
   - Enable predictive context loading
   - Increase cache hit rates
   - Use lazy loading for optional context

3. **Review Network/API Issues**
   - Check API provider status
   - Verify network connectivity
   - Consider switching to faster model if available

## 🔒 Quality Gate Failures

### **Problem: Quality Gates Failing**
**Symptoms:**
- Validation errors in deliverables
- Standards compliance failures
- BMad methodology violations

**Solutions:**
1. **Identify Specific Failures**
   ```bash
   @quality-enforcer Show detailed quality gate failure analysis
   ```

2. **Review Standards Compliance**
   ```bash
   @bmad-master Validate current work against BMad methodology requirements
   ```

3. **Fix Common Issues**
   - Ensure all deliverables have proper documentation
   - Validate acceptance criteria completeness
   - Check architecture compliance with standards

### **Problem: Quality Gate Configuration Issues**
**Symptoms:**
- Quality gates not running automatically
- Incorrect validation criteria
- Missing quality checks

**Solutions:**
1. **Validate Configuration**
   ```bash
   @opencode-configurator Review and fix quality gate configuration
   ```

2. **Check Threshold Settings**
   - Review quality gate thresholds in `agentos-config.yaml`
   - Ensure realistic and achievable targets
   - Validate gate trigger conditions

## 📁 File & Directory Issues

### **Problem: Missing Directories**
**Symptoms:**
- Cache/logs/metrics directories not found
- File permission errors
- Configuration files not loading

**Solutions:**
1. **Create Missing Directories**
   ```bash
   mkdir -p ~/.config/opencode/{cache,logs,metrics}
   ```

2. **Check Permissions**
   ```bash
   chmod 755 ~/.config/opencode/
   chmod -R 644 ~/.config/opencode/*.md
   ```

3. **Validate Directory Structure**
   ```bash
   @opencode-configurator Validate directory structure and fix any issues
   ```

### **Problem: Configuration File Errors**
**Symptoms:**
- YAML parsing errors
- JSON schema validation failures
- Configuration not loading

**Solutions:**
1. **Validate YAML Syntax**
   ```bash
   # Check agentos-config.yaml syntax
   python -c "import yaml; yaml.safe_load(open('~/.config/opencode/agentos-config.yaml'))"
   ```

2. **Validate JSON Schema**
   ```bash
   # Check opencode.json against schema
   @opencode-configurator Validate opencode.json schema compliance
   ```

3. **Reset to Defaults**
   - Backup current configuration
   - Restore from known good configuration
   - Gradually reapply customizations

## 🔄 Workflow Issues

### **Problem: BMad Workflows Not Working**
**Symptoms:**
- Workflow steps not executing properly
- Missing deliverables
- Process not following BMad methodology

**Solutions:**
1. **Validate Workflow Configuration**
   ```bash
   @bmad-master Validate BMad workflow configuration and execution
   ```

2. **Check Workflow Dependencies**
   - Ensure all required templates are available
   - Validate agent dependencies
   - Check quality gate integration

3. **Manual Workflow Execution**
   ```bash
   @bmad-master Execute [workflow-name] workflow step by step with validation
   ```

## 🆘 Emergency Recovery

### **Complete System Reset**
If all else fails, perform a complete system reset:

1. **Backup Current Configuration**
   ```bash
   cp -r ~/.config/opencode ~/.config/opencode.backup
   ```

2. **Clear All Caches**
   ```bash
   rm -rf ~/.config/opencode/{cache,logs,metrics}/*
   ```

3. **Validate Base Configuration**
   ```bash
   @opencode-configurator Perform complete system validation and repair
   ```

4. **Restore from Backup**
   - Restore known good configuration
   - Test basic functionality
   - Gradually restore customizations

### **Get Expert Help**
When you need additional assistance:

```bash
@bmad-master I'm experiencing [detailed problem description] and need expert troubleshooting assistance
```

```bash
@opencode-configurator Help me diagnose and fix [specific technical issue]
```

```bash
@deep-researcher Research solutions for [complex problem] and provide comprehensive troubleshooting guide
```

## 📊 Monitoring & Prevention

### **Proactive Monitoring**
Set up regular health checks:

```bash
# Daily health check
@metrics-analyst Generate daily system health report

# Weekly performance review
@context-optimizer Analyze weekly performance trends and optimization opportunities

# Monthly configuration audit
@opencode-configurator Perform monthly configuration audit and optimization
```

### **Performance Baselines**
Establish performance baselines:
- **Context Loading**: < 2 seconds
- **Agent Response**: < 5 seconds
- **Cache Hit Rate**: > 80%
- **Token Efficiency**: > 60% reduction
- **Quality Gate Pass**: > 95%

### **Alert Thresholds**
Monitor these key metrics:
- Token usage spikes
- Context loading failures
- Quality gate failures
- Agent coordination errors
- Performance degradation

## 📚 Additional Resources

- [Quick Start Guide](quick-start-guide.md)
- [BMad Methodology](bmad-kb.md)
- [AgentOS Configuration](../agentos-config.yaml)
- [Performance Monitoring](../quality/reports/agentos-quality-dashboard.md)

---

**💡 Pro Tip**: Most issues can be resolved by running `@opencode-configurator Run comprehensive system diagnostics` which will identify and often auto-fix common problems.