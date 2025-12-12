# How to Fix GitHub Actions Workflow Failures

## Understanding the Failures

When workflows fail, it usually means:
1. **Linting errors** - Code doesn't follow style rules
2. **Formatting issues** - Code isn't properly formatted
3. **Missing dependencies** - Package installation issues

## Quick Fix Steps

### Option 1: Fix Locally and Push

#### Frontend Formatting:
```bash
# Install dependencies
npm install

# Auto-fix formatting
npm run format

# Check linting
npm run lint
```

#### Backend Formatting:
```bash
cd backend

# Install dependencies
pip install black flake8

# Auto-fix formatting
black .

# Check linting
flake8 . --count --max-complexity=10 --max-line-length=127
```

Then commit and push:
```bash
git add .
git commit -m "Fix: Auto-format code"
git push
```

### Option 2: Check GitHub Actions Logs

1. Go to: https://github.com/AnanthAkshay/AstroSense/actions
2. Click on the failed workflow
3. Click on the failed job (e.g., "ESLint (Frontend)")
4. Expand the failed step to see the exact error
5. Fix the issues shown in the logs

### Option 3: Make Workflows More Lenient (Temporary)

If you want workflows to pass while you fix issues, you can temporarily make them non-blocking:

Edit `.github/workflows/linter.yml` and `.github/workflows/formatter.yml`:
- Change `continue-on-error: false` to `continue-on-error: true`

**Note:** This is only for temporary use. Fix the actual issues as soon as possible.

## Common Issues and Solutions

### Issue: "Prettier found formatting issues"
**Solution:**
```bash
npm run format
git add .
git commit -m "Fix: Format code with Prettier"
git push
```

### Issue: "Black found formatting issues"
**Solution:**
```bash
cd backend
black .
git add .
git commit -m "Fix: Format Python code with Black"
git push
```

### Issue: "ESLint found issues"
**Solution:**
```bash
npm run lint
# Fix the issues shown, then:
git add .
git commit -m "Fix: Resolve ESLint issues"
git push
```

### Issue: "Flake8 found issues"
**Solution:**
```bash
cd backend
flake8 . --count --max-complexity=10 --max-line-length=127
# Fix the issues shown, then:
git add .
git commit -m "Fix: Resolve Flake8 issues"
git push
```

## Verify Fixes

After fixing, the workflows should show:
- ✅ Green checkmark = Success
- ❌ Red X = Still has issues (check logs again)

## Need Help?

If workflows still fail after trying these steps:
1. Check the detailed logs in GitHub Actions
2. Share the specific error message
3. We can help fix the specific issues

