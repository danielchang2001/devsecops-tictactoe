# Build stage
FROM node:23-alpine AS build
WORKDIR /app

# Accept build argument to inject API URL at build time
ARG API_URL
ENV VITE_API_URL=$API_URL

COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
RUN apk update && apk upgrade

# Copy the dist artifacts from the build stage to final image
COPY --from=build /app/dist /usr/share/nginx/html

# Add nginx configuration if needed (uncomment to use a custom nginx config)
# COPY nginx.conf /etc/nginx/conf.d/default.conf\

EXPOSE 80

# Run nginx to serve the frontend
CMD ["nginx", "-g", "daemon off;"]