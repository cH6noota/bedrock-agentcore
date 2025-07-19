# アカウントIDを取得
account_id=$(aws sts get-caller-identity --query Account --output text)

# ECRにログイン
aws ecr get-login-password --region us-east-1 | \
  podman login --username AWS --password-stdin "${account_id}.dkr.ecr.us-east-1.amazonaws.com"

# イメージをビルド
podman build --platform linux/arm64 \
  -t "${account_id}.dkr.ecr.us-east-1.amazonaws.com/bedrock-agentcore/fastapi:latest" \
  .

# イメージをECRにプッシュ
podman push "${account_id}.dkr.ecr.us-east-1.amazonaws.com/bedrock-agentcore/fastapi:latest"