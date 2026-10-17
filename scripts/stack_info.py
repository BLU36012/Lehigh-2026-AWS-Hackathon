"""Print the CloudFormation stack outputs (SiteURL, bucket, table, distribution).

    python scripts/stack_info.py --region us-east-1
    python scripts/stack_info.py --region us-east-1 --stack lv-price-finder
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from load_dynamo import die, resolve_region, preflight  # noqa: E402

from botocore.exceptions import ClientError  # noqa: E402


def arg(flag, default=None):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 >= len(sys.argv):
            die("%s needs a value" % flag)
        return sys.argv[i + 1]
    return default


stack = arg("--stack", "lv-price-finder")
session = preflight(resolve_region(arg("--region")), quiet=True)

try:
    info = session.client("cloudformation").describe_stacks(StackName=stack)["Stacks"][0]
except ClientError as e:
    die("Could not read stack '%s':\n  %s"
        % (stack, e.response["Error"].get("Message", e)))

print("%s  [%s]" % (stack, info["StackStatus"]))
print("-" * 60)
outputs = {o["OutputKey"]: o["OutputValue"] for o in info.get("Outputs", [])}
if not outputs:
    die("The stack reports no outputs. Did it finish creating?")
for k in ("SiteURL", "BucketName", "TableName", "DistributionId", "ApiEndpoint"):
    if k in outputs:
        print("  %-15s %s" % (k, outputs[k]))
print()
print("Open: %s" % outputs.get("SiteURL", "(no SiteURL output)"))
