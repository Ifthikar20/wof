# Three buckets with different trust levels:
#   uploads - raw user files, private, written only through presigned POSTs
#   media   - processed, EXIF-free variants, served only through CloudFront
#   anchor  - WORM (object lock) copy of the daily audit-chain head hash

resource "aws_s3_bucket" "uploads" {
  #checkov:skip=CKV_AWS_18:Access is via presigned POSTs and the worker role; audit with CloudTrail S3 data events instead of server access logs.
  #checkov:skip=CKV2_AWS_62:Processing is triggered by the app ("complete" call), not bucket events.
  #checkov:skip=CKV_AWS_144:Raw uploads are transient; only processed media is worth replicating.
  bucket = "${local.name}-uploads-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket" "media" {
  #checkov:skip=CKV_AWS_18:Served through CloudFront; request logging belongs at the CDN.
  #checkov:skip=CKV2_AWS_62:No event-driven processing on processed media.
  #checkov:skip=CKV_AWS_144:Cross-region replication is a Growth-stage item in docs/10 (DR); versioning covers accidental deletes.
  bucket = "${local.name}-media-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket" "anchor" {
  #checkov:skip=CKV_AWS_18:Write-once objects under compliance-mode object lock; CloudTrail covers access.
  #checkov:skip=CKV2_AWS_62:No consumers need events for anchored hashes.
  #checkov:skip=CKV_AWS_144:Move this bucket to a separate account for the strongest guarantee (see README).
  #checkov:skip=CKV2_AWS_61:Object lock enforces 7-year retention; lifecycle deletion is intentionally absent.
  bucket              = "${local.name}-audit-anchor-${data.aws_caller_identity.current.account_id}"
  object_lock_enabled = true
}

locals {
  buckets = {
    uploads = aws_s3_bucket.uploads.id
    media   = aws_s3_bucket.media.id
    anchor  = aws_s3_bucket.anchor.id
  }
}

resource "aws_s3_bucket_public_access_block" "all" {
  for_each                = local.buckets
  bucket                  = each.value
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "all" {
  for_each = local.buckets
  bucket   = each.value
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "all" {
  for_each = local.buckets
  bucket   = each.value
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.main.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_versioning" "all" {
  for_each = local.buckets
  bucket   = each.value
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id
  rule {
    id     = "expire-noncurrent"
    status = "Enabled"
    filter {}
    noncurrent_version_expiration {
      noncurrent_days = 7
    }
    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "media" {
  bucket = aws_s3_bucket.media.id
  rule {
    id     = "expire-noncurrent"
    status = "Enabled"
    filter {}
    noncurrent_version_expiration {
      noncurrent_days = 30
    }
    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
}

# Browsers upload straight to the private bucket with a presigned POST from the site origin.
resource "aws_s3_bucket_cors_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id
  cors_rule {
    allowed_methods = ["POST"]
    allowed_origins = ["https://${var.domain}"]
    allowed_headers = ["*"]
    max_age_seconds = 600
  }
}

# Compliance-mode object lock: nobody, including the account root, can delete or alter
# an anchored hash before it expires (7 years). For the strongest guarantee, move this
# bucket to a separate AWS account that the app account can only write to.
resource "aws_s3_bucket_object_lock_configuration" "anchor" {
  bucket = aws_s3_bucket.anchor.id
  rule {
    default_retention {
      mode  = "COMPLIANCE"
      years = 7
    }
  }
}

# ---- Media CDN: CloudFront with origin access control (the bucket stays private) ----
resource "aws_cloudfront_origin_access_control" "media" {
  name                              = "${local.name}-media"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_acm_certificate" "media" {
  provider          = aws.us_east_1
  domain_name       = "media.${var.domain}"
  validation_method = "DNS"
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_acm_certificate_validation" "media" {
  provider                = aws.us_east_1
  certificate_arn         = aws_acm_certificate.media.arn
  validation_record_fqdns = [for r in cloudflare_record.media_cert : r.hostname]
}

resource "aws_cloudfront_response_headers_policy" "media" {
  name = "${local.name}-media"
  security_headers_config {
    content_type_options {
      override = true
    }
    strict_transport_security {
      access_control_max_age_sec = 63072000
      include_subdomains         = true
      preload                    = true
      override                   = true
    }
  }
  cors_config {
    access_control_allow_credentials = false
    access_control_allow_headers {
      items = ["*"]
    }
    access_control_allow_methods {
      items = ["GET", "HEAD"]
    }
    access_control_allow_origins {
      items = ["https://${var.domain}"]
    }
    origin_override = true
  }
}

resource "aws_cloudfront_distribution" "media" {
  #checkov:skip=CKV_AWS_68:Static, re-encoded images only; no dynamic surface for a WAF to protect.
  #checkov:skip=CKV2_AWS_47:Same as above (no application code behind this origin).
  #checkov:skip=CKV_AWS_86:Add standard logging when a log bucket with ACLs is provisioned; not needed for launch.
  #checkov:skip=CKV_AWS_374:Stories are meant to be read worldwide.
  #checkov:skip=CKV_AWS_310:Single origin; S3 regional durability is sufficient for media.
  #checkov:skip=CKV_AWS_305:Not a website distribution; there is no root object.
  enabled         = true
  is_ipv6_enabled = true
  aliases         = ["media.${var.domain}"]
  price_class     = "PriceClass_100"
  comment         = "${local.name} processed media"

  origin {
    domain_name              = aws_s3_bucket.media.bucket_regional_domain_name
    origin_id                = "media"
    origin_access_control_id = aws_cloudfront_origin_access_control.media.id
  }

  default_cache_behavior {
    target_origin_id           = "media"
    viewer_protocol_policy     = "redirect-to-https"
    allowed_methods            = ["GET", "HEAD"]
    cached_methods             = ["GET", "HEAD"]
    compress                   = true
    cache_policy_id            = "658327ea-f89d-4fab-a63d-7e88639e58f6" # Managed-CachingOptimized
    response_headers_policy_id = aws_cloudfront_response_headers_policy.media.id
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate_validation.media.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}

data "aws_iam_policy_document" "media_bucket" {
  statement {
    sid       = "CloudFrontReadOnly"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.media.arn}/*"]
    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.media.arn]
    }
  }
  statement {
    sid       = "DenyInsecureTransport"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = [aws_s3_bucket.media.arn, "${aws_s3_bucket.media.arn}/*"]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "media" {
  bucket = aws_s3_bucket.media.id
  policy = data.aws_iam_policy_document.media_bucket.json
}

data "aws_iam_policy_document" "tls_only" {
  for_each = { uploads = aws_s3_bucket.uploads.arn, anchor = aws_s3_bucket.anchor.arn }
  statement {
    sid       = "DenyInsecureTransport"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = [each.value, "${each.value}/*"]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "tls_only" {
  for_each = data.aws_iam_policy_document.tls_only
  bucket   = local.buckets[each.key]
  policy   = each.value.json
}
