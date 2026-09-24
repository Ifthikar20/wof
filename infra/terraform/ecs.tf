resource "aws_ecs_cluster" "main" {
  name = local.name
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_cloudwatch_log_group" "app" {
  for_each          = toset(["web", "api", "worker", "beat", "migrate"])
  name              = "/${local.name}/${each.key}"
  retention_in_days = 365
  kms_key_id        = aws_kms_key.main.arn
}

# The web tier reaches the API over private DNS: api.wof.internal:8000.
resource "aws_service_discovery_private_dns_namespace" "internal" {
  name = "wof.internal"
  vpc  = aws_vpc.main.id
}

resource "aws_service_discovery_service" "api" {
  name = "api"
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.internal.id
    dns_records {
      ttl  = 10
      type = "A"
    }
  }
  health_check_custom_config {
    failure_threshold = 1
  }
}

locals {
  backend_image  = "${aws_ecr_repository.app["backend"].repository_url}:${var.image_tag}"
  frontend_image = "${aws_ecr_repository.app["frontend"].repository_url}:${var.image_tag}"
  db_app_secret  = aws_secretsmanager_secret.db_app.arn
  db_root_secret = aws_db_instance.main.master_user_secret[0].secret_arn

  backend_env = [
    { name = "DJANGO_SETTINGS_MODULE", value = "wof.settings.prod" },
    { name = "DJANGO_ALLOWED_HOSTS", value = "${var.domain},admin.${var.domain},api.wof.internal" },
    { name = "DJANGO_ADMIN_URL", value = var.admin_path },
    { name = "SITE_URL", value = "https://${var.domain}" },
    { name = "CSRF_TRUSTED_ORIGINS", value = "https://${var.domain},https://admin.${var.domain}" },
    { name = "TRUSTED_PROXY_IP_HEADER", value = "HTTP_CF_CONNECTING_IP" },
    { name = "POSTGRES_HOST", value = aws_db_instance.main.address },
    { name = "POSTGRES_DB", value = "wof" },
    { name = "POSTGRES_SSLMODE", value = "require" },
    { name = "S3_REGION", value = var.aws_region },
    { name = "S3_PRIVATE_BUCKET", value = aws_s3_bucket.uploads.id },
    { name = "S3_PUBLIC_BUCKET", value = aws_s3_bucket.media.id },
    { name = "MEDIA_CDN_URL", value = "https://media.${var.domain}" },
    { name = "EMAIL_HOST", value = "smtp.postmarkapp.com" },
    { name = "EMAIL_PORT", value = "587" },
    { name = "DEFAULT_FROM_EMAIL", value = var.from_email },
    { name = "DIGEST_FROM_EMAIL", value = var.digest_from_email },
    { name = "DIGEST_MESSAGE_STREAM", value = "broadcast" },
    { name = "AUDIT_ANCHOR_BUCKET", value = aws_s3_bucket.anchor.id },
  ]

  app_secret_refs = [for k, s in aws_secretsmanager_secret.app : { name = k, valueFrom = s.arn }]
  db_app_refs = [
    { name = "POSTGRES_USER", valueFrom = "${local.db_app_secret}:username::" },
    { name = "POSTGRES_PASSWORD", valueFrom = "${local.db_app_secret}:password::" },
  ]
  db_owner_refs = [
    { name = "POSTGRES_USER", valueFrom = "${local.db_root_secret}:username::" },
    { name = "POSTGRES_PASSWORD", valueFrom = "${local.db_root_secret}:password::" },
  ]

  # Hardening shared by every container: read-only root, no Linux capabilities,
  # a small writable /tmp volume, logs to CloudWatch.
  hardening = {
    readonlyRootFilesystem = true
    linuxParameters        = { capabilities = { drop = ["ALL"] }, initProcessEnabled = true }
    mountPoints            = [{ sourceVolume = "tmp", containerPath = "/tmp", readOnly = false }]
  }
}

