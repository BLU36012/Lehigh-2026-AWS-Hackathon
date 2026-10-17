"""Load the exported bundle into DynamoDB.

    python scripts/load_dynamo.py <table-name> --region us-east-1

Item layout (single table, pk/sk):
    META                  / BUNDLE          -> hospitals, services, payers, geo
    P#<service>#<payer>   / H#<hospital_id> -> {lo, mid, hi, n, set, meth, plans}

Payloads are stored as pre-serialised JSON strings in a `body` attribute. That
keeps floats out of DynamoDB's Decimal type, so the Lambda can hand the bytes
straight back without a lossy round-trip.

Also importable: scripts/deploy_boto.py reuses build_items() and load().
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLE = os.path.join(ROOT, "web", "prices.json")

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    sys.stderr.write("\nboto3 is not installed.\n  pip install boto3\n\n")
    sys.exit(1)


def die(msg):
    sys.stderr.write("\n" + msg.rstrip() + "\n\n")
    sys.exit(1)


def resolve_region(region):
    region = (region or os.environ.get("AWS_DEFAULT_REGION")
              or os.environ.get("AWS_REGION"))
    if not region:
        die("No AWS region set.\n"
            "\n"
            "  Pass it on the command line:\n"
            "      --region us-east-1\n"
            "\n"
            "  Or set it for the session:\n"
            "      PowerShell:  $env:AWS_DEFAULT_REGION = \"us-east-1\"\n"
            "      Git Bash:    export AWS_DEFAULT_REGION=us-east-1\n"
            "\n"
            "  It must match the region the CloudFormation stack was created in.")
    return region


def preflight(region, quiet=False):
    """Return a boto3 Session, or exit with something readable."""
    try:
        session = boto3.Session(region_name=region)
        who = session.client("sts").get_caller_identity()
    except NoCredentialsError:
        die("No AWS credentials found.\n"
            "\n"
            "  Create an access key in the console (IAM -> Users -> your user ->\n"
            "  Security credentials -> Create access key -> CLI), then:\n"
            "      PowerShell:  $env:AWS_ACCESS_KEY_ID = \"<your 20-char key id>\"\n"
            "                   $env:AWS_SECRET_ACCESS_KEY = \"<your 40-char secret>\"\n"
            "      Git Bash:    export AWS_ACCESS_KEY_ID=<your 20-char key id>\n"
            "                   export AWS_SECRET_ACCESS_KEY=<your 40-char secret>\n"
            "\n"
            "  Or run 'aws configure' if you have the AWS CLI installed.")
    except ClientError as e:
        die("AWS rejected those credentials:\n  %s"
            % e.response["Error"].get("Message", e))
    if not quiet:
        print("account %s | region %s" % (who["Account"], region))
    return session


def build_items():
    if not os.path.exists(BUNDLE):
        die("Missing %s - run 'python scripts/export_web.py' first." % BUNDLE)
    bundle = json.load(open(BUNDLE, encoding="utf-8"))

    meta = {k: bundle[k] for k in
            ("hospitals", "services", "payers", "payerPlans", "quality",
             "counties", "cities", "zips")}
    items = [{"pk": "META", "sk": "BUNDLE",
              "body": json.dumps(meta, separators=(",", ":"))}]

    for key, by_hospital in bundle["prices"].items():
        code, payer = key.split("|", 1)
        for hospital_id, entry in by_hospital.items():
            items.append({
                "pk": "P#%s#%s" % (code, payer),
                "sk": "H#%s" % hospital_id,
                "body": json.dumps(entry, separators=(",", ":")),
            })
    return items


def load(session, table_name, items):
    table = session.resource("dynamodb").Table(table_name)
    try:
        table.load()
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "ResourceNotFoundException":
            die("No DynamoDB table named '%s' in %s.\n"
                "\n"
                "  Check the TableName output of your CloudFormation stack, and\n"
                "  that you are using the same region the stack was created in."
                % (table_name, session.region_name))
        if code in ("AccessDeniedException", "UnrecognizedClientException"):
            die("Those credentials cannot read DynamoDB in %s:\n  %s"
                % (session.region_name, e.response["Error"].get("Message", code)))
        raise

    print("writing %d items to %s ..." % (len(items), table_name))
    written = 0
    try:
        with table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item=item)
                written += 1
                if written % 500 == 0:
                    print("  %d/%d" % (written, len(items)))
    except ClientError as e:
        die("Write failed after %d items:\n  %s"
            % (written, e.response["Error"].get("Message", e)))

    probe = table.get_item(Key={"pk": "META", "sk": "BUNDLE"}).get("Item")
    print("done: %d items | meta readback: %s"
          % (written, "ok" if probe else "MISSING"))
    return written


def main():
    args = list(sys.argv[1:])
    region = None
    if "--region" in args:
        i = args.index("--region")
        if i + 1 >= len(args):
            die("--region needs a value, e.g. --region us-east-1")
        region = args[i + 1]
        del args[i:i + 2]

    if not args:
        die("Usage: python scripts/load_dynamo.py <table-name> --region <region>\n"
            "\n"
            "  The table name is the TableName output of the CloudFormation\n"
            "  stack, by default 'lv-price-finder-rates'.")

    region = resolve_region(region)
    session = preflight(region)
    load(session, args[0], build_items())


if __name__ == "__main__":
    main()
