# TODO: Dockerfile for Frontend Application

# Step 1: Choose an appropriate base image, e.g., python:3.8-slim
FROM python:3.11-slim-bookworm

# Step 2: Set the working directory in the container
WORKDIR /app

# Step 3: Copy the requirements.txt file into the container and install the dependencies
COPY requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

# Step 4: Copy the rest of your application's code into the container
COPY . .

# Step 5: Specify the command to run the application, e.g., using streamlit
CMD ["python", "-m", "streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]

# Step 6: Expose the necessary port, typically 8501 for streamlit applications
EXPOSE 8501

# Note: Remember to test the Dockerfile locally to ensure the container builds and runs as expected before deploying
