-- Override dockerls to NOT attach to docker-compose files
-- Only attach to actual Dockerfiles

vim.lsp.config('dockerls', {
  filetypes = { 'dockerfile' }, -- Only Dockerfile, not yaml
})
