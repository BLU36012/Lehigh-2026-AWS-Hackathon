# Deploying to AWS

Step-by-step for putting the Price Finder on AWS with the CLI, from nothing
installed to a live HTTPS URL. Roughly 25 minutes, most of it waiting for
CloudFront.

Commands are written for **Git Bash** on Windows (which the repo already uses).
Where PowerShell differs, it is noted.

---

## What you are building

```
                    ┌─────────────────────────────┐
  browser  ──────▶  │  CloudFront (HTTPS, gzip)   │
                    └──────────┬───────┬──────────┘
                     /*        │       │   /api/*
                    ┌──────────▼─┐  ┌──▼──────────────┐
                    │ S3 bucket  │  │ API Gateway     │
                    │ (private)  │  └──┬──────────────┘
                    └────────────┘     │
                                    ┌──▼───────┐   ┌────────────┐
                                    │ Lambda   │──▶│ DynamoDB   │
                                    └──────────┘   └────────────┘
```

Both the page and the API sit behind **one** CloudFront distribution, so the
browser only ever sees one origin and CORS never enters the picture.

Everything is defined in [infra/template.yaml](infra/template.yaml).

**Cost:** a hackathon's worth of traffic lands inside the free tier — well under
$1 either way. The one thing that will quietly bill you is leaving it running
afterwards, so see [Tear it down](#9-tear-it-down).

---

## Two ways to get the template into AWS

`infra/template.yaml` is a description, not a program. You hand it to the
CloudFormation service, which creates the resources and tracks them together as
one **stack** — delete the stack and all 14 go with it.

| | **Console** | **CLI** |
|---|---|---|
| Install | nothing | AWS CLI v2 |
| Hand over the template | upload the file in a web form | `aws cloudformation deploy` |
| Repeatable | no, it is clicking | yes |
| Good for | the first time, seeing what gets built | redeploying all evening |

**Both paths still need `boto3`** for one step: loading 2,968 rows into
DynamoDB, which is not something to click through. `boto3` reads credentials
from environment variables, so that step does not require the AWS CLI either.

The CLI path is steps 1–9 below. The console path is next.

---

## Console path (nothing to install but boto3)

### A. Create the stack

1. Sign in to the AWS Console.
2. **Set your region first** — the selector at top right. Pick `us-east-1`.
   Resources land in whatever region is selected, and it is easy to create them
   somewhere you then cannot find.
3. Go to **CloudFormation → Create stack → With new resources (standard)**.
4. Under *Specify template*, choose **Upload a template file**, click
   **Choose file**, and select `infra/template.yaml` from this repo.
5. **Next**. Stack name: `lv-price-finder`. Leave `ProjectName` at its default.
6. **Next** through the options page.
7. On the review page, tick **"I acknowledge that AWS CloudFormation might
   create IAM resources"** — this is the console's version of
   `--capabilities CAPABILITY_IAM`, and it is required because the template
   creates the Lambda's execution role.
8. **Submit**, then watch the **Events** tab. Expect **5–15 minutes**; CloudFront
   is the slow part. You want `CREATE_COMPLETE` on the stack itself.

### B. Collect the outputs

Open the **Outputs** tab of the finished stack. Copy these four:

| Output | Looks like |
|---|---|
| `BucketName` | `lv-price-finder-site-123456789012` |
| `TableName` | `lv-price-finder-rates` |
| `DistributionId` | `E1A2B3C4D5E6F7` |
| `SiteURL` | `https://d111111abcdef8.cloudfront.net` |

### C–E in one command (recommended)

Once the stack exists, everything left is ordinary API calls that boto3 can make
without the AWS CLI. [scripts/deploy_boto.py](scripts/deploy_boto.py) reads the
stack outputs, loads DynamoDB, uploads `dist/` with the right content types and
cache headers, invalidates CloudFront and checks the result:

```powershell
$env:AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
$env:AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

python scripts/build_site.py
python scripts/deploy_boto.py --region us-east-1
```

```
account 123456789012 | region us-east-1

[1/4] reading stack 'lv-price-finder'
  SiteURL         https://d111111abcdef8.cloudfront.net
  BucketName      lv-price-finder-site-123456789012
  ...
[2/4] loading DynamoDB
  writing 2968 items to lv-price-finder-rates ...
[3/4] uploading dist/ to s3://lv-price-finder-site-123456789012
  index.html            36 KB  no-cache
  prices.json          615 KB  public, max-age=3600
[4/4] invalidating CloudFront
```

Re-run it after any change. Add `--skip-data` to push only the page, which is
most redeploys and takes a few seconds.

The manual console steps are below if you would rather click through them once
to see what the script is doing.

### C. Upload the two site files

**S3 → your bucket → Upload → Add files** → pick `dist/index.html` and
`dist/prices.json`, then **Upload**.

Optional but worth it: before uploading, expand **Properties → Metadata**, add
**System defined → Cache-Control** and set `no-cache` for `index.html`, so a
later re-upload shows up immediately instead of being cached for hours.

### D. Load DynamoDB

> **The values below are examples.** `AKIAIOSFODNN7EXAMPLE` is AWS's published
> dummy key, not yours. Paste the real 20-character key ID and 40-character
> secret from IAM. If you are unsure whether yours took, run
> `python scripts/check_aws_auth.py --region us-east-1`.

The only step that needs code. Use the access key from step 2 of the CLI path
below.

**PowerShell:**

```powershell
pip install boto3

$env:AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
$env:AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

python scripts/load_dynamo.py lv-price-finder-rates --region us-east-1
```

**Git Bash:**

```bash
pip install boto3

export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

python scripts/load_dynamo.py lv-price-finder-rates --region us-east-1
```

`export` is Bash syntax and does nothing in PowerShell — mixing the two is the
usual cause of a `NoRegionError` or `NoCredentialsError` here. Passing
`--region` explicitly sidesteps half of that.

The region must match the one the stack was created in. The script checks your
credentials and that the table exists before writing anything, and prints the
account and region it is about to write to:

```
account 123456789012 | region us-east-1
writing 2968 items to lv-price-finder-rates ...
```

Confirm in **DynamoDB → Tables → lv-price-finder-rates → Explore items** that
there are roughly 2,968 items.

### E. Invalidate and open

**CloudFront → your distribution → Invalidations → Create invalidation**, path
`/*`. Then open the `SiteURL` from step B.

If the page loads but says "Could not load price data," step D did not land —
check the table has items, and that you loaded it in the same region as the
stack.

---

## 1. Install the AWS CLI

You do not have it yet (`aws --version` currently fails).

Download and run the Windows installer:
<https://awscli.amazonaws.com/AWSCLIV2.msi>

Then **close and reopen your terminal** so the new `PATH` is picked up:

```bash
aws --version
# aws-cli/2.x.x Python/3.x.x Windows/11 exe/AMD64
```

## 2. Create an access key

In the AWS Console: **IAM → Users → your user → Security credentials → Create
access key → Command Line Interface (CLI)**.

If you are on a brand-new account and have only the root login, create an IAM
user first and attach the `AdministratorAccess` policy. Root access keys are
best avoided even for a hackathon.

Copy the **Access key ID** and **Secret access key** — the secret is shown once.

## 3. Configure the CLI

```bash
aws configure
```

```
AWS Access Key ID     [None]: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Default region name   [None]: us-east-1
Default output format [None]: json
```

Keys are written to `~/.aws/credentials`. **Never commit that file**, and never
paste keys into source. `.gitignore` already covers `.aws/`.

Confirm it works:

```bash
aws sts get-caller-identity
```

```json
{ "UserId": "...", "Account": "123456789012", "Arn": "arn:aws:iam::...:user/you" }
```

If this errors, nothing below will work — fix it here first.

## 4. Install boto3

The DynamoDB loader needs it:

```bash
pip install boto3
```

## 5. Build the site

```bash
python scripts/build_site.py
```

```
  dist/index.html          36 KB
  dist/prices.json        615 KB
```

This wraps `web/index.html` in a real HTML document (the artifact platform
supplies `<head>`, charset and viewport; S3 does not) and points the page at
`/api/*`.

> `dist/prices.json` is still copied for local testing. Once the API is live the
> page uses it only as a fallback, so you can leave it or delete it.

## 6. Deploy the stack

First, lint the template. A schema error costs you a failed stack and a
15-minute round trip, and the linter finds it in seconds:

```bash
pip install cfn-lint
python -c "from cfnlint import api; [print(m) for m in api.lint_all(open('infra/template.yaml').read())]"
```

Ignore `E3006 ... does not exist in <region>` for GovCloud, China and
`ap-east-2`/`ap-southeast-6` — those only matter if you deploy there. Ignore
`I3011` (informational). Anything else is a real error and will fail the stack.

Then deploy:

```bash
aws cloudformation deploy \
  --template-file infra/template.yaml \
  --stack-name lv-price-finder \
  --capabilities CAPABILITY_IAM \
  --region us-east-1
```

`--capabilities CAPABILITY_IAM` is required because the template creates the
Lambda's execution role; without it the deploy is refused.

**This takes about 5–15 minutes** — CloudFront distributions are slow to create.
The command blocks until it finishes. To watch progress in another terminal:

```bash
aws cloudformation describe-stack-events --stack-name lv-price-finder \
  --query "StackEvents[0:5].[Timestamp,ResourceStatus,ResourceType]" --output table
```

## 7. Read the outputs

```bash
aws cloudformation describe-stacks --stack-name lv-price-finder \
  --query "Stacks[0].Outputs" --output table
```

You need four values. Put them in shell variables:

```bash
STACK=lv-price-finder
get() { aws cloudformation describe-stacks --stack-name $STACK \
        --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text; }

BUCKET=$(get BucketName)
DIST_ID=$(get DistributionId)
TABLE=$(get TableName)
URL=$(get SiteURL)

echo "$BUCKET / $DIST_ID / $TABLE / $URL"
```

<details>
<summary>PowerShell equivalent</summary>

```powershell
$STACK = "lv-price-finder"
function Get-Out($k) {
  aws cloudformation describe-stacks --stack-name $STACK `
    --query "Stacks[0].Outputs[?OutputKey=='$k'].OutputValue" --output text
}
$BUCKET  = Get-Out BucketName
$DIST_ID = Get-Out DistributionId
$TABLE   = Get-Out TableName
$URL     = Get-Out SiteURL
```
</details>

## 8. Load the data and upload the site

### 8a. DynamoDB

```bash
python scripts/load_dynamo.py "$TABLE" --region us-east-1
```

```
writing 2968 items to lv-price-finder-rates …
  500/2968
  ...
