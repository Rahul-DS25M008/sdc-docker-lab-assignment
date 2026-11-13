
# Docker Lab: Image Generation Application

## Overview

This project containerizes a FastAPI image-generation backend and a
Streamlit frontend using Docker and Docker Compose.

The project is based on the Docker lab for the Solution Deployment &
Communication course at FH Technikum Wien.

The primary objective is to deploy the frontend and backend as separate
containers and enable communication between them through Docker networking.

The deployment also includes Redis and an RQ worker to support the
asynchronous queue-based image-generation endpoint.

## Architecture

Four Docker Compose services are configured:

| Service | Technology | Purpose |
|---|---|---|
| backend | Python / FastAPI | Image-generation API |
| frontend | Python / Streamlit | User interface |
| redis | Redis 7 | Background job queue |
| worker | Python / RQ | Processes queued image-generation tasks |

Communication:

- The frontend accesses FastAPI through `http://backend:8000`.
- FastAPI accesses Redis through `redis://redis:6379/0`.
- The worker consumes jobs from the Redis queues.
- Backend and worker share the `generated_images` Docker volume.
- The `redis_data` volume stores Redis persistence data.

Docker Compose creates the default application network automatically.

## Prerequisites

- Docker Engine
- Docker Compose v2
- An environment with access to the Docker daemon
- OpenAI and Stability API credentials for live model generation

The deployment has been developed and tested using GitHub Codespaces.

## Environment variables

The following variables are required for live image generation:

| Variable | Used by | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | Backend | GPT-based input classification |
| `STABILITY_KEY` | Backend and worker | Stability image generation |
| `API_URL` | Frontend | Backend service address |
| `REDIS_URL` | Backend and worker | Redis connection |
| `UPLOAD_FOLDER` | Backend and worker | Generated image directory |
| `PROFANITY_PROMPT_FILE` | Backend | Input-filter system prompt |

In GitHub Codespaces, `OPENAI_API_KEY` and `STABILITY_KEY` are
configured as Codespaces repository secrets.

The remaining variables are configured in `docker-compose.yml`
or the backend Dockerfile.

Real credentials must not be committed to the repository.

## Running the application

From the `docker-lab` directory:

```bash
docker compose config --quiet
docker compose up --build -d
docker compose ps
```

Access the applications:

- FastAPI documentation: `http://localhost:8000/docs`
- Streamlit frontend: `http://localhost:8501`

When using GitHub Codespaces, access these applications through the
forwarded ports, keeping their visibility Private.

View service logs:

```bash
docker compose logs --tail 50 backend frontend redis worker
```

Stop the application:

```bash
docker compose down
```

Named volumes remain available after a normal `docker compose down`.
Using `docker compose down -v` also removes the named volumes.

## Image-generation API

The supplied backend supports three generation modes:

| Endpoint | Behaviour |
|---|---|
| `POST /images` | Synchronous generation; returns PNG |
| `POST /v2/images` | FastAPI BackgroundTasks; returns image ID |
| `POST /v3/images` | Redis/RQ job; returns image ID |
| `GET /images/{image_id}` | Retrieves generated JPEG or returns HTTP 202 |

Example request body:

```json
{
  "userPrompt": "A small robot reading a book"
}
```

The v1 endpoint performs GPT-based input classification before image
generation. The original v2 and v3 implementations do not apply the
same classification step.

For v2 and v3, a generated JPEG is stored in `/app/images`.
The frontend polls the retrieval endpoint until an image is returned.

## Testing

### Docker and networking

The following checks were completed successfully:

- Backend and frontend Docker images build successfully.
- Both applications start in separate Docker containers.
- Both services return HTTP 200 on their health endpoints.
- Compose networking enables frontend-to-backend communication.
- `localhost:8000` from the frontend container does not address
  the backend container.
- `http://backend:8000` works inside the Compose network.

### Redis and worker

The following checks were completed:

- Redis starts and responds to `PING`.
- The RQ worker listens on the high, default and low queues.
- An offline RQ job executes successfully.
- Backend and worker access the same image volume.
- Named volumes survive normal Compose shutdown.

### Offline application integration

An offline integration test module is provided at:

`docker-lab/backend/test_offline_integration.py`

Run:

```bash
docker compose exec -T backend \
  python -m unittest -v test_offline_integration
```

The tests exercise v1, v2, v3, image conversion and retrieval without
calling external model APIs.

The same module contains a synthetic JPEG task that can be enqueued
through Redis to test the actual RQ worker and persistent image volume.

Mocks and synthetic images are used only for testing; they do not
replace the normal production generation code.

### External API test status

Live API tests were attempted on 13 November 2026.

- OpenAI rejected the configured credential with HTTP 401
  (`invalid_api_key`).
- Stability rejected the configured credential with gRPC
  `UNAUTHENTICATED`.
- The v2 endpoint accepted a generation request and returned an image
  ID, but the background task could not generate an image because
  Stability authentication failed.
- Live v1 and v3 generation were not successfully validated.

The externally supplied credentials require replacement or
reactivation by their owner.

Consequently, live image-generation success is not claimed.

## Known limitations

- The retrieval endpoint returns HTTP 202 whenever an image file is
  missing, even when a job has failed or an ID never existed.
- The supplied Streamlit application has no maximum polling duration.
- The original v2 background-task implementation does not expose
  persistent failure status through the retrieval endpoint.
- Real model generation requires working external credentials.
- This lab configuration is intended for coursework and development,
  not a hardened public production deployment.

## Project structure

```text
docker-lab/
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── app.py
│   ├── dependencies.py
│   ├── gpt_service.py
│   ├── worker.py
│   ├── test_offline_integration.py
│   ├── image_generator/
│   └── routes/
├── frontend/
│   ├── Dockerfile
│   ├── .dockerignore
│   └── streamlit_app.py
└── docker-compose.yml
```

## Summary

The principal Docker lab objective was achieved: the backend and
frontend run as separate containerized applications and communicate
through Docker Compose networking.

The Redis/RQ worker and persistent image volume extend the deployment
to support the supplied asynchronous architecture.

External image-generation API authentication remains the only
confirmed blocker for live model-generation verification.