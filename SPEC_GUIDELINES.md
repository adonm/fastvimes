# FastVimes Spec Guidelines

## Overview

This document provides clear guidelines for organizing and maintaining the FastVimes specification to ensure consistency and clarity for AI agent contributions.

## Spec Organization Structure

### 1. **AGENT.md** - Primary Spec Document
- **Purpose**: Living specification containing architecture, patterns, and requirements
- **Sections**:
  - Project Vision & Core Concept
  - Architecture Patterns (Single Source of Truth)
  - API Design & Namespacing
  - Development Workflow
  - Testing Strategy
  - Contributor Guidelines

### 2. **Test Requirements** - Validation Rules
- **Multi-Schema Testing**: Every feature must work with different schemas
- **API Consistency**: Same endpoints via CLI/FastAPI/NiceGUI
- **Performance Validation**: Ensure changes don't degrade performance
- **Edge Case Handling**: Test with reserved words, special characters

### 3. **Code Quality Standards**
- **Established Patterns**: Use existing DatabaseService patterns
- **Minimal Custom Code**: Prefer composition over inheritance
- **Security First**: Never expose secrets, use SQLGlot for safety
- **Type Safety**: Use type hints on all public functions
- **Ruff Compliance**: Format with ruff, fix all linting issues

## Spec Review Process

### Pre-Implementation Review
1. **Architecture Alignment**: Does the change fit the single source of truth pattern?
2. **Multi-Schema Support**: Will it work with any database schema?
3. **API Consistency**: Does it maintain 1:1 mapping between CLI/FastAPI/NiceGUI?
4. **Security Review**: Are there any security implications?
5. **Performance Impact**: Will this affect system performance?

### Implementation Review
1. **Spec Compliance**: Does the code match the spec requirements?
2. **Test Coverage**: Are there adequate tests for all schema types?
3. **Documentation**: Is user-facing documentation updated?
4. **Examples**: Are there working examples demonstrating the feature?

## Spec Evolution Guidelines

### Adding New Features
1. **Update AGENT.md** - Add clear requirements and architecture patterns
2. **Define Test Requirements** - Specify multi-schema testing requirements
3. **Create Examples** - Provide working examples in `examples/` directory
4. **Update Documentation** - Add user-facing documentation

### Modifying Existing Features
1. **Backward Compatibility** - Ensure existing code continues to work
2. **Migration Path** - Provide clear upgrade path if breaking changes
3. **Test Updates** - Update tests to match new behavior
4. **Documentation Updates** - Update all relevant documentation

## Review Checklist for AI Agents

### Before Starting Implementation
- [ ] Read AGENT.md thoroughly
- [ ] Understand the single source of truth pattern
- [ ] Identify multi-schema testing requirements
- [ ] Check for existing patterns to follow

### During Implementation
- [ ] Update AGENT.md with new spec requirements
- [ ] Write tests before implementing features
- [ ] Follow established DatabaseService patterns
- [ ] Ensure API consistency across CLI/FastAPI/NiceGUI

### After Implementation
- [ ] Run full test suite with all schema types
- [ ] Check ruff compliance
- [ ] Update user-facing documentation
- [ ] Create working examples

## Spec Quality Metrics

### Measurable Criteria
- **Test Coverage**: >90% coverage for all DatabaseService public methods
- **Multi-Schema Support**: All features tested with 4+ different schemas
- **API Consistency**: 1:1 mapping between CLI/FastAPI/NiceGUI endpoints
- **Documentation**: Every public method has examples and usage docs
- **Performance**: No regressions in benchmark tests

### Review Questions
1. Does this change align with the FastVimes core vision?
2. Is the implementation consistent with existing patterns?
3. Will this work with any database schema structure?
4. Are there adequate tests for all edge cases?
5. Is the feature documented with clear examples?

## Feature Branch Strategy

