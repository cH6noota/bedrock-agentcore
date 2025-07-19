
import boto3


region = 'us-east-1'
agent_runtime_id= 'strands_agents_fastapi-mYgIt42Juw'
repo_name = 'bedrock-agentcore/fastapi'
role_arn = "xx"

sts = boto3.client('sts', region_name=region)
account_id = sts.get_caller_identity()['Account']
container_uri = f'{account_id}.dkr.ecr.{region}.amazonaws.com/{repo_name}:latest'

client = boto3.client('bedrock-agentcore-control', region_name=region)

response = client.update_agent_runtime(
    agentRuntimeId=agent_runtime_id,
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
