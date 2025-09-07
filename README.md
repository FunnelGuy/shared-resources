# Common Runtime Resources

This repository contains shared runtime resources used across all applications in the development environment.

## Purpose

This repository stores runtime configurations, credentials, and shared resources that applications need during execution. It serves as the centralized location for:

- AWS credentials and configuration files
- API keys and authentication tokens
- Shared configuration files
- Runtime templates and defaults
- Environment-specific settings

## Repository Structure

```
common-runtime-resources/
├── README.md              # This documentation
├── .gitignore            # Excludes sensitive files from commits
├── credentials.txt       # AWS credentials (gitignored)
├── templates/            # Configuration templates
│   ├── credentials.template.txt
│   └── config.template.json
└── shared-configs/       # Non-sensitive shared configurations
    ├── regions.json      # AWS regions and defaults
    └── endpoints.json    # API endpoints and URLs
```

## Development Environment Integration

This repository is part of the organized development environment:

```
C:\Development\
├── common-runtime-resources/  # Runtime resources (this repository)
├── shared-dev-protocols/      # Development workflow standards  
└── [application-repositories] # Individual applications
```

### Key Distinction
- **common-runtime-resources/**: Application runtime needs (credentials, configs)
- **shared-dev-protocols/**: Development workflow standards (branch protocols, guidelines)

## Usage by Applications

Applications reference runtime resources using relative paths:

```python
# Example: Loading AWS credentials
credentials_path = "../common-runtime-resources/credentials.txt"

# Example: Loading shared configuration
config_path = "../common-runtime-resources/shared-configs/regions.json"
```

## Security Guidelines

### ⚠️ **CRITICAL SECURITY NOTICE**

**NEVER commit sensitive credentials or secrets to this repository.**

The `.gitignore` file excludes sensitive files, but always verify before committing:

```bash
# Always check what you're committing
git status
git diff --cached

# Only commit non-sensitive configuration files
```

### Sensitive Files (Excluded from Git)
- `credentials.txt` - AWS access keys
- `*.key` - Private keys
- `api-keys.txt` - API authentication tokens
- `.env` - Environment variables with secrets

### Safe to Commit
- `templates/` - Template files with placeholders
- `shared-configs/` - Non-sensitive configuration
- `README.md` - Documentation
- `.gitignore` - Security exclusions

## Setup Instructions

### For New Team Members

1. **Clone this repository**:
   ```bash
   cd C:\Development
   git clone https://github.com/FunnelGuy/common-runtime-resources.git
   # Or rename from existing Common/ directory
   ```

2. **Create sensitive files from templates**:
   ```bash
   cd common-runtime-resources
   cp templates/credentials.template.txt credentials.txt
   ```

3. **Add your actual credentials**:
   - Edit `credentials.txt` with real AWS keys
   - Never commit this file (it's gitignored)

4. **Verify security**:
   ```bash
   git status  # Should not show credentials.txt
   ```

### For Existing Setup

If you already have a `Common/` directory:

1. **Initialize as repository** (already done)
2. **Add templates and documentation** (included here)
3. **Verify sensitive files are excluded**:
   ```bash
   git status  # credentials.txt should not appear
   ```

## Configuration Templates

### AWS Credentials Template
File: `templates/credentials.template.txt`
```
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-west-2
```

### Application Configuration Template
File: `templates/config.template.json`
```json
{
  "aws_region": "us-west-2",
  "api_endpoints": {
    "bedrock": "https://bedrock.us-west-2.amazonaws.com"
  },
  "timeouts": {
    "api_timeout": 30,
    "retry_attempts": 3
  }
}
```

## Applications Using These Resources

This runtime resource repository supports:

- **Proposal Reviewer**: AWS Bedrock credentials, Claude API configuration
- **Networker**: LinkedIn API keys, automation settings
- **Availability Windows**: Calendar API credentials, timezone configurations
- **Contact Details Extractor**: Data source API keys, export configurations  
- **Padding Outlook**: Exchange credentials, calendar settings

## Contributing

### Adding New Resources

1. **Create templates first**:
   ```bash
   # Add template with placeholders
   git add templates/new-config.template.json
   ```

2. **Document usage**:
   - Update this README with new resource description
   - Add to application documentation

3. **Test with applications**:
   - Verify applications can load new resources
   - Test with template files before adding real data

### Best Practices

- **Always use templates** for sensitive configurations
- **Document all resources** in this README
- **Test changes** with dependent applications
- **Never commit sensitive data**
- **Use descriptive commit messages**

## Troubleshooting

### Common Issues

**Applications can't find credentials**:
- Verify file exists: `C:\Development\common-runtime-resources/credentials.txt`
- Check file permissions and format
- Verify relative path from application directory

**Git trying to commit sensitive files**:
- Check `.gitignore` includes the file pattern
- Use `git status` to verify exclusion
- Remove from staging: `git reset HEAD filename`

**Template files not working**:
- Copy template to actual filename: `cp template.txt actual.txt`
- Replace placeholders with real values
- Verify application can parse the format

## Migration from Directory to Repository

If migrating from existing `Common/` directory:

1. **Backup existing files**:
   ```bash
   cp -r Common/ Common-backup/
   ```

2. **Initialize repository** (completed)
3. **Add documentation and templates** (completed)
4. **Verify security exclusions work**:
   ```bash
   git status  # Should not show credentials.txt
   ```

5. **Update application references** (if needed)
6. **Create GitHub repository and push**

## Future Enhancements

- Environment-specific configurations (dev, staging, prod)
- Encrypted credential storage
- Automatic credential rotation support
- Configuration validation scripts