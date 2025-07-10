# Shared Node.js base image for frontend
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Create a non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -s /bin/sh -u 1000 -G appuser appuser

# Change ownership to appuser
RUN chown -R appuser:appuser /app

USER appuser 