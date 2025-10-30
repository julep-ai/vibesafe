# Claude-Powered GitHub Actions

This repository uses Claude AI to provide automated code review and test failure analysis through GitHub Actions.

## Features

### 1. Automated Code Review (`claude-review.yml`)

Automatically reviews pull requests using Claude Sonnet 4, providing:
- Summary of changes
- Code quality observations
- Security and performance concerns
- Suggestions for improvement

**Triggers:** When a PR is opened, synchronized, or reopened against `main` or `develop` branches.

**Requirements:**
- `ANTHROPIC_API_KEY` secret configured in repository settings

### 2. Test Failure Analysis (`claude-test-analysis.yml`)

Analyzes test failures from CI runs and provides:
- Root cause analysis
- Debugging steps
- Classification (flaky test, environment issue, or real bug)
- Priority assessment

**Triggers:** When the CI workflow completes with failures.

**Requirements:**
- `ANTHROPIC_API_KEY` secret configured in repository settings

## Setup Instructions

### 1. Get an Anthropic API Key

1. Sign up at [console.anthropic.com](https://console.anthropic.com)
2. Generate an API key from the API Keys section
3. Copy the key (starts with `sk-ant-`)

### 2. Configure GitHub Repository Secret

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `ANTHROPIC_API_KEY`
5. Value: Paste your Anthropic API key
6. Click **Add secret**

### 3. Verify Workflows

Once the secret is configured, the workflows will automatically run:

- **Code Review**: On every PR update
- **Test Analysis**: When tests fail in CI

You can verify they're working by:
1. Creating a test PR
2. Checking the "Actions" tab
3. Looking for comments from the GitHub Actions bot on your PR

## Workflow Details

### Claude Review Workflow

**Location:** `.github/workflows/claude-review.yml`

**Permissions Required:**
- `contents: read` - Read repository code
- `pull-requests: write` - Post review comments
- `issues: write` - Update comments

**Configuration:**
- **Model:** `claude-sonnet-4-20250514` (latest Sonnet 4)
- **Max Tokens:** 2000
- **Diff Limit:** 50,000 characters (truncated if larger)
- **File Limit:** First 20 changed files

**How it works:**
1. Fetches PR diff and changed files
2. Sends context to Claude API with review prompt
3. Posts review as a comment on the PR
4. Updates existing comment on subsequent runs (doesn't spam)

### Test Failure Analysis Workflow

**Location:** `.github/workflows/claude-test-analysis.yml`

**Permissions Required:**
- `contents: read` - Read repository code
- `pull-requests: write` - Post analysis comments
- `issues: write` - Update comments
- `actions: read` - Access workflow logs

**Configuration:**
- **Model:** `claude-sonnet-4-20250514`
- **Max Tokens:** 2000
- **Log Limit:** Last 2000 characters per failed job
- **Job Limit:** First 3 failed jobs analyzed

**How it works:**
1. Triggered when CI workflow fails
2. Downloads logs from failed jobs
3. Sends failure context to Claude API
4. Posts analysis on the associated PR
5. Updates existing comment on subsequent failures

## Cost Considerations

### API Usage Estimates

**Code Review:**
- Average tokens per review: ~1500-2000 (input) + ~800-1500 (output)
- Cost per review: ~$0.03-0.05 USD
- Typical monthly cost: $5-15 (for 100-300 PRs)

**Test Analysis:**
- Average tokens per analysis: ~1000-1500 (input) + ~800-1200 (output)
- Cost per analysis: ~$0.02-0.04 USD
- Typical monthly cost: $2-10 (for 50-250 failures)

**Total estimated cost:** $7-25/month for active development

### Cost Optimization

To reduce costs:

1. **Limit review to specific branches:**
   ```yaml
   on:
     pull_request:
       branches: [ main ]  # Only main, not develop
   ```

2. **Skip draft PRs:** (already configured)
   ```yaml
   if: github.event.pull_request.draft == false
   ```

3. **Use Claude Haiku for reviews:**
   Change model to `claude-3-5-haiku-20241022` (~80% cost reduction)

4. **Disable test analysis:**
   Delete or disable `claude-test-analysis.yml`

## Customization

### Modify Review Focus

Edit the prompt in `claude-review.yml` to focus on specific concerns:

```python
prompt = f"""Review this PR focusing on:
1. Security vulnerabilities
2. Performance regressions
3. Breaking API changes
...
"""
```

### Change Model

To use a different Claude model, update the `model` field:

```python
data = {
    "model": "claude-3-5-haiku-20241022",  # Faster, cheaper
    # or
    "model": "claude-opus-4-20250514",  # More thorough, expensive
    ...
}
```

### Adjust Token Limits

For longer or shorter responses:

```python
data = {
    "max_tokens": 4000,  # Increase for more detailed reviews
    ...
}
```

## Troubleshooting

### Reviews Not Appearing

1. **Check API key:**
   - Verify `ANTHROPIC_API_KEY` is set in repository secrets
   - Ensure key is valid and has credits

2. **Check workflow permissions:**
   - Go to Settings → Actions → General
   - Ensure "Read and write permissions" is enabled

3. **Check workflow runs:**
   - Go to Actions tab
   - Look for failed Claude workflow runs
   - Check logs for error messages

### API Rate Limits

If you hit rate limits:
- Reduce frequency (only review on `main` branch)
- Add delays between API calls
- Contact Anthropic to increase limits

### Workflow Fails

Common issues:
- **401 Unauthorized:** Invalid API key
- **429 Too Many Requests:** Rate limit exceeded
- **Timeout:** Diff too large, increase timeout or reduce diff size

## Security Notes

- API keys are stored as encrypted GitHub secrets
- Keys are never exposed in logs or outputs
- Code diffs are sent to Anthropic's API (review their data policy)
- Workflows run in isolated GitHub Actions runners
- No write access to repository code (only comments)

## Disabling Claude Actions

To disable without deleting workflows:

1. **Disable in UI:**
   - Go to Actions tab
   - Find workflow
   - Click "..." → Disable workflow

2. **Remove API key:**
   - Delete `ANTHROPIC_API_KEY` from repository secrets
   - Workflows will skip Claude steps gracefully

3. **Delete workflows:**
   ```bash
   rm .github/workflows/claude-*.yml
   git add .github/workflows/
   git commit -m "Remove Claude Actions"
   ```

## Support

- **Claude API:** [docs.anthropic.com](https://docs.anthropic.com)
- **GitHub Actions:** [docs.github.com/actions](https://docs.github.com/actions)
- **Repository Issues:** Open an issue in this repository

## Examples

### Example Code Review Comment

```markdown
## 🤖 Claude Code Review

### Summary
This PR adds hash-based verification to the code generation pipeline,
ensuring generated implementations match their specifications. The changes
are well-structured and include comprehensive tests.

### Key Observations
- ✅ Strong type safety with Pydantic models
- ✅ Good test coverage (98% on hashing module)
- ⚠️ Consider caching hash computations for performance
- ⚠️ Error messages could be more descriptive for users

### Security
- ✅ SHA256 hashing is appropriate for this use case
- ✅ No hardcoded secrets or credentials

### Suggestions
1. Add benchmark tests for hash computation performance
2. Consider using functools.lru_cache for frequently computed hashes
3. Document the hash format in module docstrings
```

### Example Test Failure Analysis

```markdown
## 🔍 Claude Test Failure Analysis

### Root Cause
The test failure in `test_integration.py::test_complete_function_workflow`
is caused by a `FileNotFoundError` when loading the Jinja2 template. The
test creates a temporary directory but doesn't copy the template files.

### Debugging Steps
1. Check if `prompts/` directory exists in temp test directory
2. Verify template path resolution in `CodeGenerator.__init__`
3. Add fixture to copy templates to temp directory
4. Run test with `pytest -vv tests/test_integration.py::test_complete_function_workflow`

### Classification
**Real Bug** - Test environment setup issue, not a flaky test

### Priority
**Medium** - Doesn't affect production code, but blocks integration testing

### Suggested Fix
```python
@pytest.fixture
def temp_templates(tmp_path):
    template_dir = tmp_path / "prompts"
    template_dir.mkdir()
    shutil.copy("prompts/function.j2", template_dir)
    return template_dir
```
```

## License

These workflows are part of the Defless project and follow the same license terms.
