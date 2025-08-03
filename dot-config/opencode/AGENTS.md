# OpenCode Agent Ecosystem - Quick Reference

<system_overview>
This OpenCode configuration implements the **BMad methodology** with **AgentOS enhancement** for systematic software development. The system uses hierarchical context loading, quality gates, and intelligent agent coordination.

**📋 Complete Documentation**: See `knowledge/bmad-kb.md` for full methodology details  
**⚙️ Technical Configuration**: See `agentos-config.yaml` for AgentOS settings  
**🔧 Configuration Guide**: See `knowledge/opencode-configuration-kb.md` for setup patterns
</system_overview>

## <agent_ecosystem>

### 🎯 **Primary Entry Points**

#### 🎭 **BMad Master** (`@bmad-master`) ✅ AgentOS Enhanced
**Universal task executor** - Start here if unsure which agent to use
- Executes any BMad task or workflow directly
- Smart context loading and subagent coordination
- **Usage**: `@bmad-master I want to [start a project/create stories/run workflow]`

#### 🔍 **Context Primer** (`@context-primer`)
**Project discovery specialist** - Use for new project orientation
- Comprehensive project analysis and codebase understanding
- **Usage**: `@context-primer Analyze this project and provide development context`

#### 📋 **Agent Lister** (`@agent-lister`)
**Quick reference** - Lists all available agents with descriptions
- **Usage**: `@agent-lister Show me all available agents`

### 🏗️ **Core Development Agents**

#### 📊 **Business Analyst** (`@business-analyst`) ✅ AgentOS Enhanced
Requirements elicitation and business process analysis
- **Usage**: `@business-analyst Gather requirements for [feature/project]`

#### 🚀 **Product Manager** (`@product-manager`)
Product strategy and roadmap management
- **Usage**: `@product-manager Create product roadmap for [product]`

#### 👤 **Product Owner** (`@product-owner`)
Backlog management and sprint planning
- **Usage**: `@product-owner Create user stories for [feature]`

#### 🏗️ **System Architect** (`@system-architect`)
Technical architecture and system design
- **Usage**: `@system-architect Design architecture for [system type]`

#### 💻 **Senior Developer** (`@senior-developer`)
Implementation and technical leadership
- **Usage**: `@senior-developer Implement [feature] following best practices`

#### 🎨 **UX Designer** (`@ux-designer`)
User experience and interface design
- **Usage**: `@ux-designer Design UX for [feature/workflow]`

#### ✅ **Quality Assurance** (`@quality-assurance`)
Testing strategy and quality validation
- **Usage**: `@quality-assurance Create test plan for [feature]`

#### 🔄 **Scrum Master** (`@scrum-master`)
Process facilitation and team coaching
- **Usage**: `@scrum-master Facilitate sprint planning for [project]`

### 🔍 **Specialized Agents**

#### 🔍 **Deep Researcher** (`@deep-researcher`)
Advanced research and knowledge discovery
- **Usage**: `@deep-researcher Research [topic] with comprehensive analysis`

#### ⚙️ **OpenCode Configurator** (`@opencode-configurator`)
OpenCode configuration and agent ecosystem management
- **Usage**: `@opencode-configurator Configure [MCP/LSP/agents] for [purpose]`

#### 🔄 **Automation Orchestrator** (`@automation-orchestrator`)
Workflow automation and process optimization
- **Usage**: `@automation-orchestrator Automate [workflow/process]`

#### 📊 **Metrics Analyst** (`@metrics-analyst`)
Development KPIs and performance metrics
- **Usage**: `@metrics-analyst Analyze performance metrics for [project]`

#### 🗂️ **Cache Manager** (`@cache-manager`)
Context cache management and optimization specialist
- **Usage**: `@cache-manager Populate cache with current project context`

#### 📋 **Session Manager** (`@session-manager`)
Session tracking and development productivity monitoring
- **Usage**: `@session-manager Start session logging for this development session`

#### 📈 **Performance Monitor** (`@performance-monitor`)
System performance monitoring and analytics specialist
- **Usage**: `@performance-monitor Show system performance metrics and trends`

#### ⚡ **Lean Optimizer** (`@lean-optimizer`)
Lean manufacturing principles for development
- **Usage**: `@lean-optimizer Optimize [process] for efficiency`

#### 📚 **Knowledge Curator** (`@knowledge-curator`)
Institutional knowledge and best practices management
- **Usage**: `@knowledge-curator Organize knowledge for [domain]`

#### 📖 **Documentation Librarian** (`@documentation-librarian`)
Documentation lifecycle and findability management
- **Usage**: `@documentation-librarian Improve documentation for [project]`

#### 📋 **Script Supervisor** (`@script-supervisor`)
Consistency across requirements and specifications
- **Usage**: `@script-supervisor Validate consistency of [documents]`

