# Cloud Mini Project: Dockerized TODO Microservices

This project is a complete microservices-based TODO platform using Flask, PostgreSQL, Redis, Nginx, Docker Compose, cAdvisor, and GitHub Actions.

## Architecture

- `app`: Flask API with SQLAlchemy and Redis integration
- `db`: PostgreSQL database with persistent storage
- `redis`: Redis cache used for task caching and visit counting
- `nginx`: Reverse proxy in front of the Flask service
- `cadvisor`: Container monitoring dashboard

## API Endpoints

- `GET /tasks`
- `POST /tasks`
- `DELETE /tasks/<id>`
- `GET /health`

## Run the Project

1. Open a terminal in the `project` directory.
2. Start the stack:

```bash
docker compose up --build
```

3. Open the services:

- API through Nginx: `http://localhost/tasks`
- cAdvisor dashboard: `http://localhost:8080`

## Scale the Flask API

Run the application with multiple Flask containers:

```bash
docker compose up --build --scale app=3
```

Nginx uses Docker DNS-based service discovery so requests continue to route to the scaled `app` service.

## Example Requests

Create a task:

```bash
curl -X POST http://localhost/tasks \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Write documentation\"}"
```

List tasks:

```bash
curl http://localhost/tasks
```

Delete a task:

```bash
curl -X DELETE http://localhost/tasks/1
```

## Environment Variables

The project uses the following variables from `.env`:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `DB_HOST`
- `DB_PORT`
- `REDIS_HOST`
- `REDIS_PORT`
- `TASKS_CACHE_TTL`

## CI/CD

GitHub Actions workflow:

- Builds the Flask Docker image on pushes and pull requests
- Optionally pushes the image to Docker Hub when `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets are configured

## Frontend

A simple web interface was implemented using HTML, CSS, and JavaScript to interact with the API. It allows users to add, view, and delete tasks directly from the browser.

## Notes

- PostgreSQL data is stored in the `postgres_data` Docker volume
- Redis data is stored in the `redis_data` Docker volume
- The Flask service waits for PostgreSQL before creating tables and serving traffic
