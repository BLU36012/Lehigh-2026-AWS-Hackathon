#!/usr/bin/env bash
# Deploy the Lehigh Valley Price Finder to AWS.
#   ./scripts/deploy.sh [stack-name] [region]
set -euo pipefail

STACK="${1:-lv-price-finder}"
REGION="${2:-us-east-1}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> 1/5  building dist/"
python scripts/build_site.py

echo "==> 2/5  deploying stack '$STACK' in $REGION (first run takes ~5 min for CloudFront)"
aws cloudformation deploy \
  --template-file infra/template.yaml \
  --stack-name "$STACK" \
  --capabilities CAPABILITY_IAM \
  --region "$REGION"

get() {
  aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text
}
BUCKET="$(get BucketName)"
DIST_ID="$(get DistributionId)"
TABLE="$(get TableName)"
URL="$(get SiteURL)"

echo "==> 3/5  loading DynamoDB table '$TABLE'"
python scripts/load_dynamo.py "$TABLE" --region "$REGION"

echo "==> 4/5  syncing dist/ to s3://$BUCKET"
# Long cache on the data file, none on the page, so a redeploy is picked up at once.
aws s3 sync dist/ "s3://$BUCKET/" --region "$REGION" --delete \
  --exclude index.html \
  --cache-control "public, max-age=3600"
aws s3 cp dist/index.html "s3://$BUCKET/index.html" --region "$REGION" \
  --content-type "text/html; charset=utf-8" \
  --cache-control "no-cache"

echo "==> 5/5  invalidating CloudFront"
aws cloudfront create-invalidation --distribution-id "$DIST_ID" \
  --paths "/*" --query "Invalidation.Id" --output text

echo
echo "Live at: $URL"
echo "(a brand-new distribution can take a few more minutes to finish propagating)"
