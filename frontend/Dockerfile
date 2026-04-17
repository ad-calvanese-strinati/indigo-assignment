FROM node:20-alpine

WORKDIR /frontend

COPY package.json /frontend/package.json
RUN npm install

COPY . /frontend

CMD ["npm", "run", "dev"]
