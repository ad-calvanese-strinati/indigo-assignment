FROM node:20-alpine AS build

WORKDIR /frontend

COPY package.json /frontend/package.json
RUN npm install

COPY . /frontend

RUN npm run build

FROM node:20-alpine

WORKDIR /frontend

COPY --from=build /frontend/dist /frontend/dist
COPY --from=build /frontend/scripts /frontend/scripts
COPY --from=build /frontend/package.json /frontend/package.json

RUN npm install --omit=dev

CMD ["sh", "-c", "node scripts/write-runtime-config.js && npx serve -s dist -l ${PORT:-3000}"]
