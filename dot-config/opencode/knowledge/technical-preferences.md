# Technical Preferences and Standards

## Overview
This document defines the preferred technologies, patterns, and standards for BMad methodology implementation. These preferences guide architecture decisions and technology selection across all projects.

## Technology Stack Preferences

### Programming Languages
- **Primary Backend**: TypeScript/Node.js, Python, Java
- **Primary Frontend**: TypeScript/React, Vue.js, Angular
- **Mobile**: React Native, Flutter, Swift/Kotlin
- **Infrastructure**: TypeScript (CDK), Python (Terraform), YAML

### Cloud Providers
- **Preferred**: AWS (primary), Azure (secondary), GCP (tertiary)
- **Rationale**: AWS offers comprehensive services and mature ecosystem

### Database Technologies
- **Relational**: PostgreSQL (primary), MySQL (secondary)
- **NoSQL**: MongoDB (document), Redis (cache), DynamoDB (AWS)
- **Search**: Elasticsearch, OpenSearch
- **Analytics**: ClickHouse, BigQuery

### API Patterns
- **REST**: OpenAPI 3.0 specification required
- **GraphQL**: Apollo Server/Client preferred
- **Real-time**: WebSockets, Server-Sent Events
- **Messaging**: AWS SQS/SNS, RabbitMQ, Apache Kafka

## Architecture Patterns

### Application Architecture
- **Microservices**: Preferred for complex systems
- **Monolith**: Acceptable for simple applications
- **Serverless**: Preferred for event-driven workloads
- **JAMstack**: Preferred for static/content sites

### Code Organization
- **Monorepo**: Preferred for related services (Nx, Lerna, Rush)
- **Polyrepo**: Acceptable for independent services
- **Module Structure**: Domain-driven design principles
- **Dependency Injection**: Preferred for testability

### Data Patterns
- **Repository Pattern**: Required for data access
- **Event Sourcing**: Consider for audit requirements
- **CQRS**: Consider for read/write separation
- **Database per Service**: Required for microservices

## Development Standards

### Code Quality
- **Linting**: ESLint (JS/TS), Pylint (Python), Checkstyle (Java)
- **Formatting**: Prettier (JS/TS), Black (Python), Google Java Format
- **Type Safety**: TypeScript strict mode, Python type hints
- **Testing**: Jest (JS/TS), pytest (Python), JUnit (Java)

### Security Standards
- **Authentication**: OAuth 2.0/OIDC, JWT tokens
- **Authorization**: RBAC, attribute-based access control
- **Secrets**: AWS Secrets Manager, Azure Key Vault
- **Encryption**: TLS 1.3, AES-256, RSA-2048+

### Performance Standards
- **API Response**: < 200ms for 95th percentile
- **Page Load**: < 3 seconds for initial load
- **Database**: Query optimization, proper indexing
- **Caching**: Redis, CloudFront, application-level caching

## Infrastructure Preferences

### Deployment
- **Containerization**: Docker required
- **Orchestration**: Kubernetes (EKS), Docker Compose (local)
- **CI/CD**: GitHub Actions (preferred), GitLab CI, Jenkins
- **Infrastructure as Code**: AWS CDK (preferred), Terraform

### Monitoring and Observability
- **Logging**: Structured logging (JSON), centralized (ELK, CloudWatch)
- **Metrics**: Prometheus/Grafana, CloudWatch, DataDog
- **Tracing**: AWS X-Ray, Jaeger, Zipkin
- **Alerting**: PagerDuty, Slack integration

### Environment Management
- **Development**: Local Docker, cloud development environments
- **Testing**: Automated testing environments, feature branches
- **Staging**: Production-like environment for final validation
- **Production**: Blue-green or canary deployments

## Framework Preferences

### Backend Frameworks
- **Node.js**: NestJS (enterprise), Express (simple), Fastify (performance)
- **Python**: FastAPI (modern), Django (full-featured), Flask (lightweight)
- **Java**: Spring Boot, Quarkus (cloud-native)

### Frontend Frameworks
- **React**: Next.js (full-stack), Create React App (SPA)
- **Vue**: Nuxt.js (full-stack), Vue CLI (SPA)
- **Angular**: Angular CLI, Nx workspace

### Testing Frameworks
- **Unit Testing**: Jest, pytest, JUnit
- **Integration Testing**: Supertest, TestContainers
- **E2E Testing**: Playwright, Cypress, Selenium
- **Load Testing**: k6, Artillery, JMeter

## Tool Preferences

### Development Tools
- **IDE**: VS Code (primary), IntelliJ IDEA, WebStorm
- **Version Control**: Git with conventional commits
- **Package Management**: npm/yarn (JS), pip/poetry (Python), Maven/Gradle (Java)
- **Documentation**: Markdown, OpenAPI, JSDoc/TypeDoc

### Project Management
- **Issue Tracking**: GitHub Issues, Jira, Linear
- **Documentation**: Notion, Confluence, GitBook
- **Communication**: Slack, Microsoft Teams
- **Design**: Figma, Sketch, Adobe XD

## Anti-Patterns to Avoid

### Technology Choices
- **Avoid**: Outdated frameworks, unmaintained libraries
- **Avoid**: Over-engineering with unnecessary complexity
- **Avoid**: Vendor lock-in without clear benefits
- **Avoid**: Mixing too many programming languages unnecessarily

### Architecture Decisions
- **Avoid**: Distributed monoliths
- **Avoid**: Shared databases across services
- **Avoid**: Synchronous communication for non-critical paths
- **Avoid**: Premature optimization

### Development Practices
- **Avoid**: Skipping tests for "quick fixes"
- **Avoid**: Hardcoded configuration values
- **Avoid**: Ignoring security best practices
- **Avoid**: Inconsistent coding standards

## Decision Framework

### Technology Selection Criteria
1. **Team Expertise**: Leverage existing team knowledge
2. **Community Support**: Active community and documentation
3. **Long-term Viability**: Stable, well-maintained projects
4. **Performance Requirements**: Meets performance benchmarks
5. **Security Posture**: Strong security track record
6. **Cost Considerations**: Total cost of ownership
7. **Integration Capabilities**: Works well with existing stack

### When to Deviate
- **Performance Requirements**: Specific performance needs
- **Team Expertise**: Existing team specialization
- **Client Requirements**: Specific client technology mandates
- **Legacy Integration**: Existing system constraints
- **Regulatory Compliance**: Industry-specific requirements

## Customization Guidelines

### Project-Specific Overrides
- Document deviations from these preferences
- Provide clear rationale for alternative choices
- Ensure team alignment on technology decisions
- Update project documentation accordingly

### Preference Updates
- Review preferences quarterly
- Incorporate new technology trends
- Gather team feedback on current choices
- Update based on project learnings

## Implementation Notes

### For Architecture Documents
- Reference these preferences in technology selection
- Justify any deviations with clear rationale
- Ensure consistency across project components
- Document technology-specific patterns

### For Development Teams
- Use these as default starting points
- Adapt based on specific project needs
- Maintain consistency within projects
- Share learnings to improve preferences

This document serves as a living guide that should be updated based on team experience, industry trends, and project learnings.