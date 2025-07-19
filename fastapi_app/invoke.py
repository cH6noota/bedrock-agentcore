import boto3
import json
import uuid

runtime_session_id = str(uuid.uuid4())

agentRuntimeArn = 'xx'


agent_core_client = boto3.client('bedrock-agentcore', region_name='us-east-1')
payload = json.dumps({
    "input": {"prompt": "こんにちは"}
})

response = agent_core_client.invoke_agent_runtime(
    agentRuntimeArn=agentRuntimeArn,
    runtimeSessionId=runtime_session_id,
    payload=payload,
    qualifier="DEFAULT"
)

response_body = response['response'].read()
response_data = json.loads(response_body)
print("Agent Response:", response_data)