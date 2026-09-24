output "deploy_role_arn" {
  description = "Set as AWS_DEPLOY_ROLE_ARN in the GitHub 'production' environment."
  value       = aws_iam_role.deploy.arn
}

output "ecr_backend" {
  value = aws_ecr_repository.app["backend"].repository_url
}

output "ecr_frontend" {
  value = aws_ecr_repository.app["frontend"].repository_url
}

output "ecs_cluster" {
  value = aws_ecs_cluster.main.name
}

output "private_subnets" {
  description = "For one-off tasks (migrations)."
  value       = join(",", aws_subnet.private[*].id)
}

output "app_security_group" {
  value = aws_security_group.app.id
}

output "turnstile_site_key" {
  description = "Public site key: set NEXT_PUBLIC_TURNSTILE_SITE_KEY for the frontend build."
  value       = cloudflare_turnstile_widget.site.id
}

output "media_host" {
  value = "https://media.${var.domain}"
}

output "upload_host" {
  description = "Browsers POST uploads here; set NEXT_PUBLIC_UPLOAD_HOST for the frontend build."
  value       = "https://${aws_s3_bucket.uploads.bucket_regional_domain_name}"
}

output "email_webhook_url_user" {
  description = "Username for the Postmark webhook URL (password is the variable you set)."
  value       = random_password.webhook_user.result
  sensitive   = true
}

output "db_app_secret_arn" {
  description = "Fill with {\"username\":\"wof_app\",\"password\":\"…\"} after running infra/postgres/roles.sql."
  value       = aws_secretsmanager_secret.db_app.arn
}
