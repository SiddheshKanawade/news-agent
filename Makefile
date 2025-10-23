IMAGE_NAME=news-agent:latest
SERVICE_IMAGE_NAME=news-service:latest
format:
	autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place prazo service --exclude=__init__.py
	black prazo service --line-length 80
	isort --profile black prazo service --line-length 80

run:
	uv run python -m prazo.main

service:
	python service/api.py

docs:
	cd docs && python -m http.server 3000

docker-local:
	docker compose -f docker-compose-agent.yml build
	docker compose -f docker-compose-agent.yml up

docker-build:
	docker build --platform=linux/x86_64 -t $(IMAGE_NAME) -f ./docker/Dockerfile .

docker-build-service:
	docker build --platform=linux/x86_64 -t $(SERVICE_IMAGE_NAME) -f ./docker/Dockerfile.service .

# docker tag news-agent:latest agenticsystemsregistry.azurecr.io/news-agent:latest
# docker push agenticsystemsregistry.azurecr.io/news-agent:latest

