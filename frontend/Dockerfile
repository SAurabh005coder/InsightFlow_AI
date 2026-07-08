# Stage 1: Build the React application
FROM node:20-alpine AS build

WORKDIR /app

# Copy package configuration and install dependencies
COPY package*.json /app/
RUN npm install --legacy-peer-deps

# Copy client source code and build production assets
COPY . /app/
RUN npm run build

# Stage 2: Serve assets with Nginx
FROM nginx:alpine

# Copy compiled assets from build stage to Nginx serving root
COPY --from=build /app/dist /usr/share/nginx/html

# Copy Nginx default configuration to handle React Router client side routes
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
