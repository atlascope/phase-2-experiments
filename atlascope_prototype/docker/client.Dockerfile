FROM node:22.11.0-alpine

RUN apk update && apk add git

COPY ./client/package.json ./
COPY ./client/package-lock.json ./

WORKDIR /atlascope/client

RUN npm install
