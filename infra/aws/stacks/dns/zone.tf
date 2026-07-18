resource "aws_route53_zone" "public" {
  name          = var.domain_name
  comment       = ""
  force_destroy = false

  tags = merge(var.tags, {
    Name    = var.domain_name
    Purpose = "authoritative-public-dns"
  })

  lifecycle {
    prevent_destroy = true
  }
}
