# Secrets Management

This project uses a `secrets.yaml` file to store all your actual credentials, API keys, passwords, and configuration values in one place.

## Setup

1. **Create your secrets file:**
   ```bash
   # The secrets.yaml file already exists as a template
   # Just edit it and fill in your actual values
   nano secrets.yaml
   # or use your preferred editor
   ```

2. **Fill in all your credentials:**
   - Snowflake credentials
   - TransitApp API key
   - AWS credentials and account ID
   - OpenAI API key
   - Any other secrets you need

3. **Load secrets into environment:**
   ```bash
   # Option 1: Use the shell script (recommended)
   source scripts/load_secrets.sh
   
   # Option 2: Use Python script directly
   source <(python scripts/load_secrets.sh)
   
   # Option 3: Show what would be exported (for debugging)
   python scripts/load_secrets.py --show
   ```

## How It Works

1. **secrets.yaml** - Your actual credentials (NOT in git)
2. **master_config.yaml** - Template with placeholders (in git)
3. **load_secrets.sh** / **load_secrets.py** - Scripts that read secrets.yaml and export to environment variables

When you run `source scripts/load_secrets.sh`, it:
- Reads all key-value pairs from `secrets.yaml`
- Flattens any nested structure
- Substitutes variables (e.g., `{AWS_ACCOUNT_ID}`)
- Exports everything as environment variables

## Usage in Your Workflow

```bash
# At the start of your work session
cd /Users/spartan/Documents/MSDA/Project/transit-system
source scripts/load_secrets.sh

# Now all your secrets are available as environment variables
echo $SNOWFLAKE_ACCOUNT
echo $TRANSIT_APP_API_KEY
# etc.

# All tools will automatically use these:
# - dbt (via profiles.yml using env_var())
# - Python scripts
# - Airflow (if configured)
# - Local testing scripts
```

## Security Notes

⚠️ **Important:**
- `secrets.yaml` is already in `.gitignore` and will NOT be committed
- Never commit this file or share it
- Keep it secure on your local machine only
- The `master_config.yaml` file has placeholders and IS in git (this is safe)

## File Structure

```
transit-system/
├── secrets.yaml              # YOUR actual credentials (NOT in git)
├── config/
│   └── master_config.yaml    # Template with placeholders (in git)
└── scripts/
    ├── load_secrets.sh       # Shell script to load secrets
    └── load_secrets.py       # Python script to load secrets
```

## Variable Substitution

The script supports variable substitution. For example:

```yaml
AWS_ACCOUNT_ID: "123456789012"
AWS_S3_RAW_BUCKET: "transit-raw-data-{AWS_ACCOUNT_ID}"
```

Will export:
- `AWS_ACCOUNT_ID=123456789012`
- `AWS_S3_RAW_BUCKET=transit-raw-data-123456789012`

## Troubleshooting

**Issue:** "Secrets file not found"
- Make sure `secrets.yaml` exists in the project root
- Check the path is correct

**Issue:** "PyYAML not installed"
```bash
pip install pyyaml
```

**Issue:** Variables not being exported
- Make sure you're using `source` not just running the script
- Check that values in secrets.yaml are not empty or None
- Verify YAML syntax is correct

