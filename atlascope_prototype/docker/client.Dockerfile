FROM  node:latest

WORKDIR /atlascope/client

COPY ./client/package.json /atlascope/client/package.json

RUN npm install
