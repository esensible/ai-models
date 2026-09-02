# Build/deploy the viewer — run INSIDE the devcontainer (node/python/uv/pulumi/aws baked in).
SHELL := /usr/bin/env bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
STACK ?= dev

.PHONY: install build typecheck test preview deploy destroy

install:                       ## install infra + frontend node deps and the backend venv
	cd infra && npm install
	cd frontend && npm install
	cd backend && uv sync

build:                         ## build the frontend bundle (frontend/dist)
	cd frontend && npm run build

typecheck:                     ## type-check infra + frontend without emitting
	cd infra && npx tsc --noEmit
	cd frontend && npx tsc --noEmit

test:                          ## lint + test the python backend
	cd backend && uv run ruff check . && uv run pytest -q

preview:                       ## pulumi preview (no changes)
	cd infra && pulumi preview -s $(STACK)

deploy:                        ## provision infra, then build+sync the frontend behind CloudFront
	cd infra && pulumi up -y -s $(STACK)
	WS=$$(cd infra && pulumi stack output wsUrl -s $(STACK))
	SITE=$$(cd infra && pulumi stack output siteBucketName -s $(STACK))
	DIST=$$(cd infra && pulumi stack output cloudfrontDistributionId -s $(STACK))
	TOKEN=$$(cd infra && pulumi config get viewer:apiToken -s $(STACK))
	cd frontend && VITE_WS_URL="$$WS" VITE_API_TOKEN="$$TOKEN" npm run build
	aws s3 sync frontend/dist "s3://$$SITE" --delete
	aws cloudfront create-invalidation --distribution-id "$$DIST" --paths '/*' >/dev/null
	echo "deployed → $$(cd infra && pulumi stack output cloudfrontUrl -s $(STACK))"

destroy:                       ## tear it all down
	cd infra && pulumi destroy -y -s $(STACK)
