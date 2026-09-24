# Application secrets. Values generated here never appear in the repository; they are
# injected into containers at start-up by ECS from Secrets Manager.

resource "random_password" "django_secret" {
  length  = 64
  special = false
}

resource "random_id" "field_key" {
  byte_length = 32 # Fernet key: 32 url-safe base64 bytes
}

resource "random_password" "webhook_user" {
  length  = 24
  special = false
}

locals {
  app_secrets = {
    DJANGO_SECRET_KEY      = random_password.django_secret.result
    FIELD_ENCRYPTION_KEYS  = "${random_id.field_key.b64_url}="
    REDIS_URL              = "rediss://:${random_password.redis.result}@${aws_elasticache_replication_group.main.primary_endpoint_address}:6379/0"
    TURNSTILE_SECRET_KEY   = cloudflare_turnstile_widget.site.secret
    EMAIL_HOST_USER        = var.email_host_user
    EMAIL_HOST_PASSWORD    = var.email_host_user
    EMAIL_WEBHOOK_USER     = random_password.webhook_user.result
    EMAIL_WEBHOOK_PASSWORD = var.email_webhook_password
  }
}

resource "aws_secretsmanager_secret" "app" {
  #checkov:skip=CKV2_AWS_57:Rotated by runbook RB-5 (key rotation needs a dual-key window in the app); the DB password is rotated by RDS.
  for_each   = local.app_secrets
  name       = "${local.name}/${each.key}"
  kms_key_id = aws_kms_key.main.arn
}

resource "aws_secretsmanager_secret_version" "app" {
  for_each      = local.app_secrets
  secret_id     = aws_secretsmanager_secret.app[each.key].id
  secret_string = each.value
}
