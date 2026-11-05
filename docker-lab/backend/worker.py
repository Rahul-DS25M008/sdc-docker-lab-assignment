import io

from PIL import Image
from dotenv import load_dotenv
from rq import Worker

import dependencies

load_dotenv('.env')

listen = ['high', 'default', 'low']


if __name__ == '__main__':
    conn = dependencies.get_redis_connection()
    Worker(connection=conn, queues=listen).work()


def profanity_violation(user_prompt: str):
    gpt_service = dependencies.get_gpt_service()
    response = dependencies.get_profanity_violation()
    if gpt_service.contains_profanity(user_prompt):
        return {"detail": response}


def gen_image_task(image_id: str, user_prompt: str):
    image_generator = dependencies.get_image_generator()
    # profanity filter
    img_binary = image_generator.generate_image(user_prompt)
    img = Image.open(io.BytesIO(img_binary))
    upload_dir = dependencies.get_upload_folder()
    img.save(f"{upload_dir}/{image_id}.jpeg", "JPEG")
