# TODO: Dockerfile for Backend Application

# Step 1: Choose an appropriate base image, e.g., python:3.8-slim
FROM python:3.11-slim-bookworm

# Step 2: Set the working directory in the container
WORKDIR /app

# Step 3: Copy the requirements.txt file into the container and install the dependencies
COPY requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

# Step 4: Copy the rest of your application's code into the container
COPY . .

# Step 5: Specify the command to run the application, e.g., using uvicorn
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

# Step 6: Expose the necessary port, typically 8000 for FastAPI applications
EXPOSE 8000

# Step 7: Include any additional steps required for your specific application setup, such as setting up a database connection or configuring logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PROFANITY_PROMPT_FILE=/app/profanity_prompt.txt \
    UPLOAD_FOLDER=/app/images

RUN mkdir -p /app/images

# Note: Remember to test the Dockerfile locally to ensure the container builds and runs as expected before deploying
