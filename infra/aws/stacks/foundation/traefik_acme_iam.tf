data "aws_iam_policy_document" "traefik_acme" {
  statement {
    sid = "AllowRoute53ChallengeRecordChanges"
    actions = [
      "route53:ChangeResourceRecordSets",
      "route53:ListResourceRecordSets",
    ]
    resources = [data.aws_route53_zone.public.arn]
  }

  statement {
    sid = "AllowRoute53ChallengeChangePolling"
    actions = [
      "route53:GetChange",
    ]
    resources = ["arn:aws:route53:::change/*"]
  }

  statement {
    sid = "AllowRoute53ZoneDiscovery"
    actions = [
      "route53:ListHostedZonesByName",
    ]
    resources = ["*"]
  }
}

module "traefik_acme_user" {
  source = "../../modules/iam-user"

  user_name   = var.traefik_acme_iam_user_name
  purpose     = "traefik-route53-acme-dns01"
  policy_name = "homeserver-traefik-route53-acme"
  policy_json = data.aws_iam_policy_document.traefik_acme.json
  tags        = var.tags
}
