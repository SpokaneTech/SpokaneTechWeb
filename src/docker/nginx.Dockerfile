# Use the official Nginx image as a base
FROM nginx:alpine

# Copy the custom nginx.conf into the container
COPY src/docker/nginx.conf /etc/nginx/nginx.conf
