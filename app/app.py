import json
import os
import time

import redis
from flask import Flask, jsonify, request, send_from_directory
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from models import Base, Task


DB_USER = os.getenv("POSTGRES_USER", "todo_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "todo_password")
DB_NAME = os.getenv("POSTGRES_DB", "todo_db")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
TASKS_CACHE_TTL = int(os.getenv("TASKS_CACHE_TTL", "30"))

DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


def create_db_engine():
    return create_engine(DATABASE_URL, pool_pre_ping=True)


def wait_for_database(max_retries=20, delay=3):
    for attempt in range(1, max_retries + 1):
        try:
            engine = create_db_engine()
            with engine.connect():
                Base.metadata.create_all(engine)
            return engine
        except OperationalError:
            if attempt == max_retries:
                raise
            time.sleep(delay)
    raise RuntimeError("Database connection retries exhausted")


def create_redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


app = Flask(__name__)
engine = wait_for_database()
SessionLocal = sessionmaker(bind=engine)
redis_client = create_redis_client()


def serialize_task(task):
    return {"id": task.id, "title": task.title}


def get_cached_tasks():
    try:
        cached_tasks = redis_client.get("tasks_cache")
        if cached_tasks:
            return cached_tasks
    except redis.RedisError:
        return None
    return None


def invalidate_tasks_cache():
    try:
        redis_client.delete("tasks_cache")
    except redis.RedisError:
        pass


def update_visit_counter():
    try:
        return redis_client.incr("visits")
    except redis.RedisError:
        return None


@app.get("/health")
def healthcheck():
    return jsonify({"status": "ok"}), 200


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/tasks")
def get_tasks():
    visit_count = update_visit_counter()
    cached_tasks = get_cached_tasks()
    if cached_tasks:
        return (
            jsonify(
                {
                    "tasks": json.loads(cached_tasks),
                    "source": "cache",
                    "visits": visit_count,
                }
            ),
            200,
        )

    session = SessionLocal()
    try:
        tasks = session.query(Task).order_by(Task.id.asc()).all()
        serialized_tasks = [serialize_task(task) for task in tasks]
        try:
            redis_client.setex(
                "tasks_cache",
                TASKS_CACHE_TTL,
                json.dumps(serialized_tasks),
            )
        except redis.RedisError:
            pass
        return (
            jsonify(
                {
                    "tasks": serialized_tasks,
                    "source": "database",
                    "visits": visit_count,
                }
            ),
            200,
        )
    finally:
        session.close()


@app.post("/tasks")
def create_task():
    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip()

    if not title:
        return jsonify({"error": "Field 'title' is required"}), 400

    session = SessionLocal()
    try:
        task = Task(title=title)
        session.add(task)
        session.commit()
        session.refresh(task)
        invalidate_tasks_cache()
        return jsonify(serialize_task(task)), 201
    finally:
        session.close()


@app.delete("/tasks/<int:task_id>")
def delete_task(task_id):
    session = SessionLocal()
    try:
        task = session.get(Task, task_id)
        if task is None:
            return jsonify({"error": "Task not found"}), 404

        session.delete(task)
        session.commit()
        invalidate_tasks_cache()
        return jsonify({"message": "Task deleted", "id": task_id}), 200
    finally:
        session.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
