# GitHub Actions Workflows

This directory contains CI/CD workflows for automated code quality checks.

## Workflows

### 1. Linter (`linter.yml`)

Runs code linting checks on both frontend and backend:

- **Frontend**: ESLint (via `npm run lint`)
- **Backend**: Flake8 (Python code style checker)

**Triggers:**
- Pull requests to `main` or `master` branches
- Pushes to `main` or `master` branches

### 2. Formatter (`formatter.yml`)

Checks code formatting consistency:

- **Frontend**: Prettier (checks formatting without modifying files)
- **Backend**: Black (checks Python code formatting)

**Triggers:**
- Pull requests to `main` or `master` branches
- Pushes to `main` or `master` branches

## Local Usage

### Frontend Formatting

```bash
# Check formatting
npm run format:check

# Auto-fix formatting
npm run format
```

### Backend Formatting

```bash
cd backend

# Check formatting
black --check .

# Auto-fix formatting
black .
```

### Backend Linting

```bash
cd backend

# Run Flake8
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

## Configuration Files

- `.prettierrc.json` - Prettier configuration for frontend
- `.prettierignore` - Files to exclude from Prettier
- `backend/.flake8` - Flake8 configuration for backend
- `backend/pyproject.toml` - Black configuration for backend

## Notes

- All workflows run in parallel for faster CI/CD
- Workflows fail if code doesn't meet quality standards
- Formatting checks are read-only (they check but don't modify files in CI)

