# Hello World Projects Rules

## Security & Safety Rules
- **NEVER modify, create, or delete files outside of `/Users/folstein/Documents/VIBE_CODING/hello_world_projects/`**
- **NEVER use `../` paths that would access parent directories above the project root**
- **NEVER modify system files, configuration files, or directories outside this project**
- **All file operations must be contained within the current project directory tree**
- **When using terminal commands, always use relative paths or absolute paths within the project**
- **Do not install global packages or modify system-wide settings**
- **Always verify package names before installation (check for typosquatting)**
- **Review generated code for unexpected system calls or network requests**
- **Use virtual environments and containers when possible for isolation**
- **Never execute code that requests elevated privileges without explicit user approval**

## Code Style & Standards
- Always include clear, descriptive comments explaining what each section of code does
- Use consistent indentation (2 spaces for web languages, 4 spaces for Python, tabs for Go)
- Choose descriptive variable and function names over short abbreviations
- Add a header comment to each file explaining its purpose

## Project Structure
- Create a separate directory for each hello world project (e.g., `python-hello/`, `js-hello/`, `rust-hello/`)
- Include a `README.md` in each project directory explaining:
  - What language/framework is used
  - How to run the program
  - What the program demonstrates
- Add appropriate `.gitignore` files for each language

## Learning & Documentation
- When creating new hello world projects, include comments that explain:
  - Basic syntax being demonstrated
  - Key language concepts being shown
  - Common patterns or idioms for that language
- Always test that code runs successfully before considering it complete
- Include example output in README files when helpful

## Language-Specific Preferences
- **Python**: Use `if __name__ == "__main__":` for executable scripts
- **JavaScript**: Prefer `const` and `let` over `var`, use modern ES6+ syntax
- **Java**: Follow standard naming conventions (PascalCase for classes, camelCase for methods)
- **Go**: Use `gofmt` formatting, follow Go naming conventions
- **Rust**: Use `cargo` for project management, include `Cargo.toml`

## Error Handling
- Include basic error handling appropriate for the language
- Show both successful execution and common error scenarios when relevant
- Use language-appropriate error handling patterns (try/catch, Result types, etc.)

## Dependencies & Setup
- Minimize external dependencies for hello world projects
- When dependencies are needed, clearly document installation steps
- Include version information for language runtimes and tools
- Prefer language standard libraries over external packages when possible

## External Documentation References
- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
  - Use this for the latest LangGraph patterns, APIs, and best practices
  - Reference when creating LangGraph-based projects or workflows
  - Fetch current documentation using curl when needed for specific implementations
- **LangChain Documentation**: https://python.langchain.com/docs/
  - Use for LangChain core concepts, chains, agents, and integrations
  - Reference for building AI applications with language models
  - Include examples of prompt engineering and model interactions
- **Open WebUI Documentation**: https://docs.openwebui.com/
  - Use for Open WebUI setup, configuration, and customization
  - Reference for building web interfaces for AI models
  - Include deployment patterns and integration examples
- **Python 3.13 Documentation**: https://docs.python.org/3.13/
  - Use for current Python syntax, built-in functions, and standard library
  - Reference for latest language features and best practices
  - Include examples of modern Python patterns and idioms