#### 🚀 **Innovation Catalyst** (`@innovation-catalyst`)
Emerging technologies and adoption strategies
- **Usage**: `@innovation-catalyst Research emerging tech for [domain]`

#### 💰 **ROI Calculator** (`@roi-calculator`)
Technical decisions from business value perspective
- **Usage**: `@roi-calculator Calculate ROI for [technical decision]`

#### 🎯 **Strategic Advisor** (`@strategic-advisor`)
Technical roadmap and business strategy alignment
- **Usage**: `@strategic-advisor Align technical roadmap with business goals`

</agent_ecosystem>

## <directory_structure>

### Context Loading Hierarchy
```
~/.config/opencode/
├── agent/              # Agent definitions (markdown with YAML frontmatter)
├── agentos-config.yaml # AgentOS three-layer context architecture
├── cache/              # Context caching for performance optimization
├── logs/               # Performance monitoring and debugging logs
├── metrics/            # Analytics data and performance metrics
├── knowledge/          # Knowledge base and methodology documentation
├── tasks/              # Reusable task definitions
├── workflows/          # BMad methodology workflows
├── templates/          # Document and workflow templates
├── checklists/         # Quality validation checklists
├── standards/          # Coding and methodology standards
├── products/           # Product-specific patterns and guidelines
├── specs/              # Project specifications and requirements
├── quality/            # Quality gates and validation tools
├── context/            # Smart context loading and management
└── subagents/          # AgentOS subagent definitions
```

### Key Configuration Files
- **`agentos-config.yaml`**: AgentOS settings and context optimization
- **`opencode.json`**: Main OpenCode configuration
- **`knowledge/bmad-kb.md`**: Complete BMad methodology documentation
- **`knowledge/opencode-configuration-kb.md`**: Configuration patterns and best practices

</directory_structure>

## <quick_start_patterns>

### 🌱 **New Projects (Greenfield)**
```bash
@bmad-master I want to start a new [fullstack/service/UI] project
# Automatically loads: project-brief → architecture → stories → implementation
```

### 🏗️ **Existing Projects (Brownfield)**
```bash
@bmad-master I want to enhance an existing [fullstack/service/UI] system
# Automatically loads: analysis → planning → stories → integration
```

### 🔍 **Project Discovery**
```bash
@context-primer Analyze this project and provide development context
# Comprehensive project analysis and orientation
```

### ✅ **Quality Validation**
```bash
@quality-assurance Validate this [story/architecture] using [checklist-name]
# Runs quality gates and validation checklists
```

### 📋 **Quick Reference**
```bash
@agent-lister Show me all available agents
# Lists all agents with descriptions and usage patterns
```

</quick_start_patterns>

## <agentos_integration>

### Three-Layer Context Architecture
1. **Standards Layer**: Always-loaded methodology and coding standards
2. **Products Layer**: Auto-detected product-specific patterns
3. **Specs Layer**: Project-specific requirements and specifications

### Smart Features
- **Context Optimization**: Intelligent loading based on project type with caching
- **Quality Gates**: Automated validation at key checkpoints
- **Subagent Coordination**: Automatic spawning of specialized agents
- **Performance Monitoring**: Comprehensive metrics, logging, and analytics
- **Error Handling**: Robust fallback mechanisms and auto-recovery
- **Cache Management**: Multi-layer caching with intelligent optimization

**📋 Full AgentOS Configuration**: See `agentos-config.yaml` for complete settings

</agentos_integration>

## <methodology_reference>

### BMad Workflows Available
- **Greenfield**: `greenfield-[fullstack|service|ui].yaml`
- **Brownfield**: `brownfield-[fullstack|service|ui].yaml`
- **AgentOS Enhanced**: `agentos-bmad-fullstack.yaml`

### Quality Checklists
- `architect-checklist.md` - Technical architecture validation
- `pm-checklist.md` - Business alignment validation  
- `po-master-checklist.md` - Project setup validation
- `story-dod-checklist.md` - Story completeness validation
- `change-checklist.md` - Change impact assessment

### Key Tasks
- `create-next-story.md` - Story creation workflow
- `execute-checklist.md` - Quality validation process
- `advanced-elicitation.md` - Enhanced requirements gathering
- `configure-opencode.md` - Configuration management

**📋 Complete Methodology**: See `knowledge/bmad-kb.md` for full BMad documentation

</methodology_reference>

---

**🎯 Getting Started**: Use `@bmad-master` for general guidance or `@context-primer` for project discovery  
**📚 Full Documentation**: All detailed information is in the `knowledge/` directory  
**⚙️ Configuration**: Technical setup details are in `agentos-config.yaml` and configuration knowledge base
