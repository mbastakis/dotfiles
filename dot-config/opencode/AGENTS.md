# BMad Methodology in OpenCode - Complete Guide

## What is BMad?

**BMad (Business Methodology for Agile Development)** is a comprehensive framework that bridges business requirements with technical implementation through structured elicitation, analysis, and development processes. It provides a systematic approach to software development that ensures quality, traceability, and stakeholder alignment.

## Core Principles

1. **Iterative Elicitation**: Requirements are discovered through progressive refinement
2. **Cross-functional Collaboration**: All stakeholders participate in the development process  
3. **Quality Gates**: Each deliverable must pass defined quality checkpoints
4. **Traceability**: Clear links between business needs and technical solutions
5. **Adaptive Planning**: Plans evolve based on discovered information

## How BMad Works in OpenCode

### Project Types

BMad supports two main project types:

#### 🌱 **Greenfield Projects** (New from scratch)
- No existing codebase constraints
- Full architectural freedom
- Complete requirements discovery needed
- **Approach**: Start with project brief → architecture → stories

#### 🏗️ **Brownfield Projects** (Existing systems)
- Existing codebase and architecture
- Legacy constraints and dependencies
- Partial requirements known
- **Approach**: Start with technical analysis → stories

### Development Contexts

Each project type supports three development contexts:

- **Fullstack**: Complete web applications (frontend + backend)
- **Service**: Backend services and APIs only
- **UI**: Frontend applications and interfaces only

## The BMad Agent Ecosystem

### Core Agents

#### 🎭 **BMad Master** (`@bmad-master`)
- **Role**: Universal task executor and methodology expert
- **Use**: Can execute any BMad task or workflow directly
- **When**: Start here if unsure which agent to use

#### 📊 **Business Analyst** (`@business-analyst`)
- **Role**: Requirements elicitation and business process analysis
- **Deliverables**: Business requirements, process maps, stakeholder analysis
- **Key Tasks**: Stakeholder interviews, requirements gathering, gap analysis

#### 🚀 **Product Manager** (`@product-manager`)
- **Role**: Product strategy and roadmap management
- **Deliverables**: Product roadmap, market analysis, feature specifications
- **Key Tasks**: Market research, feature prioritization, stakeholder communication

#### 👤 **Product Owner** (`@product-owner`)
- **Role**: Backlog management and sprint planning
- **Deliverables**: User stories, acceptance criteria, sprint backlogs
- **Key Tasks**: Story creation, backlog prioritization, sprint planning

#### 🏗️ **System Architect** (`@system-architect`)
- **Role**: Technical architecture and system design
- **Deliverables**: Architecture documents, technical specifications, integration plans
- **Key Tasks**: System design, technology selection, technical risk assessment

#### 💻 **Senior Developer** (`@senior-developer`)
- **Role**: Implementation and technical leadership
- **Deliverables**: Code, technical documentation, implementation guides
- **Key Tasks**: Development, code review, technical mentoring

#### 🎨 **UX Designer** (`@ux-designer`)
- **Role**: User experience and interface design
- **Deliverables**: Wireframes, prototypes, design specifications
- **Key Tasks**: User research, wireframe creation, usability testing

#### ✅ **Quality Assurance** (`@quality-assurance`)
- **Role**: Testing strategy and quality validation
- **Deliverables**: Test plans, test cases, quality reports
- **Key Tasks**: Test planning, quality metrics, defect tracking

#### 🔄 **Scrum Master** (`@scrum-master`)
- **Role**: Process facilitation and team coaching
- **Deliverables**: Sprint reports, process improvements, team metrics
- **Key Tasks**: Sprint facilitation, impediment removal, team coaching

## BMad Workflows

### 🌱 Greenfield Workflows

#### **Greenfield Fullstack** (`greenfield-fullstack.yaml`)
**For**: New web applications from scratch
**Phases**:
1. **Project Initiation**: Project brief + requirements gathering
2. **Architecture & Design**: System architecture + UX design
3. **Epic Planning**: Break down into manageable epics
4. **Story Development**: Create detailed user stories
5. **Implementation**: Develop and test

#### **Greenfield Service** (`greenfield-service.yaml`)
**For**: New backend services and APIs
**Phases**:
1. **Project Initiation**: Service brief + requirements
2. **Service Design**: Architecture + API specifications
3. **Story Development**: Service-focused stories
4. **Implementation**: Service development

#### **Greenfield UI** (`greenfield-ui.yaml`)
**For**: New frontend applications
**Phases**:
1. **Project Initiation**: UI brief + requirements
2. **UI/UX Design**: Comprehensive UX design + architecture
3. **Epic Planning**: UI feature epics
4. **Story Development**: UI-focused stories
5. **Implementation**: Frontend development

### 🏗️ Brownfield Workflows

