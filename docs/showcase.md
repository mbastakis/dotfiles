# Nocturne Rose

The shared workstation palette. This page and its stylesheet are ready-made native outputs from the Nocturne Rose theme repository, copied into dotfiles alongside the application themes.

## Layers

Six dark steps, black to high overlay. The bottom three are backgrounds; the top three are borders and inactive UI.

<div class="palette-grid">
  <div class="swatch" style="--swatch: var(--nocturne-black)"><strong>Black</strong><span>#09090b</span></div>
  <div class="swatch" style="--swatch: var(--nocturne-base)"><strong>Base</strong><span>#0d0d10</span></div>
  <div class="swatch" style="--swatch: var(--nocturne-mantle)"><strong>Mantle</strong><span>#121217</span></div>
  <div class="swatch" style="--swatch: var(--nocturne-surface)"><strong>Surface</strong><span>#18181f</span></div>
  <div class="swatch" style="--swatch: var(--nocturne-overlay)"><strong>Overlay</strong><span>#22222c</span></div>
  <div class="swatch" style="--swatch: var(--nocturne-overlay-high)"><strong>High overlay</strong><span>#30303d</span></div>
</div>

## Accents

Rose marks focus and identity. Orchid, blue, and aqua distinguish without competing with it.

<div class="palette-grid">
  <div class="swatch" style="--swatch: var(--nocturne-rose); --label: var(--nocturne-black)"><strong>Rose</strong><span>#d48aa4</span></div>
  <div class="swatch" style="--swatch: var(--nocturne-rose-bright); --label: var(--nocturne-black)"><strong>Bright rose</strong><span>#e3a0b8</span></div>
  <div class="swatch" style="--swatch: var(--nocturne-rose-dim)"><strong>Dim rose</strong><span>#7c4659</span></div>
  <div class="swatch" style="--swatch: var(--nocturne-orchid); --label: var(--nocturne-black)"><strong>Orchid</strong><span>#b69acb</span></div>
  <div class="swatch" style="--swatch: var(--nocturne-blue); --label: var(--nocturne-black)"><strong>Blue</strong><span>#88a8bd</span></div>
  <div class="swatch" style="--swatch: var(--nocturne-aqua); --label: var(--nocturne-black)"><strong>Aqua</strong><span>#94b3ae</span></div>
</div>

## Signals

<div class="palette-grid palette-grid--4">
  <div class="swatch" style="--swatch: var(--nocturne-green); --label: var(--nocturne-black)"><strong>Success</strong><span>#8aa47f</span></div>
  <div class="swatch" style="--swatch: var(--nocturne-blue); --label: var(--nocturne-black)"><strong>Info</strong><span>#88a8bd</span></div>
  <div class="swatch" style="--swatch: var(--nocturne-amber); --label: var(--nocturne-black)"><strong>Warning</strong><span>#d3b069</span></div>
  <div class="swatch" style="--swatch: var(--nocturne-red); --label: var(--nocturne-black)"><strong>Error</strong><span>#cc655c</span></div>
</div>

## In Use

Live captures of the installed tools, including SketchyBar. Refresh with `mise exec -- task docs:capture-theme`.

<figure class="theme-shot">
  <img src="assets/theme/terminal-workspace.webp" alt="Ghostty with tmux panes, LazyGit, and SketchyBar using Nocturne Rose" />
  <figcaption>Ghostty, tmux, and LazyGit.</figcaption>
</figure>

<figure class="theme-shot">
  <img src="assets/theme/opencode-session.webp" alt="OpenCode running with its session sidebar open beneath SketchyBar" />
  <figcaption>OpenCode with the session sidebar open.</figcaption>
</figure>
