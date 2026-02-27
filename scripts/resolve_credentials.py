# /// script
# requires-python = ">=3.10"
# dependencies = ["boto3"]
# ///
"""Resolve agent credentials from AWS Secrets Manager + version-controlled config.

Fetches secrets from AWS Secrets Manager, merges them with a local config file
(containing non-secret settings like site IDs and brand colours), and writes
a single credentials JSON file in the format that agent scripts expect.

Usage (with uv — handles dependencies automatically):
    uv run resolve_credentials.py \
        --profile Admin-351596828163 \
        --agent knowledge-manager \
        --config ../Knowledge-Manager/configs/sharepoint.json \
        --output ../Knowledge-Manager/sp-credentials.json

This makes credentials machine-independent: clone repos, run `aws sso login`,
run this script, and all agent scripts work.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError, TokenRetrievalError
except ImportError:
    print("ERROR: boto3 is required. Install with: pip install boto3", file=sys.stderr)
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Agent mappings: define which Secrets Manager secrets each agent needs
# and how secret keys map to the output JSON keys.
#
# Structure:
#   agent-id -> list of (secret_suffix, key_mapping)
#   secret_suffix: appended to "claude-code/{agent}/" to form the full secret name
#   key_mapping: dict of {secret_key: output_key}
#     - If output_key is None, the secret_key is used as-is
# ---------------------------------------------------------------------------

AGENT_SECRETS = {
    "knowledge-manager": [
        (
            "azure-ad",
            {
                "tenant_id": "tenant_id",
                "client_id": "client_id",
                "client_secret": "client_secret",
            },
        ),
        (
            "openai",
            {
                "api_key": "openai_api_key",
            },
        ),
    ],
}

DEFAULT_REGION = "ap-southeast-2"
DEFAULT_PREFIX = "claude-code"


def fetch_secrets(session, agent: str, prefix: str) -> dict:
    """Fetch all secrets for an agent from AWS Secrets Manager."""
    if agent not in AGENT_SECRETS:
        logger.error(f"Unknown agent '{agent}'. Known agents: {', '.join(AGENT_SECRETS.keys())}")
        sys.exit(1)

    client = session.client("secretsmanager")
    merged = {}

    for secret_suffix, key_mapping in AGENT_SECRETS[agent]:
        secret_name = f"{prefix}/{agent}/{secret_suffix}"
        logger.info(f"Fetching secret: {secret_name}")

        try:
            response = client.get_secret_value(SecretId=secret_name)
            secret_data = json.loads(response["SecretString"])
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "ResourceNotFoundException":
                logger.error(f"Secret '{secret_name}' not found. Create it with:")
                logger.error(f'  aws secretsmanager create-secret --name "{secret_name}" '
                             f'--secret-string \'{{...}}\' --region {session.region_name} '
                             f'--profile {session.profile_name}')
                sys.exit(1)
            raise
        except (NoCredentialsError, TokenRetrievalError):
            logger.error("AWS credentials not available. Run: aws sso login --profile <profile>")
            sys.exit(1)

        # Map secret keys to output keys
        for secret_key, output_key in key_mapping.items():
            if secret_key in secret_data:
                merged[output_key] = secret_data[secret_key]
            else:
                logger.warning(f"Key '{secret_key}' not found in secret '{secret_name}'")

    return merged


def load_config(config_path: str) -> dict:
    """Load non-secret config from a version-controlled JSON file."""
    path = Path(config_path)
    if not path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve(profile: str, agent: str, config_path: str | None, output_path: str,
            region: str = DEFAULT_REGION, prefix: str = DEFAULT_PREFIX) -> None:
    """Main resolution: fetch secrets, merge with config, write output."""
    session = boto3.Session(profile_name=profile, region_name=region)

    # Start with config if provided
    if config_path:
        logger.info(f"Loading config from: {config_path}")
        result = load_config(config_path)
    else:
        result = {}

    # Fetch and merge secrets (secrets override config on key collision)
    secrets = fetch_secrets(session, agent, prefix)
    result.update(secrets)

    # Write output
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
        f.write("\n")

    logger.info(f"Credentials written to: {output}")
    logger.info(f"Keys: {', '.join(sorted(result.keys()))}")


def main():
    parser = argparse.ArgumentParser(
        description="Resolve agent credentials from AWS Secrets Manager + config.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--profile", required=True,
                        help="AWS CLI profile name (e.g., Admin-351596828163)")
    parser.add_argument("--agent", required=True,
                        help=f"Agent identifier. Known agents: {', '.join(AGENT_SECRETS.keys())}")
    parser.add_argument("--config",
                        help="Path to version-controlled config JSON to merge with secrets")
    parser.add_argument("--output", required=True,
                        help="Path to write the resolved credentials file")
    parser.add_argument("--region", default=DEFAULT_REGION,
                        help=f"AWS region (default: {DEFAULT_REGION})")
    parser.add_argument("--prefix", default=DEFAULT_PREFIX,
                        help=f"Secrets Manager prefix (default: {DEFAULT_PREFIX})")

    args = parser.parse_args()
    resolve(
        profile=args.profile,
        agent=args.agent,
        config_path=args.config,
        output_path=args.output,
        region=args.region,
        prefix=args.prefix,
    )


if __name__ == "__main__":
    main()
