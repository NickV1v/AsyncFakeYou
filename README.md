# AsyncFakeYou
AsyncFakeYou is an asynchronous Python library for interacting with the [FakeYou](https://fakeyou.com) Text-to-Speech API. It allows you to submit TTS requests, track their status, and download the resulting audio files, all in an asynchronous manner using asyncio, aiohttp and aiofiles.

## Features
* Asynchronous requests to [FakeYou](https://fakeyou.com) TTS API.
* Generation with parallel execution control
* Handle user authentication with session cookies

## Installation
```
pip install asyncfakeyou
```
## Simple usage
You can obtain a direct URL to the generated audio file.

```python
from asyncfakeyou import AsyncAudioGen
import asyncio


async def text_to_speech():
    gen = AsyncAudioGen(cookies="your_cookie_string")
    audio_url = await gen.fetch_audio("model_token_here", "sample_text")
    print(audio_url)


asyncio.run(text_to_speech())
```
Or you can download the generated audio file to a specified directory.

```python
from asyncfakeyou import AsyncAudioGen
import asyncio


async def text_to_speech():
    gen = AsyncAudioGen(cookies="your_cookie_string")
    audio_url = await gen.fetch_and_save_audio("model_token_here", "sample_text",
                                               output_path="./audio",
                                               filename="generated_audio.wav")
    print(audio_url)


asyncio.run(text_to_speech())
```

## How to obtain cookies?

The `cookies` parameter of the `AsyncAudioGen` class is optional. However, I recommend setting it as it will give you higher queue priority, even without a paid subscription. If you have a premium account, you will be able to take advantage of all its benefits through this API.

```python
from asyncfakeyou import receive_cookies
import asyncio


async def get_my_cookies():
    cookies = await receive_cookies("your_username_or_email", "your_password")
    print(cookies)


asyncio.run(get_my_cookies())
```
## Parallel execution

If you need to generate multiple audio files, you can speed up the process by using `fetch_tasks` and `fetch_and_save_tasks`. These methods handle a fixed number of tasks in parallel (`concurrent_tasks` parameter) and automatically retry failed requests. The default value for `concurrent_tasks` is 3, but you can tweak this parameter.

You can iterate through the direct URLs to the generated audio files.

```python
from asyncfakeyou import AsyncAudioGen
import asyncio


async def multiple_text_to_speech():
    gen = AsyncAudioGen(cookies="your_cookie_string")
    audio_tasks = [
        ("model_token_1", "sample_text_1"),
        ("model_token_2", "sample_text_2"),
        ("model_token_3", "sample_text_3")
    ]
    async for audio_url in gen.fetch_tasks(audio_tasks):
        print(audio_url)


asyncio.run(multiple_text_to_speech())
```
Or you can download the generated audio files to a specified directory.

```python
from asyncfakeyou import AsyncAudioGen
import asyncio


async def multiple_text_to_speech():
    gen = AsyncAudioGen(cookies="your_cookie_string")
    audio_tasks = [
        ("model_token_1", "sample_text_1", "filename1.wav"),
        ("model_token_2", "sample_text_2", "filename2.wav"),
        ("model_token_3", "sample_text_3", "filename3.wav")
    ]
    await gen.fetch_and_save_tasks(audio_tasks, output_path="./audio")


asyncio.run(multiple_text_to_speech())
```
## Contributing
Contributions are welcome! Please fork the repository and create a pull request with your improvements.
