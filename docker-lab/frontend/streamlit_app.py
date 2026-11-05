import logging
import os
from io import BytesIO

import streamlit as st
import requests
import time
import dotenv

dotenv.load_dotenv('.env')
API_URL = os.environ['API_URL']

# Define the routes for different dropdown values
routes = {
    'v1': f'{API_URL}/images',
    'v2': f'{API_URL}/v2/images',
    'v3': f'{API_URL}/v3/images'
}

# Streamlit UI components
user_input = st.text_input("Enter your prompt")
dropdown_value = st.selectbox("Select a version", options=['v1', 'v2', 'v3'])
submit_button = st.button("Submit")


# Function to poll for the image
def poll_for_image(image_id):
    while True:
        response = requests.get(f'{API_URL}/images/{image_id}')
        if response.status_code == 202:
            print('waiting...')
            time.sleep(1)  # Wait for a second before polling again
        elif response.status_code == 200:
            return response.content
        else:
            raise Exception("Error polling for image")


# Handle button click
if submit_button:
    # Prepare the request body
    data = {"userPrompt": user_input}

    # Send the POST request
    response = requests.post(routes[dropdown_value], json=data)

    # Handle different responses
    if dropdown_value == 'v1':
        if response.status_code == 200:
            st.image(response.content)
        elif response.status_code == 400:
            st.error("Please refrain from using language or requesting content that may be offensive, discriminatory, or otherwise inappropriate.")
        else:
            st.error("Failed to get the image")
    else:
        if response.status_code == 200:
            image_id = response.json()["img_id"]
            image_content = poll_for_image(image_id)
            st.image(image_content)
        else:
            st.error("Failed to get the image ID")
