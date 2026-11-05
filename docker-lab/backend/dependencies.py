import os

import redis
from rq import Queue

from gpt_service import GPTService
from image_generator import ImageGenerator


def read_prompt_file(prompt_file: str):
    with open(prompt_file, "r") as f:
        prompt = f.read()
    return prompt


def get_profanity_prompt():
    return read_prompt_file(os.environ['PROFANITY_PROMPT_FILE'])


def get_gpt_service() -> GPTService:
    return GPTService(openai_api_key=os.environ["OPENAI_API_KEY"],
                      profanity_prompt=get_profanity_prompt())


def get_profanity_violation() -> str:
    return ("Please refrain from using language or requesting content that may be offensive, discriminatory,"
            " or otherwise inappropriate.")


def get_image_generator():
    return ImageGenerator(os.environ['STABILITY_KEY'])


def get_redis_connection():
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    return redis.from_url(redis_url)


def get_queue():
    return Queue(connection=get_redis_connection())


def get_upload_folder():
    return os.getenv('UPLOAD_FOLDER', './images')
