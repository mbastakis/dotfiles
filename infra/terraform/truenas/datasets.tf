locals {
  truenas_pool = "pool_4tb"
}

data "truenas_pool" "pool_4tb" {
  name = local.truenas_pool
}

# Existing backup datasets discovered on TrueNAS. Import these before changing them.
resource "truenas_dataset" "backups" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "backups"
  force_destroy = false

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "backups_atlas" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "backups/atlas"
  force_destroy = false

  depends_on = [truenas_dataset.backups]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "backups_atlas_2026_06_23" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "backups/atlas/2026-06-23"
  force_destroy = false

  depends_on = [truenas_dataset.backups_atlas]

  lifecycle {
    prevent_destroy = true
  }
}

import {
  to = truenas_dataset.backups
  id = "pool_4tb/backups"
}

import {
  to = truenas_dataset.backups_atlas
  id = "pool_4tb/backups/atlas"
}

import {
  to = truenas_dataset.backups_atlas_2026_06_23
  id = "pool_4tb/backups/atlas/2026-06-23"
}
