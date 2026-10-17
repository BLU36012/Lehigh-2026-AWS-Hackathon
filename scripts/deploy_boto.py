"""Finish the deploy without the AWS CLI: DynamoDB + S3 + CloudFront.

Assumes the CloudFormation stack already exists (create it from the console or
with `aws cloudformation deploy`). Everything after that is API calls boto3 can
make on its own.

    python scripts/deploy_boto.py --region us-east-1
    python scripts/deploy_boto.py --region us-east-1 --stack lv-price-finder
    python scripts/deploy_boto.py --region us-east-1 --skip-data   # page only

Needs permission for: cloudformation:DescribeStacks, dynamodb:*Item/BatchWrite,
s3:PutObject, cloudfront:CreateInvalidation.
"""
import mimetypes, os, sys, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DIST = os.path.join(ROOT, "dist")
sys.path.insert(0, HERE)

from load_dynamo import die, resolve_region, preflight, build_items, load  # noqa: E402

try:
    from botocore.exceptions import ClientError
except ImportError:
    die("boto3 is not installed.\n  pip install boto3")

# Per-file headers. The page must not be cached or a redeploy stays invisible.
HEADERS = {
    ".html": ("text/html; charset=utf-8", "no-cache"),
    ".json": ("application/json", "public, max-age=3600"),
    ".css":  ("text/css; charset=utf-8", "public, max-age=3600"),
    ".js":   ("text/javascript; charset=utf-8", "public, max-age=3600"),
}

GOOD = ("CREATE_COMPLETE", "UPDATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE")


def arg(flag, default=None):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 >= len(sys.argv):
            die("%s needs a value" % flag)
        return sys.argv[i + 1]
    return default


def stack_outputs(session, stack):
    cfn = session.client("cloudformation")
    try:
        info = cfn.describe_stacks(StackName=stack)["Stacks"][0]
    except ClientError as e:
        msg = e.response["Error"].get("Message", str(e))
        if "does not exist" in msg:
            die("No CloudFormation stack named '%s' in %s.\n"
                "\n"
                "  Create it first, then re-run this script. Check the region\n"
                "  selector in the console matches --region."
                % (stack, session.region_name))
        die("Could not read the stack:\n  %s" % msg)

    status = info["StackStatus"]
    if status not in GOOD:
        die("Stack '%s' is in state %s, not a usable one.\n"
            "\n"
            "  ROLLBACK_COMPLETE means the create failed and must be deleted\n"
            "  before retrying. See the 'Recovering from a rollback' section of\n"
            "  DEPLOY.md." % (stack, status))

    return {o["OutputKey"]: o["OutputValue"] for o in info.get("Outputs", [])}


def upload(session, bucket):
    if not os.path.isdir(DIST):
        die("No dist/ directory - run 'python scripts/build_site.py' first.")
    s3 = session.client("s3")
    names = sorted(os.listdir(DIST))
    if not names:
        die("dist/ is empty - run 'python scripts/build_site.py' first.")

    for name in names:
        path = os.path.join(DIST, name)
        if not os.path.isfile(path):
            continue
        ext = os.path.splitext(name)[1].lower()
        ctype, cache = HEADERS.get(
            ext, (mimetypes.guess_type(name)[0] or "application/octet-stream",
                  "public, max-age=3600"))
        with open(path, "rb") as fh:
            s3.put_object(Bucket=bucket, Key=name, Body=fh.read(),
                          ContentType=ctype, CacheControl=cache)
        print("  %-16s %7.0f KB  %s" % (name, os.path.getsize(path) / 1024, cache))


def invalidate(session, dist_id):
    cf = session.client("cloudfront")
    res = cf.create_invalidation(
        DistributionId=dist_id,
        InvalidationBatch={
            "Paths": {"Quantity": 1, "Items": ["/*"]},
            "CallerReference": "deploy-%d" % time.time(),
        })
    return res["Invalidation"]["Id"]


def check(url):
    """CloudFront can take a few minutes on a fresh distribution; a failure
    here is not necessarily a broken deploy."""
    for path, label in (("/api/meta", "API"), ("/", "page")):
        try:
            req = urllib.request.Request(url + path,
                                         headers={"User-Agent": "deploy-check"})
            with urllib.request.urlopen(req, timeout=20) as r:
                body = r.read(80)
                print("  %-5s %s  %s" % (label, r.status,
                                         body[:60].decode("utf-8", "replace")))
        except urllib.error.HTTPError as e:
            print("  %-5s %s  <- %s" % (label, e.code, e.reason))
        except Exception as e:
            print("  %-5s no response yet (%s)" % (label, type(e).__name__))


def main():
    stack = arg("--stack", "lv-price-finder")
    region = resolve_region(arg("--region"))
    session = preflight(region)

    print("\n[1/4] reading stack '%s'" % stack)
    out = stack_outputs(session, stack)
    for k in ("SiteURL", "BucketName", "TableName", "DistributionId"):
        if k not in out:
            die("Stack output '%s' is missing. Is this the right stack?" % k)
        print("  %-15s %s" % (k, out[k]))

    if "--skip-data" in sys.argv:
        print("\n[2/4] skipping DynamoDB (--skip-data)")
    else:
        print("\n[2/4] loading DynamoDB")
        load(session, out["TableName"], build_items())

    print("\n[3/4] uploading dist/ to s3://%s" % out["BucketName"])
    upload(session, out["BucketName"])

    print("\n[4/4] invalidating CloudFront")
    print("  invalidation %s" % invalidate(session, out["DistributionId"]))

    print("\nchecking %s" % out["SiteURL"])
    check(out["SiteURL"])
    print("\nLive at: %s" % out["SiteURL"])
    print("A new distribution can take several more minutes to propagate.")


if __name__ == "__main__":
    main()
