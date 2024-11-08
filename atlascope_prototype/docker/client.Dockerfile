FROM node:22.11.0-alpine

RUN apk update && apk add git

WORKDIR /atlascope/client

COPY ./client/package.json /atlascope/client/package.json
COPY ./client/package-lock.json /atlascope/client/package-lock.json

RUN npm ci
