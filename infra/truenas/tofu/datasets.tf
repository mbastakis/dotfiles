locals {
  truenas_pool = "pool_4tb"
}

data "truenas_pool" "pool_4tb" {
  name = local.truenas_pool
}

resource "truenas_dataset" "homeserver" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver"
  force_destroy = false

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "homeserver_apps" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/apps"
  force_destroy = false

  depends_on = [truenas_dataset.homeserver]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "homeserver_data" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/data"
  force_destroy = false

  depends_on = [truenas_dataset.homeserver]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "data_taskchampion_backup" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/data/taskchampion-sync-backup"
  force_destroy = false

  depends_on = [truenas_dataset.homeserver_data]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "data_books" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/data/books"
  force_destroy = false
  uid           = 568
  gid           = 568
  mode          = "770"

  depends_on = [truenas_dataset.homeserver_data]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "data_photos" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/data/photos"
  force_destroy = false

  depends_on = [truenas_dataset.homeserver_data]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "data_photos_immich" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/data/photos/immich"
  force_destroy = false
  uid           = 568
  gid           = 568
  mode          = "770"

  depends_on = [truenas_dataset.data_photos]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "data_photos_apple_originals" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/data/photos/apple-originals"
  force_destroy = false
  uid           = 568
  gid           = 568
  mode          = "770"

  depends_on = [truenas_dataset.data_photos]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_file" "immich_storage_sentinel" {
  path          = "/mnt/pool_4tb/homeserver/data/photos/immich/.immich-storage"
  content       = "managed by infra/truenas/tofu\n"
  uid           = 568
  gid           = 568
  mode          = "0644"
  force_destroy = false

  depends_on = [truenas_dataset.data_photos_immich]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "apps_tailscale" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/apps/tailscale"
  force_destroy = false

  depends_on = [truenas_dataset.homeserver_apps]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "apps_tailscale_state" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/apps/tailscale/state"
  force_destroy = false

  depends_on = [truenas_dataset.apps_tailscale]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "apps_syncthing" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/apps/syncthing"
  force_destroy = false

  depends_on = [truenas_dataset.homeserver_apps]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "apps_syncthing_config" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/apps/syncthing/config"
  force_destroy = false

  depends_on = [truenas_dataset.apps_syncthing]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "apps_filebrowser_quantum" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/apps/filebrowser-quantum"
  force_destroy = false

  depends_on = [truenas_dataset.homeserver_apps]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "apps_filebrowser_quantum_config" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/apps/filebrowser-quantum/config"
  force_destroy = false

  depends_on = [truenas_dataset.apps_filebrowser_quantum]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "apps_backrest" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/apps/backrest"
  force_destroy = false

  depends_on = [truenas_dataset.homeserver_apps]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "apps_backrest_data" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/apps/backrest/data"
  force_destroy = false

  depends_on = [truenas_dataset.apps_backrest]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "apps_backrest_config" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/apps/backrest/config"
  force_destroy = false

  depends_on = [truenas_dataset.apps_backrest]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "apps_backrest_cache" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/apps/backrest/cache"
  force_destroy = false

  depends_on = [truenas_dataset.apps_backrest]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "apps_audiobookshelf" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/apps/audiobookshelf"
  force_destroy = false

  depends_on = [truenas_dataset.homeserver_apps]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "apps_audiobookshelf_config" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/apps/audiobookshelf/config"
  force_destroy = false
  uid           = 568
  gid           = 568
  mode          = "770"

  depends_on = [truenas_dataset.apps_audiobookshelf]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "apps_audiobookshelf_metadata" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/apps/audiobookshelf/metadata"
  force_destroy = false
  uid           = 568
  gid           = 568
  mode          = "770"

  depends_on = [truenas_dataset.apps_audiobookshelf]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "apps_audiobookshelf_backups" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/apps/audiobookshelf/backups"
  force_destroy = false
  uid           = 568
  gid           = 568
  mode          = "770"

  depends_on = [truenas_dataset.apps_audiobookshelf]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "data_obsidian" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/data/obsidian"
  force_destroy = false

  depends_on = [truenas_dataset.homeserver_data]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "data_obsidian_michail" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/data/obsidian/michail"
  force_destroy = false

  depends_on = [truenas_dataset.data_obsidian]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "data_files" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/data/files"
  force_destroy = false

  depends_on = [truenas_dataset.homeserver_data]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "data_files_household" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/data/files/household"
  force_destroy = false

  depends_on = [truenas_dataset.data_files]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "data_files_users" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/data/files/users"
  force_destroy = false

  depends_on = [truenas_dataset.data_files]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "data_files_users_michail" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/data/files/users/michail"
  force_destroy = false

  depends_on = [truenas_dataset.data_files_users]

  lifecycle {
    prevent_destroy = true
  }
}

resource "truenas_dataset" "data_files_users_chara" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/data/files/users/chara"
  force_destroy = false

  depends_on = [truenas_dataset.data_files_users]

  lifecycle {
    prevent_destroy = true
  }
}
