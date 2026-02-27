#!/usr/bin/env python3
"""
Configure AWS access for Databricks operations
Handles S3 access for Delta tables, model storage, etc.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def configure_aws_credentials():
    """
    Configure AWS credentials from environment variables
    """

    # Load from .env file if exists
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✓ Loaded credentials from {env_file}")

    # Check required AWS environment variables
    required_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY'
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nTo configure AWS access:")
        print("1. Copy .env.example to .env")
        print("2. Fill in your AWS credentials")
        print("3. Run this script again")
        return False

    # Optional session token for temporary credentials
    if os.getenv('AWS_SESSION_TOKEN'):
        print("✓ Using temporary AWS credentials (session token present)")
    else:
        print("✓ Using permanent AWS credentials")

    print(f"✓ AWS Region: {os.getenv('AWS_REGION', 'us-east-1')}")

    return True

def configure_databricks_spark_session():
    """
    Configure Spark session with AWS credentials for Databricks
    """

    from pyspark.sql import SparkSession

    # Get credentials from environment
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_session_token = os.getenv('AWS_SESSION_TOKEN')

    # Build Spark session with AWS configuration
    builder = SparkSession.builder \
        .appName("MLRecommendationPipeline") \
        .config("spark.hadoop.fs.s3a.access.key", aws_access_key) \
        .config("spark.hadoop.fs.s3a.secret.key", aws_secret_key)

    # Add session token if using temporary credentials
    if aws_session_token:
        builder = builder.config("spark.hadoop.fs.s3a.session.token", aws_session_token)

    # Additional S3 configurations
    builder = builder \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.endpoint", "s3.amazonaws.com") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "true") \
        .config("spark.hadoop.fs.s3a.fast.upload", "true") \
        .config("spark.hadoop.fs.s3a.block.size", "128M") \
        .config("spark.hadoop.fs.s3a.multipart.size", "128M")

    spark = builder.getOrCreate()

    print("✓ Spark session configured with AWS credentials")

    # Test S3 access if needed
    test_s3_access(spark)

    return spark

def test_s3_access(spark):
    """
    Test S3 access with configured credentials
    """

    test_bucket = os.getenv('S3_TEST_BUCKET', 'databricks-ml-models')
    test_path = f"s3a://{test_bucket}/"

    try:
        # Try to list files in the bucket
        print(f"\nTesting S3 access to {test_path}")
        df = spark.read.format("parquet").load(test_path)
        print(f"✓ Successfully accessed S3 bucket: {test_bucket}")
        return True
    except Exception as e:
        if "test" in test_bucket:
            # Expected if using default test bucket
            print(f"ℹ️ S3 test skipped (test bucket not configured)")
        else:
            print(f"⚠️ Could not access S3: {str(e)}")
        return False

def setup_databricks_cli():
    """
    Configure Databricks CLI with credentials
    """

    import subprocess

    databricks_host = os.getenv('DATABRICKS_HOST')
    databricks_token = os.getenv('DATABRICKS_TOKEN')

    if not databricks_host or not databricks_token:
        print("⚠️ Databricks credentials not configured")
        return False

    # Configure Databricks CLI
    try:
        # Create .databrickscfg file
        databricks_cfg = Path.home() / '.databrickscfg'

        config_content = f"""[DEFAULT]
host = {databricks_host}
token = {databricks_token}

[aws]
host = {databricks_host}
token = {databricks_token}
aws_region = {os.getenv('AWS_REGION', 'us-east-1')}
"""

        databricks_cfg.write_text(config_content)
        databricks_cfg.chmod(0o600)  # Secure file permissions

        print(f"✓ Databricks CLI configured at {databricks_cfg}")

        # Test connection
        result = subprocess.run(
            ["databricks", "workspace", "ls", "/"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("✓ Successfully connected to Databricks workspace")
            return True
        else:
            print(f"⚠️ Could not connect to Databricks: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error configuring Databricks CLI: {str(e)}")
        return False

def main():
    """
    Complete AWS and Databricks configuration
    """

    print("""
╔══════════════════════════════════════════════════════════════╗
║           AWS & DATABRICKS CONFIGURATION                    ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Step 1: Configure AWS credentials
    print("\n1. Configuring AWS Credentials...")
    if not configure_aws_credentials():
        sys.exit(1)

    # Step 2: Setup Databricks CLI
    print("\n2. Configuring Databricks CLI...")
    setup_databricks_cli()

    # Step 3: Configure Spark session (if in Databricks environment)
    if 'DATABRICKS_RUNTIME_VERSION' in os.environ:
        print("\n3. Configuring Spark Session...")
        spark = configure_databricks_spark_session()
    else:
        print("\n3. Not in Databricks environment - skipping Spark configuration")

    print("\n" + "="*60)
    print("✅ CONFIGURATION COMPLETE")
    print("="*60)

    print("\nYou can now:")
    print("• Access S3 buckets from Databricks")
    print("• Use MLflow with S3 artifact storage")
    print("• Read/write Delta tables on S3")
    print("• Access AWS services (DynamoDB, Kinesis, etc.)")

    # Show example usage
    print("\nExample usage in Databricks notebook:")
    print("""
# Read Delta table from S3
df = spark.read.format("delta").load("s3a://your-bucket/path/to/delta/table")

# Write to S3
df.write.format("delta").mode("append").save("s3a://your-bucket/output/path")

# Load MLflow model from S3
import mlflow
model = mlflow.pyfunc.load_model("s3://your-bucket/models/model-name/version")
    """)

if __name__ == "__main__":
    main()