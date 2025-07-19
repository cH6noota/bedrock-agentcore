import boto3
import json
import time

def create_agentcore_role(agent_name, region='us-east-1'):
    iam_client = boto3.client('iam', region_name=region)
    sts_client = boto3.client('sts', region_name=region)
    account_id = sts_client.get_caller_identity()["Account"]
    role_name = f'agentcore-{agent_name}-role'

    # IAMポリシー
    role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "BedrockPermissions",
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "Resource": ["*"]
            },
            {
                "Sid": "ECRImageAccess",
                "Effect": "Allow",
                "Action": [
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer"
                ],
                "Resource": [
                    f"arn:aws:ecr:{region}:{account_id}:repository/*"
                ]
            },
            {
                "Sid": "LogsCreateAndDescribe",
                "Effect": "Allow",
                "Action": [
                    "logs:DescribeLogStreams",
                    "logs:CreateLogGroup"
                ],
                "Resource": [
                    f"arn:aws:logs:{region}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*"
                ]
            },
            {
                "Sid": "LogsDescribeGroups",
                "Effect": "Allow",
                "Action": [
                    "logs:DescribeLogGroups"
                ],
                "Resource": [
                    f"arn:aws:logs:{region}:{account_id}:log-group:*"
                ]
            },
            {
                "Sid": "LogsPutEvents",
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": [
                    f"arn:aws:logs:{region}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*"
                ]
            },
            {
                "Sid": "ECRTokenAccess",
                "Effect": "Allow",
                "Action": [
                    "ecr:GetAuthorizationToken"
                ],
                "Resource": ["*"]
            },
            {
                "Sid": "XRayAccess",
                "Effect": "Allow",
                "Action": [
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                    "xray:GetSamplingRules",
                    "xray:GetSamplingTargets"
                ],
                "Resource": ["*"]
            },
            {
                "Sid": "CloudWatchMetrics",
                "Effect": "Allow",
                "Action": ["cloudwatch:PutMetricData"],
                "Resource": ["*"]
            },
            {
                "Sid": "GetAgentAccessToken",
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:GetWorkloadAccessToken",
                    "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
                    "bedrock-agentcore:GetWorkloadAccessTokenForUserId"
                ],
                "Resource": [
                    f"arn:aws:bedrock-agentcore:{region}:{account_id}:workload-identity-directory/default",
                    f"arn:aws:bedrock-agentcore:{region}:{account_id}:workload-identity-directory/default/workload-identity/{agent_name}-*"
                ]
            }
        ]
    }

    # AssumeRoleポリシー
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AssumeRolePolicy",
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock-agentcore.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }

    # ロール作成
    try:
        role = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy)
        )
        time.sleep(10)
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"Role '{role_name}' already exists. Recreating...")
        # 既存ロール削除
        policies = iam_client.list_role_policies(RoleName=role_name)
        for policy_name in policies['PolicyNames']:
            iam_client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
        iam_client.delete_role(RoleName=role_name)
        time.sleep(10)
        role = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy)
        )
        time.sleep(10)
    except Exception as e:
        print(f"Error creating role: {e}")
        return None

    # インラインポリシー付与
    try:
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName="AgentCorePolicy",
            PolicyDocument=json.dumps(role_policy)
        )
        time.sleep(10)
    except Exception as e:
        print(f"Error attaching policy: {e}")
        return None

    print(f"Role '{role_name}' created and policy attached.")
    return role['Role']['Arn']

def create_agent_runtime(agent_runtime_name, container_uri, role_arn, region='us-east-1'):
    client = boto3.client('bedrock-agentcore-control', region_name=region)
    try:
        response = client.create_agent_runtime(
            agentRuntimeName=agent_runtime_name,
            agentRuntimeArtifact={
                'containerConfiguration': {
                    'containerUri': container_uri
                }
            },
            networkConfiguration={"networkMode": "PUBLIC"},
            roleArn=role_arn
        )
        print("Agent Runtime created successfully!")
        print(f"Agent Runtime ARN: {response['agentRuntimeArn']}")
        print(f"Status: {response['status']}")
        return response
    except Exception as e:
        print(f"Error creating agent runtime: {e}")
        return None

if __name__ == "__main__":
    region = 'us-east-1'
    agent_name = "strands_agents_fastapi"
    agent_runtime_name = "strands_agents_fastapi"
    repo_name = 'bedrock-agentcore/fastapi'

    sts = boto3.client('sts', region_name=region)
    account_id = sts.get_caller_identity()['Account']
    container_uri = f'{account_id}.dkr.ecr.{region}.amazonaws.com/{repo_name}:latest'

    # 1. IAMロール作成
    role_arn = create_agentcore_role(agent_name, region=region)
    if not role_arn:
        print("Failed to create IAM role. Exiting.")
        exit(1)

    # 2. Agent Runtime作成
    create_agent_runtime(agent_runtime_name, container_uri, role_arn, region=region)