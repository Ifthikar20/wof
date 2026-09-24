# Production infrastructure

Terraform for the reference architecture in [docs/10](../../docs/10-infrastructure-and-deployment.md):
Cloudflare at the edge, AWS for compute and data, GitHub Actions for deploys.

```
Browser ─► Cloudflare (DNS, TLS, WAF, bot rules, rate limits, cache, Turnstile, Access)
             │  only Cloudflare IPs may reach the origin
             ▼
           ALB (TLS 1.2+) ─► ECS Fargate: web (Next.js) ──► api (Django) ─► RDS Postgres 16 (Multi-AZ)
                                           worker, beat (Celery)          └► ElastiCache Redis (TLS + auth)
           media.<domain> ─► CloudFront ─► S3 media (private, OAC)
           S3 uploads (private, presigned POST) · S3 audit anchor (object lock, 7 years)
```

## What it creates

| Area | Resources |
|---|---|
| Network | VPC across 2 AZs: public (ALB, NAT), private (containers), isolated (database, Redis, no internet route); VPC flow logs; S3 gateway endpoint |
| Edge | Cloudflare DNS, strict TLS, managed WAF, custom firewall rules (AI crawlers, admin path, API bot score), rate limits (auth 20/min, story API 240/min per IP), edge cache for anonymous feed reads, Access (SSO + MFA) on `admin.<domain>`, Turnstile widget |
| Compute | ECS cluster; services `web`, `api`, `worker`, `beat`; `migrate` one-off task; CPU autoscaling for web/api (2–12); deployment circuit breakers with automatic rollback; read-only root filesystems, all Linux capabilities dropped |
| Data | RDS PostgreSQL 16 (encrypted, Multi-AZ, 14-day PITR, deletion protection, forced TLS, IAM auth, managed master password); ElastiCache Redis 7 (encrypted at rest and in transit, auth token) |
| Storage | S3 `uploads` (private, CORS for presigned POST), `media` (private, CloudFront OAC), `audit-anchor` (compliance-mode object lock), ALB access logs; all block public access, TLS-only policies, versioning |
| Secrets | Secrets Manager for Django secret key, field-encryption key, Redis URL, Turnstile secret, email credentials; one KMS key with rotation for everything at rest |
| Identity | Least-privilege task roles (web has none; api can only put uploads; worker reads uploads and writes media); GitHub OIDC deploy role limited to the `production` environment |
| Monitoring | SNS alarms: audit chain broken (SEV-1), 5xx rate > 1%, low DB storage, worker/beat not running |

## First-time setup

1. **State backend:** create an S3 bucket (versioned, encrypted) and a DynamoDB table
   `terraform-locks` (partition key `LockID`). Copy `backend.hcl.example` to `backend.hcl`.
2. **Variables:** copy `terraform.tfvars.example` to `terraform.tfvars`. Pass the secrets as
   environment variables: `TF_VAR_cloudflare_api_token`, `TF_VAR_email_host_user` (the Postmark
   server token) and `TF_VAR_email_webhook_password`.
3. **Apply:**
   ```bash
   terraform init -backend-config=backend.hcl
   terraform apply
   ```
4. **Database roles:** from a one-off ECS task (or a temporary bastion) in the private subnets, run `infra/postgres/roles.sql` as
   `wof_owner` (password in the RDS-managed secret). Set a password for `wof_app`, then store
   `{"username":"wof_app","password":"…"}` in the secret named by output `db_app_secret_arn`.
5. **GitHub:** create the `production` environment with required reviewers. Add these
   environment variables: `AWS_REGION`, `AWS_DEPLOY_ROLE_ARN`, `ECS_CLUSTER`, `ECR_BACKEND`,
   `ECR_FRONTEND`, `PRIVATE_SUBNETS`, `APP_SECURITY_GROUP`, `MEDIA_HOST`, `UPLOAD_HOST`,
   `TURNSTILE_SITE_KEY`, `DOMAIN` (all from `terraform output`).
6. **First deploy:** run the *Deploy* workflow manually. It builds and pushes both images,
   runs migrations as the schema owner, rolls out all services and smoke-tests the site.
7. **Email (Postmark):** verify the sending domain (SPF, DKIM, DMARC `p=none` to start), create a
   `broadcast` message stream for the digest, and add a webhook for Bounce, Spam Complaint and
   Subscription Change events pointing at
   `https://<user>:<password>@<domain>/api/v1/digest/webhooks/postmark`
   (the user is output `email_webhook_url_user`; the password is your variable).
8. **Admin:** create the first staff account with `python manage.py createsuperuser` in a
   one-off task, then turn on 2FA for it before using `https://admin.<domain>/<admin_path>`.

## Ongoing

- **Deploys:** every green CI run on `main` triggers *Deploy* after an approver accepts it.
- **Infra changes:** `terraform plan` / `apply` from a trusted machine. CI checks formatting,
  `terraform validate` and a Checkov security scan on every pull request.
- **Accepted scanner exceptions:** each has a `#checkov:skip` comment with its reason next to
  the resource.
- **Stronger audit anchoring:** move the `audit-anchor` bucket to a separate AWS account that the
  app account can only write to.
- **Cost:** roughly $350–600/month at launch sizes (NAT gateway, Multi-AZ RDS and Redis, 2×
  web/api tasks). For staging set `multi_az = false` and `desired_count = 1`.
