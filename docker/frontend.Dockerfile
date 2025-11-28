# Stage 1: Build the React App
FROM node:16-alpine as build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies (legacy peer deps to handle conflicts)
RUN npm install --legacy-peer-deps

# FIX: Install missing TF dependencies explicitly
RUN npm install @tensorflow/tfjs-core @tensorflow/tfjs-converter @tensorflow/tfjs-backend-webgl --legacy-peer-deps

COPY frontend/ .
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]