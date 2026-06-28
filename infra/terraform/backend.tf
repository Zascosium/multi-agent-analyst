terraform {
  backend "s3" {
    bucket  = "multi-agent-analyst-tfstate-983664477381"
    key     = "terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}
