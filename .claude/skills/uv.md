# UV Package Manager Skill

Expert skill for using `uv`, the fast Python package and project manager written in Rust.

## Overview

`uv` is a drop-in replacement for pip, pip-tools, and virtualenv that's 10-100x faster. Use this skill when managing Python dependencies, creating virtual environments, or working with Python projects.

## Core Commands

### Virtual Environments

#### Create a virtual environment
```bash
uv venv                    # Create .venv in current directory
uv venv path/to/venv       # Create venv at specific path
uv venv --python 3.12      # Use specific Python version
```

#### Activate virtual environment
```bash
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

### Package Installation

#### Install packages
```bash
uv pip install package-name              # Install single package
uv pip install package-name==1.2.3       # Install specific version
uv pip install "package-name>=1.0,<2.0"  # Version constraints
uv pip install -r requirements.txt       # Install from requirements
uv pip install -e .                      # Install in editable mode
uv pip install -e ".[dev]"               # Install with extras
uv pip install --system                  # Install to system Python
```

#### Install from pyproject.toml
```bash
uv pip install -e .              # Install project in editable mode
uv pip install -e ".[dev,test]"  # Install with optional dependencies
```

### Package Management

#### List installed packages
```bash
uv pip list                # List all packages
uv pip list --format json  # JSON format
uv pip show package-name   # Show package details
```

#### Freeze dependencies
```bash
uv pip freeze              # Output installed packages
uv pip freeze > requirements.txt  # Save to file
```

#### Uninstall packages
```bash
uv pip uninstall package-name           # Uninstall single package
uv pip uninstall -r requirements.txt    # Uninstall from file
```

#### Upgrade packages
```bash
uv pip install --upgrade package-name   # Upgrade single package
uv pip install --upgrade -r requirements.txt  # Upgrade all
```

### Project Initialization

#### Initialize new project
```bash
uv init                    # Initialize in current directory
uv init --lib              # Initialize as library
uv init --name myproject   # Initialize with specific name
```

### Compilation & Lock Files

#### Compile dependencies
```bash
uv pip compile pyproject.toml -o requirements.txt  # Compile to requirements.txt
uv pip compile requirements.in -o requirements.txt # Compile .in file
```

#### Sync environment
```bash
uv pip sync requirements.txt  # Sync venv to exact requirements
```

## Best Practices

### Project Setup Workflow

1. **Create project structure:**
```bash
mkdir myproject && cd myproject
uv init --lib  # or without --lib for application
```

2. **Create virtual environment:**
```bash
uv venv
source .venv/bin/activate
```

3. **Install project with dev dependencies:**
```bash
uv pip install -e ".[dev]"
```

### Dependency Management

1. **Always use version constraints in pyproject.toml:**
```toml
dependencies = [
    "requests>=2.31.0,<3.0.0",
    "pydantic>=2.0.0",
]
```

2. **Separate dev dependencies:**
```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "mypy>=1.11.0",
]
```

3. **Lock dependencies for reproducibility:**
```bash
uv pip freeze > requirements.txt
```

### Performance Tips

- **Use `uv` instead of `pip`** - It's significantly faster
- **Use `uv pip sync`** instead of `pip install -r` for exact reproduction
- **Leverage caching** - `uv` automatically caches packages

### Common Patterns

#### Quick test environment
```bash
uv venv .test-venv
source .test-venv/bin/activate
uv pip install pytest hypothesis
pytest
```

#### Install from git
```bash
uv pip install git+https://github.com/user/repo.git
uv pip install git+https://github.com/user/repo.git@branch-name
uv pip install git+https://github.com/user/repo.git@v1.0.0
```

#### Install with extras
```bash
uv pip install "package[extra1,extra2]"
uv pip install -e ".[dev,test,docs]"
```

## Troubleshooting

### Virtual environment issues

**Problem:** Virtual environment not found
```bash
# Solution: Ensure you've created it
uv venv
source .venv/bin/activate
```

**Problem:** Wrong Python version
```bash
# Solution: Specify Python version
uv venv --python 3.12
```

### Installation issues

**Problem:** Package not found
```bash
# Solution: Check package name on PyPI
uv pip install --index-url https://pypi.org/simple/ package-name
```

**Problem:** Conflicting dependencies
```bash
# Solution: Use constraints file
uv pip install -r requirements.txt -c constraints.txt
```

### Network issues

**Problem:** Timeout errors
```bash
# Solution: Increase timeout
uv pip install --timeout 300 package-name
```

## Advanced Usage

### Custom index URLs
```bash
uv pip install --index-url https://custom.pypi.org/simple/ package-name
uv pip install --extra-index-url https://custom.pypi.org/simple/ package-name
```

### Offline installation
```bash
# Download packages
uv pip download -r requirements.txt -d ./packages/

# Install offline
uv pip install --no-index --find-links ./packages/ -r requirements.txt
```

### Build from source
```bash
uv pip install --no-binary :all: package-name  # Build all from source
uv pip install --no-binary package-name package-name  # Build specific package
```

## Integration with Other Tools

### With pytest
```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
pytest
```

### With pre-commit
```bash
uv pip install pre-commit
pre-commit install
```

### With tox
```bash
uv pip install tox
tox
```

## When to Use This Skill

✅ **Use this skill when:**
- Creating Python projects
- Managing dependencies
- Setting up virtual environments
- Installing packages
- Troubleshooting package installation
- Optimizing Python environment setup

❌ **Don't use for:**
- Building packages (use build tools)
- Publishing to PyPI (use twine)
- System-wide Python management (use pyenv)

## Quick Reference

```bash
# Most common commands
uv venv                           # Create venv
source .venv/bin/activate        # Activate
uv pip install -e ".[dev]"       # Install project + dev deps
uv pip install package-name      # Install package
uv pip list                      # List packages
uv pip freeze > requirements.txt # Save dependencies
uv pip uninstall package-name    # Uninstall package
```

## Resources

- Official docs: https://github.com/astral-sh/uv
- PyPI: https://pypi.org
- Python Packaging Guide: https://packaging.python.org
