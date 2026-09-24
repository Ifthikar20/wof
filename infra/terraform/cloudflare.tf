data "cloudflare_zone" "main" {
  name = var.domain
}

locals {
  zone_id = data.cloudflare_zone.main.id
}

# ---- DNS ----
resource "cloudflare_record" "apex" {
  zone_id = local.zone_id
  name    = var.domain
  type    = "CNAME" # flattened at the apex by Cloudflare
  content = aws_lb.main.dns_name
  proxied = true
}

resource "cloudflare_record" "admin" {
  zone_id = local.zone_id
  name    = "admin"
  type    = "CNAME"
  content = aws_lb.main.dns_name
  proxied = true
}

resource "cloudflare_record" "media" {
  zone_id = local.zone_id
  name    = "media"
  type    = "CNAME"
  content = aws_cloudfront_distribution.media.domain_name
  proxied = false # CloudFront terminates TLS for media
}

resource "cloudflare_record" "origin_cert" {
  for_each = {
    for o in aws_acm_certificate.origin.domain_validation_options : o.domain_name => o
  }
  zone_id = local.zone_id
  name    = each.value.resource_record_name
  type    = each.value.resource_record_type
  content = each.value.resource_record_value
  proxied = false
}

resource "cloudflare_record" "media_cert" {
  for_each = {
    for o in aws_acm_certificate.media.domain_validation_options : o.domain_name => o
  }
  zone_id = local.zone_id
  name    = each.value.resource_record_name
  type    = each.value.resource_record_type
  content = each.value.resource_record_value
  proxied = false
}

# ---- TLS & baseline security ----
resource "cloudflare_zone_settings_override" "main" {
  zone_id = local.zone_id
  settings {
    ssl                      = "strict" # Cloudflare verifies the ALB's ACM certificate
    always_use_https         = "on"
    min_tls_version          = "1.2"
    tls_1_3                  = "on"
    automatic_https_rewrites = "on"
    security_level           = "medium"
    browser_check            = "on"
    opportunistic_encryption = "on"
  }
}

# ---- WAF: Cloudflare managed rules (Pro plan and above) ----
resource "cloudflare_ruleset" "waf_managed" {
  count   = var.enable_waf_managed_rules ? 1 : 0
  zone_id = local.zone_id
  name    = "Managed WAF"
  kind    = "zone"
  phase   = "http_request_firewall_managed"

  rules {
    action      = "execute"
    expression  = "true"
    description = "Cloudflare Managed Ruleset"
    enabled     = true
    action_parameters {
      id = "efb7b8c949ac4650a09736fc376e9aee"
    }
  }
}

# ---- Custom firewall rules ----
resource "cloudflare_ruleset" "firewall" {
  zone_id = local.zone_id
  name    = "Wall of Founders firewall"
  kind    = "zone"
  phase   = "http_request_firewall_custom"

  rules {
    action      = "block"
    description = "Dataset / AI-training crawlers (mirrors robots.txt)"
    enabled     = true
    expression  = "(http.user_agent contains \"GPTBot\") or (http.user_agent contains \"CCBot\") or (http.user_agent contains \"ClaudeBot\") or (http.user_agent contains \"Bytespider\") or (http.user_agent contains \"PerplexityBot\") or (http.user_agent contains \"Amazonbot\")"
  }

  rules {
    action      = "block"
    description = "The admin console is only reachable on the admin host"
    enabled     = true
    expression  = "(http.host eq \"${var.domain}\" and starts_with(http.request.uri.path, \"/${var.admin_path}\"))"
  }

  rules {
    action      = "managed_challenge"
    description = "Challenge unverified automation hitting the JSON API"
    enabled     = true
    expression  = "(starts_with(http.request.uri.path, \"/api/\") and not cf.client.bot and cf.bot_management.score lt 10)"
  }
}

# ---- Edge rate limits (the app has its own, finer-grained limits behind these) ----
resource "cloudflare_ruleset" "ratelimit" {
  zone_id = local.zone_id
  name    = "Rate limits"
  kind    = "zone"
  phase   = "http_ratelimit"

  rules {
    action      = "block"
    description = "Login, signup and password reset"
    enabled     = true
    expression  = "(starts_with(http.request.uri.path, \"/api/v1/auth/\") and http.request.method eq \"POST\")"
    ratelimit {
      characteristics     = ["cf.colo.id", "ip.src"]
      period              = 60
      requests_per_period = 20
      mitigation_timeout  = 600
    }
  }

  rules {
    action      = "managed_challenge"
    description = "Bulk reading of the story API"
    enabled     = true
    expression  = "(starts_with(http.request.uri.path, \"/api/v1/stories\"))"
    ratelimit {
      characteristics     = ["cf.colo.id", "ip.src"]
      period              = 60
      requests_per_period = 240
      mitigation_timeout  = 300
    }
  }
}

# ---- Cache anonymous feed reads at the edge (logged-in requests bypass) ----
resource "cloudflare_ruleset" "cache" {
  zone_id = local.zone_id
  name    = "Edge cache"
  kind    = "zone"
  phase   = "http_request_cache_settings"

  rules {
    action      = "set_cache_settings"
    description = "Anonymous GETs of the public story API"
    enabled     = true
    expression  = "(http.request.method eq \"GET\" and starts_with(http.request.uri.path, \"/api/v1/stories\") and not http.cookie contains \"wof_session\")"
    action_parameters {
      cache = true
      edge_ttl {
        mode = "respect_origin"
      }
      browser_ttl {
        mode = "respect_origin"
      }
    }
  }
}

# ---- Cloudflare Access: SSO in front of the admin console ----
resource "cloudflare_zero_trust_access_application" "admin" {
  zone_id                   = local.zone_id
  name                      = "Wall of Founders admin"
  domain                    = "admin.${var.domain}"
  type                      = "self_hosted"
  session_duration          = "8h"
  app_launcher_visible      = false
  auto_redirect_to_identity = true
}

resource "cloudflare_zero_trust_access_policy" "admin_staff" {
  application_id = cloudflare_zero_trust_access_application.admin.id
  zone_id        = local.zone_id
  name           = "Staff"
  precedence     = 1
  decision       = "allow"
  include {
    email_domain = [var.staff_email_domain]
  }
  require {
    auth_method = "mfa"
  }
}

# ---- Turnstile (bot check on signup, comments, reports, subscribe, password reset) ----
resource "cloudflare_turnstile_widget" "site" {
  account_id = var.cloudflare_account_id
  name       = "Wall of Founders"
  domains    = [var.domain]
  mode       = "managed"
}