resource "aws_ecs_task_definition" "backend" {
  for_each = {
    api     = { cpu = 512, memory = 1024, role = aws_iam_role.api.arn, cmd = null, db = local.db_app_refs, port = 8000 }
    worker  = { cpu = 512, memory = 1024, role = aws_iam_role.worker.arn, cmd = ["celery", "-A", "wof", "worker", "-l", "info", "--concurrency", "2"], db = local.db_app_refs, port = null }
    beat    = { cpu = 256, memory = 512, role = aws_iam_role.worker.arn, cmd = ["celery", "-A", "wof", "beat", "-l", "info", "--schedule", "/tmp/celerybeat-schedule"], db = local.db_app_refs, port = null }
    migrate = { cpu = 256, memory = 512, role = aws_iam_role.api.arn, cmd = ["python", "manage.py", "migrate", "--noinput"], db = local.db_owner_refs, port = null }
  }

  family                   = "${local.name}-${each.key}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = each.value.cpu
  memory                   = each.value.memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = each.value.role
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
  volume {
    name = "tmp"
  }

  container_definitions = jsonencode([merge(local.hardening, each.value.cmd == null ? {} : { command = each.value.cmd }, {
    name         = each.key
    image        = local.backend_image
    essential    = true
    environment  = local.backend_env
    secrets      = concat(local.app_secret_refs, each.value.db)
    portMappings = each.value.port == null ? [] : [{ containerPort = each.value.port, protocol = "tcp" }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.app[each.key].name
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = each.key
      }
    }
  })])
}

resource "aws_ecs_task_definition" "web" {
  family                   = "${local.name}-web"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.web.arn
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
  volume {
    name = "tmp"
  }

  # Next.js writes its data cache under .next/cache; give it a writable volume.
  volume {
    name = "nextcache"
  }

  container_definitions = jsonencode([merge(local.hardening, {
    mountPoints = [
      { sourceVolume = "tmp", containerPath = "/tmp", readOnly = false },
      { sourceVolume = "nextcache", containerPath = "/app/.next/cache", readOnly = false },
    ]
    name         = "web"
    image        = local.frontend_image
    essential    = true
    portMappings = [{ containerPort = 3000, protocol = "tcp" }]
    environment = [
      { name = "API_INTERNAL_URL", value = "http://api.wof.internal:8000" },
      { name = "SITE_URL", value = "https://${var.domain}" },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.app["web"].name
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "web"
      }
    }
  })])
}

locals {
  services = {
    web    = { task = aws_ecs_task_definition.web.arn, count = var.desired_count, tg = aws_lb_target_group.web.arn, port = 3000, discovery = false }
    api    = { task = aws_ecs_task_definition.backend["api"].arn, count = var.desired_count, tg = aws_lb_target_group.api.arn, port = 8000, discovery = true }
    worker = { task = aws_ecs_task_definition.backend["worker"].arn, count = 1, tg = null, port = null, discovery = false }
    beat   = { task = aws_ecs_task_definition.backend["beat"].arn, count = 1, tg = null, port = null, discovery = false } # exactly one scheduler
  }
}

resource "aws_ecs_service" "app" {
  for_each               = local.services
  name                   = each.key
  cluster                = aws_ecs_cluster.main.id
  task_definition        = each.value.task
  desired_count          = each.value.count
  launch_type            = "FARGATE"
  enable_execute_command = false
  propagate_tags         = "SERVICE"

  deployment_minimum_healthy_percent = each.key == "beat" ? 0 : 100
  deployment_maximum_percent         = each.key == "beat" ? 100 : 200
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.app.id]
    assign_public_ip = false
  }

  dynamic "load_balancer" {
    for_each = each.value.tg == null ? [] : [1]
    content {
      target_group_arn = each.value.tg
      container_name   = each.key
      container_port   = each.value.port
    }
  }

  dynamic "service_registries" {
    for_each = each.value.discovery ? [1] : []
    content {
      registry_arn = aws_service_discovery_service.api.arn
    }
  }

  # Deploys register new task definitions from CI; don't fight them on the next apply.
  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }
}

resource "aws_appautoscaling_target" "app" {
  for_each           = toset(["web", "api"])
  service_namespace  = "ecs"
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.app[each.key].name}"
  scalable_dimension = "ecs:service:DesiredCount"
  min_capacity       = var.desired_count
  max_capacity       = 12
}

resource "aws_appautoscaling_policy" "cpu" {
  for_each           = aws_appautoscaling_target.app
  name               = "${each.key}-cpu"
  policy_type        = "TargetTrackingScaling"
  service_namespace  = each.value.service_namespace
  resource_id        = each.value.resource_id
  scalable_dimension = each.value.scalable_dimension
  target_tracking_scaling_policy_configuration {
    target_value = 60
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}
