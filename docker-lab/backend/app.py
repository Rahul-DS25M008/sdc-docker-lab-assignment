import dotenv
import fastapi
from fastapi.middleware.cors import CORSMiddleware
from routes import image_gen_router

dotenv.load_dotenv('.env')

app = fastapi.FastAPI()


# Allow all origins to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(image_gen_router)