#### **Brownfield Fullstack** (`brownfield-fullstack.yaml`)
**For**: Enhancing existing web applications
**Phases**:
1. **Discovery & Analysis**: Understand existing system + requirements
2. **Planning & Design**: Plan within existing constraints
3. **Story Development**: Integration-aware stories
4. **Implementation**: Safe integration

#### **Brownfield Service** (`brownfield-service.yaml`)
**For**: Enhancing existing services
**Phases**:
1. **Service Analysis**: Analyze existing architecture
2. **Planning & Design**: Service enhancement planning
3. **Story Development**: Service integration stories
4. **Implementation**: Service enhancement

#### **Brownfield UI** (`brownfield-ui.yaml`)
**For**: Enhancing existing UIs
**Phases**:
1. **UI Analysis**: Analyze existing UI patterns
2. **Design & Planning**: UI enhancement planning
3. **Story Development**: UI integration stories
4. **Implementation**: UI enhancement

## Quality Gates & Checklists

BMad enforces quality through comprehensive checklists:

### **Architect Checklist** (`architect-checklist.md`)
- Technical architecture validation
- Security and performance review
- Infrastructure and deployment planning

### **Product Manager Checklist** (`pm-checklist.md`)
- Business alignment validation
- Market research verification
- Resource and timeline planning

### **Product Owner Checklist** (`po-master-checklist.md`)
- Project setup validation
- Feature sequencing review
- MVP scope alignment

### **Change Management Checklist** (`change-checklist.md`)
- Change impact assessment
- Risk mitigation planning
- Stakeholder approval process

### **Story Definition of Done** (`story-dod-checklist.md`)
- Story completeness validation
- Acceptance criteria verification
- Implementation readiness

### **Story Draft Checklist** (`story-draft-checklist.md`)
- Story quality validation
- Technical guidance review
- Self-containment assessment

## Key Tasks

### **Story Management**
- `create-next-story.md`: Create the next logical story in development
- `brownfield-create-story.md`: Create stories for existing systems
- `validate-next-story.md`: Comprehensive story validation

### **Epic & Project Management**
- `brownfield-create-epic.md`: Create epics for existing systems
- `create-doc.md`: Generate documents from templates

### **Quality & Process**
- `execute-checklist.md`: Run quality validation checklists
- `advanced-elicitation.md`: Enhanced requirements gathering
- `shard-doc.md`: Break documents into manageable pieces

## Templates

BMad provides comprehensive templates for all document types:

### **Core Templates**
- `prd-tmpl.yaml`: Product Requirements Document
- `story-tmpl.yaml`: User Story Template
- `architecture-tmpl.yaml`: System Architecture Document

### **Specialized Templates**
- `project-brief-tmpl.yaml`: Project initiation
- `front-end-spec-tmpl.yaml`: UI/UX specifications
- `brownfield-prd-tmpl.yaml`: Existing system enhancements

## How to Use BMad in OpenCode

### 1. **Starting a New Project**

For **Greenfield** projects:
```
@bmad-master I want to start a new [fullstack/service/UI] project
```

For **Brownfield** projects:
```
@bmad-master I want to enhance an existing [fullstack/service/UI] system
```

### 2. **Working with Specific Agents**

```
@product-manager Create a product roadmap for my e-commerce platform
@system-architect Design the architecture for a microservices system
@product-owner Create user stories for the shopping cart feature
```

### 3. **Running Workflows**

```
@bmad-master Run the greenfield-fullstack workflow for my new app
@bmad-master Execute the brownfield-service workflow for API enhancement
```

### 4. **Quality Validation**

```
@quality-assurance Validate this story using the story-dod-checklist
@system-architect Review this architecture using the architect-checklist
```

### 5. **Document Generation**

```
@bmad-master Create a PRD using the prd-template
@system-architect Generate architecture documentation
```

## Best Practices

### **Requirements Management**
- Start with high-level goals and decompose
- Validate requirements with multiple stakeholders
- Maintain traceability throughout development

### **Team Collaboration**
- Use cross-functional team participation
- Maintain regular communication and feedback
- Ensure shared understanding of goals

### **Quality Assurance**
- Build quality into the process from the start
- Use multiple validation points
- Regular quality reviews and improvements

### **Change Management**
- Follow structured change request processes
- Assess impact of all changes
- Get stakeholder approval for significant changes

## Success Metrics

BMad tracks both **Quality Metrics** (requirements traceability, defect rates, customer satisfaction) and **Process Metrics** (story completion rates, sprint goal achievement, stakeholder engagement).

## Getting Help

- **Start with**: `@bmad-master` for general guidance
- **Methodology questions**: Access the knowledge base in `knowledge/bmad-kb.md`
- **Process guidance**: Use `advanced-elicitation.md` for enhanced requirements gathering
- **Quality issues**: Run appropriate checklists for validation

BMad in OpenCode provides a complete, production-ready methodology for systematic software development with built-in quality assurance and stakeholder alignment.
