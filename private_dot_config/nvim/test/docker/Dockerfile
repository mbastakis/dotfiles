# Dockerfile test file with intentional format/lint issues

# Missing specific version
FROM node:latest

# Running as root (security issue)
USER root

# Inconsistent spacing
WORKDIR /app

# Not using COPY --chown
COPY package*.json ./

# Running npm as root
RUN npm install

# Very long RUN command
RUN apt-get update && apt-get install -y curl wget git vim nano htop net-tools iputils-ping dnsutils telnet netcat

# Multiple RUN commands (should be combined)
RUN mkdir -p /app/data
RUN chmod 755 /app/data
RUN chown node:node /app/data

# COPY without .dockerignore consideration
COPY . .

# Missing --no-cache
RUN apt-get update && apt-get install -y python3

# Hardcoded secrets (bad practice)
ENV DATABASE_PASSWORD=secretpassword123
ENV API_KEY="hardcoded-api-key"

# Exposing multiple ports
EXPOSE 3000
EXPOSE 8080 9090

# Missing health check
# HEALTHCHECK --interval=30s CMD curl -f http://localhost:3000/ || exit 1

# Using shell form instead of exec form
CMD npm start
