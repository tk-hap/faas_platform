#! /usr/bin/env bash

set -e
set -x

cd backend/src
python -c "import faas.main; import json; print(json.dumps(faas.main.app.openapi()))" > ../../openapi.json
cd ../../
mv openapi.json frontend/
cd frontend
npm run generate-client
npx biome format --write ./src/client
