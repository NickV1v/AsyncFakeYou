import aiohttp
import os


FAKEYOU_LOGIN_URL = "https://api.fakeyou.com/v1/login"
FAKEYOU_MODELS_URL = "https://api.fakeyou.com/tts/list"


async def get_models_list(output_path: str = "./") -> None:
    """
    Asynchronously fetches the list of models from the FakeYou website and saves it to a `models_list.txt` file

    Args:
        output_path (str): The directory path where the file will be saved. Default is "./".

    Returns:
        None

    Raises:
        aiohttp.ClientError: If an error occurs during the HTTP request.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(FAKEYOU_MODELS_URL) as response:
                response.raise_for_status()
                with open(os.path.join(output_path, "models_list.txt"), "w") as file:
                    file.write(str(response.content))
    except aiohttp.ClientError as e:
        print(f"Client error: {e}")
        raise


async def receive_cookies(username_or_email: str, password: str) -> str:
    """
    Asynchronously logs into the FakeYou website and retrieves session cookies.

    Args:
        username_or_email (str): The username or email address for login.
        password (str): The user's password.

    Returns:
        str: The session cookies returned by the server after successful authentication.

    Raises:
        aiohttp.ClientError: If an error occurs during the HTTP request.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(FAKEYOU_LOGIN_URL, json={
                "username_or_email": username_or_email,
                "password": password
            }) as response:
                response.raise_for_status()
                headers = response.headers
                return headers["Set-Cookie"].split(';')[0][8:]
    except aiohttp.ClientError as e:
        print(f"Authentication failed. Make sure that you have entered your username and password correctly: {e}")
        raise
