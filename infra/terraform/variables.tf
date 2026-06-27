variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "app_name" {
  description = "Application name (used for resource naming)"
  type        = string
  default     = "multi-agent-analyst"
}

variable "anthropic_api_key" {
  description = "Anthropic API key (stored in SSM, referenced here for initial setup)"
  type        = string
  sensitive   = true
}

variable "e2b_api_key" {
  description = "E2B API key"
  type        = string
  sensitive   = true
}

variable "task_cpu" {
  type    = number
  default = 1024
}

variable "task_memory" {
  type    = number
  default = 2048
}

variable "desired_count" {
  description = "Number of ECS tasks"
  type        = number
  default     = 1
}
