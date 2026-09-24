variable "environment" {
  description = "Deployment name, e.g. production or staging."
  type        = string
  default     = "production"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "domain" {
  description = "Apex domain managed in Cloudflare, e.g. walloffounders.com."
  type        = string
}

variable "cloudflare_api_token" {
  description = "Token with Zone:Edit, DNS:Edit, WAF:Edit, Access:Edit and Turnstile:Edit."
  type        = string
  sensitive   = true
}

variable "cloudflare_account_id" {
  type = string
}

variable "github_repository" {
  description = "owner/repo allowed to deploy through GitHub OIDC."
  type        = string
  default     = "Ifthikar20/wof"
}

variable "staff_email_domain" {
  description = "Email domain allowed through Cloudflare Access to the admin console."
  type        = string
}

variable "admin_path" {
  description = "Non-default Django admin path (defence against drive-by scanning)."
  type        = string
  default     = "console-7f3a/"
}

variable "image_tag" {
  description = "Initial image tag. Later deploys come from GitHub Actions."
  type        = string
  default     = "bootstrap"
}

variable "multi_az" {
  description = "Multi-AZ database. Turn off only for staging."
  type        = bool
  default     = true
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.medium"
}

variable "redis_node_type" {
  type    = string
  default = "cache.t4g.small"
}

variable "desired_count" {
  description = "Minimum running tasks for the web and API services."
  type        = number
  default     = 2
}

variable "enable_waf_managed_rules" {
  description = "Cloudflare managed WAF ruleset (requires a Pro plan or higher)."
  type        = bool
  default     = true
}

variable "email_host_user" {
  description = "Postmark server token (SMTP username and password)."
  type        = string
  sensitive   = true
}

variable "email_webhook_password" {
  type      = string
  sensitive = true
}

variable "from_email" {
  type    = string
  default = "Wall of Founders <hello@walloffounders.com>"
}

variable "digest_from_email" {
  type    = string
  default = "Wall of Founders Digest <digest@walloffounders.com>"
}

variable "alarm_email" {
  description = "Address that receives CloudWatch alarms (audit chain, 5xx, queue depth)."
  type        = string
}
