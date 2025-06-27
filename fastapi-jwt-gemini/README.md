# FastAPI JWT Authentication Example

This project is a simple example of how to implement JWT authentication in a FastAPI application.

## Running the Project

### Using Docker

**Prerequisites:**

* Docker
* Docker Compose

**Instructions:**

1.  **Build and run the container:**

    ```bash
    docker-compose up -d --build
    ```

2.  **Access the API:**

    The API will be available at `http://localhost:8000`.

### Locally

**Prerequisites:**

* Python 3.9+
* pip

**Instructions:**

1.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the application:**

    ```bash
    uvicorn main:app --reload
    ```

## Testing the Project

1.  **Access the interactive documentation:**

    Go to `http://localhost:8000/docs` in your browser.

2.  **Get a token:**

    *   Click on the `/token` endpoint.
    *   Click "Try it out".
    *   Enter `johndoe` for the username and `secret` for the password.
    *   Click "Execute".
    *   Copy the `access_token` from the response.

3.  **Authorize your requests:**

    *   Click the "Authorize" button at the top of the page.
    *   In the "Value" field, paste the `access_token` you copied.
    *   Click "Authorize".

4.  **Test the protected endpoints:**

    *   Click on any of the protected endpoints (e.g., `/users/me`).
    *   Click "Try it out".
    *   Click "Execute".

    You should now be able to see the response from the protected endpoint.
