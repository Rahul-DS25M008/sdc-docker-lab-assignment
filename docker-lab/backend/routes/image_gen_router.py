import io
import os
import uuid

from PIL import Image
from fastapi import APIRouter, Request, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import Response, FileResponse, JSONResponse

from image_generator import ImageGenerator
import worker

from dependencies import get_gpt_service, get_profanity_violation, get_image_generator, get_queue, get_upload_folder
from gpt_service import GPTService
from rq import Queue

# import pydantic base model
from pydantic import BaseModel

router = APIRouter()

class ImageModel(BaseModel):
    userPrompt: str


@router.get('/images/{image_id}')
async def get_image(image_id: str, upload_folder: str = Depends(get_upload_folder)):
    file_path = f'{get_upload_folder()}/{image_id}.jpeg'
    if not os.path.exists(file_path):
        # ideally there would be a queue to check if the image job was created
        return JSONResponse({"status": "processing"}, status_code=status.HTTP_202_ACCEPTED)

    return FileResponse(file_path, media_type="image/jpeg")


# sync method
@router.post('/images')
async def post_message(request: ImageModel,
                       gpt_service: GPTService = Depends(get_gpt_service),
                       profanity_violation: str = Depends(get_profanity_violation),
                       image_generator: ImageGenerator = Depends(get_image_generator)):
    user_prompt: str = request.userPrompt

    if gpt_service.contains_profanity(user_prompt):
        raise HTTPException(status_code=400, detail=profanity_violation)
    image_binary = image_generator.generate_image(user_prompt)
    return Response(content=image_binary, media_type="image/png")


@router.post('/v2/images')
async def post_message(request: ImageModel,
                       background_tasks: BackgroundTasks,
                       image_generator: ImageGenerator = Depends(get_image_generator),
                       upload_folder: str = Depends(get_upload_folder)):
    user_prompt: str = request.userPrompt
    img_id = str(uuid.uuid4())
    background_tasks.add_task(gen_image_task, image_generator, img_id, user_prompt, upload_folder)
    return {"img_id": img_id}


def gen_image_task(image_generator: ImageGenerator, image_id: str, user_prompt: str,
                   upload_folder: str):
    img_binary = image_generator.generate_image(user_prompt)
    img = Image.open(io.BytesIO(img_binary))
    img.save(f"{upload_folder}/{image_id}.jpeg", "JPEG")


# with queue
@router.post('/v3/images')
async def post_message(request: ImageModel,
                       queue: Queue = Depends(get_queue)):
    user_prompt: str = request.userPrompt
    img_id = str(uuid.uuid4())
    # profanity filter
    queue.enqueue(worker.gen_image_task, img_id, user_prompt)
    return {"img_id": img_id}
