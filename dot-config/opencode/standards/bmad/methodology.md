# BMad Methodology Standards

## Core Methodology

BMad (Business Methodology for Agile Development) is a comprehensive framework that bridges business requirements with technical implementation through structured elicitation, analysis, and development processes.

### Key Principles

1. **Iterative Elicitation**: Requirements are discovered through progressive refinement
2. **Cross-functional Collaboration**: All stakeholders participate in the development process  
3. **Quality Gates**: Each deliverable must pass defined quality checkpoints
4. **Traceability**: Clear links between business needs and technical solutions
5. **Adaptive Planning**: Plans evolve based on discovered information

## Project Types

### Greenfield Projects
- **Definition**: New projects starting from scratch
- **Characteristics**: No existing codebase constraints, full architectural freedom, complete requirements discovery needed
- **Approach**: Start with project brief, then architecture, then stories

### Brownfield Projects
- **Definition**: Projects working with existing systems
- **Characteristics**: Existing codebase and architecture, legacy constraints and dependencies, partial requirements known
- **Approach**: Start with technical analysis, then stories

## Quality Standards

### Requirements Management
- All requirements must be traceable to business objectives
- Requirements must be validated with stakeholders
- Changes must follow structured change management process
- Start with high-level goals and decompose
- Maintain traceability throughout development

### Development Process
- Follow spec-driven development approach
- Implement comprehensive testing strategy
- Maintain documentation throughout development lifecycle
- Cross-functional team participation
- Regular communication and feedback

### Deliverable Quality
- All deliverables must pass quality gates
- Code must meet established coding standards
- Documentation must be complete and accurate
- Quality built into the process, not added at the end
- Multiple validation points throughout development

## Workflow Patterns

### Story Development Lifecycle
1. **Elicitation**: Gather initial requirements
2. **Analysis**: Break down into manageable pieces
3. **Design**: Create technical and UX specifications
4. **Implementation**: Develop and test
5. **Validation**: Verify against acceptance criteria
6. **Deployment**: Release to production

### Quality Gates
- **Story Draft**: Initial story meets basic criteria
- **Story Refinement**: Story is detailed and estimated
- **Definition of Done**: Story meets all completion criteria
- **Architecture Review**: Technical design is sound
- **Change Management**: Changes are properly assessed

## Success Metrics

### Quality Metrics
- Requirements traceability
- Defect rates
- Customer satisfaction
- Time to market
- Team velocity

### Process Metrics
- Story completion rates
- Sprint goal achievement
- Stakeholder engagement
- Knowledge transfer effectiveness
- Process adherence

## Integration with AgentOS

BMad methodology integrates with AgentOS through:
- Structured specification development using AgentOS spec templates
- Quality gate enforcement through automated validation
- Context-aware development processes with smart context loading
- Standards compliance validation through quality enforcer subagent
- Three-layer context architecture supporting BMad workflows