done: 2968 items
meta readback: ok
```

One `META/BUNDLE` item holds hospitals, services, payers and the map geometry
(21 KB). The other 2,967 are one per service × payer × hospital.

### 8b. S3

Two commands, because the page and the data want different cache headers:

```bash
aws s3 sync dist/ "s3://$BUCKET/" --delete \
  --exclude index.html --cache-control "public, max-age=3600"

aws s3 cp dist/index.html "s3://$BUCKET/index.html" \
  --content-type "text/html; charset=utf-8" --cache-control "no-cache"
```

`no-cache` on the HTML means a redeploy shows up immediately instead of being
pinned for an hour.

### 8c. Invalidate the CDN

```bash
aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*"
```

## 9. Verify

```bash
echo "$URL"

# the API, through CloudFront
curl -s "$URL/api/meta" | head -c 120
# {"hospitals":[{"id":"LVH-ALL","name":"Lehigh Valley Hospital", ...

curl -s "$URL/api/rates?service=72148&payer=Aetna" | head -c 120
# {"LVH-ALL":{"lo":262.04,"mid":759.66, ...

# the page
curl -s -o /dev/null -w "%{http_code}\n" "$URL"
# 200
```

Then open `$URL` in a browser. You should see the example search (MRI lumbar
spine, Aetna, ZIP 18015) with three ranked hospitals.

Check the Network tab: `/api/meta` on load, then one `/api/rates?...` per
search. A second identical search should come back from the CloudFront cache
(`x-cache: Hit from cloudfront`) without touching Lambda.

---

## Redeploying after a change

Page or styling only:

```bash
python scripts/build_site.py
aws s3 cp dist/index.html "s3://$BUCKET/index.html" \
  --content-type "text/html; charset=utf-8" --cache-control "no-cache"
aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*"
```

New data (after editing `scripts/shoppable_services.csv` and re-running the
extract/export pipeline):

```bash
python scripts/load_dynamo.py "$TABLE" --region us-east-1
aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/api/*"
```

Infrastructure change: re-run the `cloudformation deploy` from step 6. It
updates in place and only touches what changed.

### Or just run the script

[scripts/deploy.sh](scripts/deploy.sh) does steps 5–8c in one go:

```bash
./scripts/deploy.sh lv-price-finder us-east-1
```

Use it once you have been through the steps manually and know what each does.

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `aws: command not found` after installing | Terminal still has the old `PATH`. Close and reopen it. |
| `AccessDenied` on `cloudformation deploy` | Your IAM user lacks permissions. Attach `AdministratorAccess` for the hackathon. |
| `InsufficientCapabilitiesException` | You left off `--capabilities CAPABILITY_IAM`. |
| Stack status `ROLLBACK_COMPLETE` | One resource failed to create and CloudFormation undid the rest. **A rolled-back stack cannot be updated or re-deployed over — you must delete it first.** See [Recovering from a rollback](#recovering-from-a-rollback) below. |
| `/api/meta` returns **503** `"Reference data has not been loaded yet"` | Step 8a did not run, or ran against a different table. Re-run the loader. |
| `/api/*` returns **404** | The path is wrong. Routes are `/api/meta` and `/api/rates` exactly — API Gateway sees the full path, there is no stage prefix. |
| Page loads but shows "Could not load price data" | Open the Network tab. A failing `/api/meta` points at Lambda; check `aws logs tail /aws/lambda/lv-price-finder-api --follow`. |
| **403 AccessDenied** XML from CloudFront | OAC and the bucket policy are still propagating. Wait a few minutes. If it persists, confirm the bucket policy's `AWS:SourceArn` matches your distribution id. |
| Changes do not appear | CloudFront cache. Invalidate, then hard-reload (Ctrl+Shift+R). |
| `BucketAlreadyExists` | Someone else owns that name. The template appends your account id, so this should not happen — if it does, pass a different `ProjectName`. |

### Recovering from a rollback

`ROLLBACK_COMPLETE` is a dead end — the stack cannot be updated, only deleted.

**1. Find out what actually failed.** The first `CREATE_FAILED` event is the
cause; everything after it is cascade noise.

Console: your stack → **Events** tab → sort oldest first → read the
**Status reason** on the first red row.

CLI:

```bash
aws cloudformation describe-stack-events --stack-name lv-price-finder \
  --query "reverse(StackEvents[?ResourceStatus=='CREATE_FAILED'].[LogicalResourceId,ResourceStatusReason])" \
  --output text
```

**2. Delete the stack.**

```bash
aws cloudformation delete-stack --stack-name lv-price-finder
aws cloudformation wait stack-delete-complete --stack-name lv-price-finder
```

Console: select the stack → **Delete**. Nothing needs emptying first, because a
rolled-back stack never got as far as holding objects in S3.

**3. Fix the cause, re-lint, deploy again.**

> **Known issue, fixed 2026-10-17.** The `ApiCachePolicy` resource used the
> property name `ParametersInCacheKeyAndForwardedHeaders`; the correct name is
> `ParametersInCacheKeyAndForwardedToOrigin`. This failed the cache policy and
> rolled back the whole stack. If you pulled the template before that date, take
> the current `infra/template.yaml` and redeploy.

Lambda logs are the fastest way into any API problem:

```bash
aws logs tail /aws/lambda/lv-price-finder-api --follow --region us-east-1
```

---

## 9. Tear it down

CloudFormation **cannot delete a bucket that still has objects in it**, so empty
it first or the stack delete will fail:

```bash
aws s3 rm "s3://$BUCKET" --recursive
aws cloudformation delete-stack --stack-name lv-price-finder --region us-east-1
aws cloudformation wait stack-delete-complete --stack-name lv-price-finder --region us-east-1
```

That removes the bucket, distribution, DynamoDB table, Lambda, API and IAM role.
