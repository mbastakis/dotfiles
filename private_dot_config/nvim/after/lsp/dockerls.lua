-- Override dockerls to NOT attach to docker-compose files
-- Only attach to actual Dockerfiles

return {
  filetypes = { "dockerfile" }, -- Only Dockerfile, not yaml
}