### Branch Organization
- **main**: Production-ready code, always deployable
- **feature/**: New features (e.g., `feature/query-builder`, `feature/bulk-operations`)
- **fix/**: Bug fixes (e.g., `fix/rql-parsing`, `fix/auth-middleware`)
- **docs/**: Documentation updates (e.g., `docs/api-reference`, `docs/component-guide`)
- **refactor/**: Code refactoring without feature changes

### Branch Workflow
1. **Create feature branch** from main with descriptive name
2. **Update AGENT.md** with spec changes in the feature branch
3. **Implement tests first** following multi-schema requirements
4. **Implement code** to pass tests
5. **Update documentation** in same branch
6. **Merge to main** only after all tests pass and spec is updated

### Branch Best Practices
- **Small, focused branches**: Each branch should address one specific feature/fix
- **Clear naming**: Use descriptive names that indicate the purpose
- **Frequent commits**: Small, logical commits with clear messages
- **Rebase before merge**: Keep commit history clean and linear
- **Delete merged branches**: Remove feature branches after successful merge

## Documentation Organization

### File Structure
```
docs/
├── api/                    # API documentation
│   ├── endpoints.md       # REST API endpoints
│   ├── rql-syntax.md      # RQL query language
│   └── authentication.md  # Auth middleware
├── components/            # UI component documentation
│   ├── data-explorer.md   # Data grid component
│   ├── query-builder.md   # Visual query builder
│   └── form-generator.md  # Auto-generated forms
├── examples/              # Working examples
│   ├── basic-usage.md     # Getting started guide
│   ├── customization.md   # Component override examples
│   └── deployment.md      # Production deployment
└── development/           # Development guides
    ├── architecture.md    # System architecture
    ├── testing.md         # Testing strategies
    └── contributing.md    # Contribution guidelines
```

### Documentation Standards
- **Keep docs with code**: Feature docs should be updated in same branch
- **Working examples**: Every feature must have a working example
- **API consistency**: Document all three interfaces (CLI/FastAPI/NiceGUI)
- **Version tracking**: Update docs when API changes
- **Clear navigation**: Organize by user journey and use cases

## Codebase Organization

### Directory Structure Principles
- **Clear separation**: API, CLI, components, and core logic in separate modules
- **Consistent naming**: Follow Python naming conventions consistently
- **Logical grouping**: Group related functionality together
- **Minimal dependencies**: Keep imports clean and dependencies minimal

### Code Organization Rules
1. **Single source of truth**: DatabaseService contains all business logic
2. **Thin wrappers**: FastAPI/CLI are lightweight wrappers over DatabaseService
3. **Testable units**: Each module should be independently testable
4. **Clear interfaces**: Public methods have clear contracts and type hints
5. **Consistent patterns**: Use established patterns for similar functionality

### File Naming Conventions
- **Snake_case**: For Python files and modules
- **Descriptive names**: File names should indicate purpose
- **Logical grouping**: Related files in same directory
- **Test files**: Match source file names with `test_` prefix

### Import Organization
- **Standard library** imports first
- **Third-party** imports second
- **Local** imports last
- **Absolute imports** preferred over relative
- **Minimal imports**: Only import what's needed

## Continuous Improvement

### Regular Reviews
- **Monthly spec review**: AGENT.md clarity and completeness
- **Quarterly architecture review**: Testing strategy effectiveness
- **Annual pattern review**: Architectural patterns and decisions
- **Documentation audit**: Ensure docs match current implementation

### Feedback Integration
- **Implementation feedback**: Update spec based on development experience
- **User feedback**: Incorporate user experience improvements
- **Performance feedback**: Address performance issues proactively
- **Security feedback**: Regular security review and updates

### Maintenance Tasks
- **Dependency updates**: Keep dependencies current and secure
- **Code cleanup**: Regular refactoring to maintain code quality
- **Documentation updates**: Keep docs synchronized with code changes
- **Test maintenance**: Update tests as codebase evolves

## Tools and Automation

### Spec Validation Tools
- **Ruff**: Code formatting and linting
- **pytest**: Multi-schema testing framework
- **mypy**: Type checking (optional)
- **Coverage**: Test coverage reporting

### Automated Checks
- Pre-commit hooks for spec compliance
- CI/CD pipeline for multi-schema testing
- Automated documentation generation
- Performance regression testing
