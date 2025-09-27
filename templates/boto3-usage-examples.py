#!/usr/bin/env python3
"""
AWS Boto3 Usage Examples
Standardized patterns for loading AWS credentials and using boto3 clients.
"""
import os
import boto3
from pathlib import Path
from typing import Optional, Dict, Any

def load_aws_credentials_from_file(credentials_path: Optional[str] = None) -> Dict[str, str]:
    """
    Load AWS credentials from common runtime resources file.
    
    Args:
        credentials_path: Path to credentials file. If None, uses default location.
        
    Returns:
        Dictionary with AWS credential keys
        
    Raises:
        FileNotFoundError: If credentials file doesn't exist
        ValueError: If credentials file format is invalid
    """
    if credentials_path is None:
        # Default path relative to project directory
        credentials_path = Path(__file__).parent.parent / "credentials.txt"
    
    credentials_path = Path(credentials_path)
    
    if not credentials_path.exists():
        raise FileNotFoundError(f"AWS credentials file not found: {credentials_path}")
    
    credentials = {}
    
    try:
        with open(credentials_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=VALUE format
                if '=' not in line:
                    continue
                
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'')  # Remove quotes
                
                credentials[key] = value
        
        # Validate required credentials
        required_keys = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
        missing_keys = [key for key in required_keys if key not in credentials]
        
        if missing_keys:
            raise ValueError(f"Missing required credentials: {missing_keys}")
        
        return credentials
        
    except Exception as e:
        raise ValueError(f"Error parsing credentials file: {e}")

def setup_aws_environment(credentials_path: Optional[str] = None) -> None:
    """
    Set up AWS environment variables from credentials file.
    
    Args:
        credentials_path: Path to credentials file. If None, uses default location.
    """
    credentials = load_aws_credentials_from_file(credentials_path)
    
    # Set environment variables for boto3
    for key, value in credentials.items():
        os.environ[key] = value
    
    print(f"✅ AWS environment configured with {len(credentials)} variables")

def create_boto3_client(service_name: str, region_name: str = 'us-west-2') -> Any:
    """
    Create boto3 client with standardized configuration.
    
    Args:
        service_name: AWS service name (e.g., 'lambda', 's3', 'dynamodb')
        region_name: AWS region name
        
    Returns:
        Configured boto3 client
        
    Example:
        >>> lambda_client = create_boto3_client('lambda', 'us-west-2')
        >>> response = lambda_client.list_functions()
    """
    try:
        # Ensure credentials are loaded
        if not os.environ.get('AWS_ACCESS_KEY_ID'):
            setup_aws_environment()
        
        client = boto3.client(service_name, region_name=region_name)
        
        # Test the client with a simple operation
        if service_name == 'lambda':
            # Test Lambda client
            try:
                client.list_functions(MaxItems=1)
                print(f"✅ {service_name} client configured successfully")
            except Exception as e:
                print(f"⚠️  {service_name} client created but test failed: {e}")
        
        return client
        
    except Exception as e:
        print(f"❌ Failed to create {service_name} client: {e}")
        raise

def create_lambda_client(region_name: str = 'us-west-2'):
    """
    Create Lambda client with error handling.
    
    Args:
        region_name: AWS region for Lambda functions
        
    Returns:
        Configured Lambda client
    """
    return create_boto3_client('lambda', region_name)

def deploy_lambda_function(function_name: str, zip_file_path: str, 
                          region_name: str = 'us-west-2') -> Dict[str, Any]:
    """
    Deploy Lambda function using boto3.
    
    Args:
        function_name: Name of the Lambda function
        zip_file_path: Path to deployment package zip file
        region_name: AWS region
        
    Returns:
        Lambda update response
        
    Raises:
        FileNotFoundError: If zip file doesn't exist
        Exception: If deployment fails
    """
    zip_path = Path(zip_file_path)
    
    if not zip_path.exists():
        raise FileNotFoundError(f"Deployment package not found: {zip_path}")
    
    # Check file size (AWS Lambda limit is 50MB)
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    if size_mb > 50:
        raise ValueError(f"Package too large: {size_mb:.1f}MB (AWS limit: 50MB)")
    
    lambda_client = create_lambda_client(region_name)
    
    try:
        print(f"📦 Deploying {function_name} from {zip_path.name} ({size_mb:.1f}MB)")
        
        with open(zip_path, 'rb') as zip_file:
            response = lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_file.read()
            )
        
        print(f"✅ Successfully deployed {function_name}")
        print(f"   Last Modified: {response.get('LastModified')}")
        print(f"   Code Size: {response.get('CodeSize', 0) / 1024:.1f} KB")
        
        return response
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        raise

def test_lambda_function(function_name: str, test_payload: Dict[str, Any],
                        region_name: str = 'us-west-2') -> Dict[str, Any]:
    """
    Test Lambda function with payload and capture logs.
    
    Args:
        function_name: Name of the Lambda function
        test_payload: Test payload to send
        region_name: AWS region
        
    Returns:
        Lambda response with parsed payload and logs
    """
    import json
    import base64
    
    lambda_client = create_lambda_client(region_name)
    
    try:
        print(f"🧪 Testing {function_name} with payload...")
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(test_payload),
            LogType='Tail'  # Include execution logs
        )
        
        # Parse response payload
        payload_response = json.loads(response['Payload'].read())
        
        # Extract and decode logs
        logs = ""
        if 'LogResult' in response:
            logs = base64.b64decode(response['LogResult']).decode('utf-8')
        
        print(f"✅ Lambda execution completed")
        print(f"   Status Code: {payload_response.get('statusCode', 'unknown')}")
        
        return {
            'response': payload_response,
            'logs': logs,
            'execution_time': response.get('ResponseMetadata', {}).get('HTTPHeaders', {}).get('x-amz-function-execution-time', 'unknown')
        }
        
    except Exception as e:
        print(f"❌ Lambda test failed: {e}")
        raise

# Example usage patterns
if __name__ == '__main__':
    """
    Example usage of AWS credential loading and boto3 clients.
    """
    
    print("AWS Boto3 Usage Examples")
    print("=" * 40)
    
    try:
        # 1. Load credentials from file
        print("\n1. Loading AWS credentials...")
        setup_aws_environment()
        
        # 2. Create Lambda client
        print("\n2. Creating Lambda client...")
        lambda_client = create_lambda_client()
        
        # 3. List Lambda functions (test)
        print("\n3. Testing Lambda client...")
        functions = lambda_client.list_functions(MaxItems=5)
        print(f"   Found {len(functions.get('Functions', []))} Lambda functions")
        
        # 4. Example deployment (commented out)
        print("\n4. Example deployment (disabled):")
        print("   # deploy_lambda_function('my-function', 'package.zip')")
        
        # 5. Example testing (commented out)
        print("\n5. Example testing (disabled):")
        print("   # test_lambda_function('my-function', {'test': 'data'})")
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure credentials.txt exists in common-runtime-resources/")
        print("2. Check AWS credentials are valid")
        print("3. Verify network connectivity to AWS")