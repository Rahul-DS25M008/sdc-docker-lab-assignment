
"""Offline integration tests for the Docker image-generation lab.
This is basically created to test the entire architecture without api keys
since they always run out of quota.
"""

import io
import os
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

from app import app
import dependencies
import worker

# Generate a small, valid PNG without an external service.
def make_test_png():
    buffer = io.BytesIO()
    image = Image.new("RGB", (32, 32), color=(30, 120, 200))
    image.save(buffer, format="PNG")
    return buffer.getvalue()

#  RQ task used to test the real worker and shared volume.
def create_synthetic_jpeg(image_id):
    folder = Path(os.environ["UPLOAD_FOLDER"])
    folder.mkdir(parents=True, exist_ok=True)
    output = folder / f"{image_id}.jpeg"
    image = Image.new("RGB", (32, 32), color=(30, 120, 200))
    image.save(output, format="JPEG")

    return output.name

class FakeGPTService:
    def contains_profanity(self, prompt):
        return "blocked" in prompt.lower()

class FakeImageGenerator:
    def generate_image(self, prompt):
        return make_test_png()

# Execute enqueued functions locally for HTTP route testing.
class InlineQueue:

    def __init__(self, generator):
        self.generator = generator
        self.last_job = None

    def enqueue(self, task, *args):
        self.last_job = (task, args)

        with patch.object(
            dependencies,
            "get_image_generator",
            return_value=self.generator,
        ):
            return task(*args)


class OfflineIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        environment_patch = patch.dict(
            os.environ,
            {"UPLOAD_FOLDER": self.temp_directory.name},
        )
        environment_patch.start()
        self.addCleanup(environment_patch.stop)
        self.generator = FakeImageGenerator()
        self.queue = InlineQueue(self.generator)
        app.dependency_overrides.clear()
        app.dependency_overrides.update({
            dependencies.get_gpt_service: lambda: FakeGPTService(),
            dependencies.get_image_generator: lambda: self.generator,
            dependencies.get_queue: lambda: self.queue,
        })
        self.addCleanup(app.dependency_overrides.clear)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def assert_valid_jpeg(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/jpeg")
        with Image.open(io.BytesIO(response.content)) as image:
            self.assertEqual(image.format, "JPEG")
            self.assertEqual(image.size, (32, 32))

    def test_v1_returns_png(self):
        response = self.client.post(
            "/images",
            json={"userPrompt": "A robot reading a book"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/png")
        self.assertTrue(
            response.content.startswith(b"\x89PNG\r\n\x1a\n")
        )

    def test_v1_rejects_mocked_offensive_prompt(self):
        response = self.client.post(
            "/images",
            json={"userPrompt": "blocked content"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())

    def test_v2_background_generation_and_retrieval(self):
        response = self.client.post(
            "/v2/images",
            json={"userPrompt": "A robot reading a book"},
        )

        self.assertEqual(response.status_code, 200)
        image_id = response.json()["img_id"]
        uuid.UUID(image_id)
        image_response = self.client.get(f"/images/{image_id}")
        self.assert_valid_jpeg(image_response)

    def test_v3_worker_task_and_retrieval(self):
        prompt = "Prof Mo wondering why all keys run out of budget"
        response = self.client.post(
            "/v3/images",
            json={"userPrompt": prompt},
        )
        self.assertEqual(response.status_code, 200)
        image_id = response.json()["img_id"]
        uuid.UUID(image_id)
        self.assertIsNotNone(self.queue.last_job)
        task, arguments = self.queue.last_job
        self.assertIs(task, worker.gen_image_task)
        self.assertEqual(arguments, (image_id, prompt))
        image_response = self.client.get(f"/images/{image_id}")
        self.assert_valid_jpeg(image_response)

    def test_missing_image_returns_202(self):
        image_id = str(uuid.uuid4())
        response = self.client.get(f"/images/{image_id}")
        self.assertEqual(response.status_code, 202)
        self.assertEqual(
            response.json(),
            {"status": "processing"},
        )

if __name__ == "__main__":
    unittest.main()