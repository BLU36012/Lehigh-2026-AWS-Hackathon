"""Diagnose AWS credential problems without printing any secrets.

    python scripts/check_aws_auth.py --region us-east-1
"""
import os, sys

REGION = "us-east-1"
if "--region" in sys.argv:
    REGION = sys.argv[sys.argv.index("--region") + 1]

KEY = "AWS_ACCESS_KEY_ID"
SEC = "AWS_SECRET_ACCESS_KEY"
TOK = "AWS_SESSION_TOKEN"

problems = []


def mask(v):
    if not v:
        return "(not set)"
    return "%s...%s  [%d chars]" % (v[:4], v[-4:], len(v)) if len(v) > 12 \
        else "[%d chars]" % len(v)


print("Environment variables")
print("-" * 60)
key = os.environ.get(KEY, "")
sec = os.environ.get(SEC, "")
tok = os.environ.get(TOK, "")
print("  %-26s %s" % (KEY, mask(key)))
print("  %-26s %s" % (SEC, mask(sec)))
print("  %-26s %s" % (TOK, mask(tok)))

for name, val in ((KEY, key), (SEC, sec), (TOK, tok)):
    if not val:
        continue
    if val != val.strip():
        problems.append("%s has leading or trailing whitespace. Re-set it "
                        "without the stray space." % name)
    if (val.startswith(('"', "'")) or val.endswith(('"', "'"))):
        problems.append("%s contains literal quote characters. In PowerShell "
                        "write  $env:%s = \"AKIA...\"  with the quotes OUTSIDE "
                        "the value." % (name, name))

print()
print("Interpretation")
print("-" * 60)

if not key and not sec:
    print("  No credentials in the environment.")
    home = os.path.expanduser("~/.aws")
    if os.path.isdir(home):
        print("  Found %s - boto3 may be reading a profile from there." % home)
        for f in ("credentials", "config"):
            p = os.path.join(home, f)
            if os.path.exists(p):
                print("    %s exists" % p)
    else:
        print("  No ~/.aws directory either.")
    problems.append("Set both %s and %s, or run 'aws configure'." % (KEY, SEC))
else:
    if key and not key.startswith(("AKIA", "ASIA")):
        problems.append("%s does not start with AKIA or ASIA, so it is probably "
                        "not an access key ID. Did the key and secret get "
                        "swapped?" % KEY)
    if key and len(key) != 20:
        problems.append("%s is %d characters; access key IDs are 20. It may be "
                        "truncated or have extra characters."
                        % (KEY, len(key)))
    if sec and len(sec) != 40:
        problems.append("%s is %d characters; secret keys are 40. It may be "
                        "truncated." % (SEC, len(sec)))

    if key.startswith("ASIA"):
        print("  Key starts with ASIA: these are TEMPORARY credentials")
        print("  (IAM Identity Center / SSO, an assumed role, or CloudShell).")
        if not tok:
            problems.append(
                "ASIA keys are useless without the matching session token, and "
                "AWS reports that as 'The security token included in the "
                "request is invalid.' Copy all THREE values from the console's "
                "'Command line or programmatic access' panel, including "
                "AWS_SESSION_TOKEN. They also expire after an hour or so, so "
                "re-copy them if they were issued a while ago.")
        else:
            print("  Session token present. If this still fails, the "
                  "credentials have most likely expired - re-copy them.")
    elif key.startswith("AKIA"):
        print("  Key starts with AKIA: long-lived IAM user credentials.")
        print("  No session token needed.")
        if tok:
            problems.append(
                "%s is set alongside an AKIA key. A stale session token from an "
                "earlier login will be rejected. Clear it:  "
                "Remove-Item Env:\\%s" % (TOK, TOK))

print()
print("Live check: sts:GetCallerIdentity in %s" % REGION)
print("-" * 60)
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    try:
        who = boto3.Session(region_name=REGION).client("sts").get_caller_identity()
        print("  OK")
        print("  Account %s" % who["Account"])
        print("  Identity %s" % who["Arn"])
    except NoCredentialsError:
        print("  FAILED - boto3 found no credentials at all.")
    except ClientError as e:
        err = e.response["Error"]
        print("  FAILED - %s" % err.get("Code"))
        print("  %s" % err.get("Message"))
except ImportError:
    print("  boto3 not installed")

if problems:
    print()
    print("Problems found")
    print("-" * 60)
    for i, p in enumerate(problems, 1):
        print("  %d. %s" % (i, p))
    sys.exit(1)
