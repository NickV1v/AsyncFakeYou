import os
import aiohttp
import asyncio
import aiofiles
import uuid
import logging
from typing import Optional, List, Tuple, Dict, AsyncGenerator
from collections import deque


FAKEYOU_INFERENCE_URL = "https://api.fakeyou.com/tts/inference"
FAKEYOU_JOB_URL = "https://api.fakeyou.com/tts/job/"
BASE_STORAGE_URL = "https://storage.googleapis.com/vocodes-public"


class AsyncAudioGen:
    def __init__(self, cookies: Optional[str] = None, log_level: int = logging.INFO) -> None:
        """
        Initializes the AsyncAudioGen class.

        Args:
            cookies (Optional[str]): Session cookies for authentication with the FakeYou API.
            log_level (int): Logging level
        """
        self._headers: Optional[Dict[str, str]] = None
        if cookies:
            self._headers = {
                "content-type": "application/json",
                "credentials": "include",
                "cookie": f"session={cookies}"
            }
        logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    async def _make_tts_request(self,
                                session: aiohttp.ClientSession,
                                model_token: str,
                                text: str) -> str:
        """
        Sends a text-to-speech (TTS) request to the FakeYou API to generate a job token.

        Args:
            session (aiohttp.ClientSession): An active aiohttp session for making HTTP requests.
            model_token (str): TTS model token for which the TTS request is made.
            text (str): The text phrase that will be converted to speech.

        Returns:
            str: The inference job token for tracking the TTS request.

        Raises:
            aiohttp.ClientError: If the HTTP request fails.
        """
        try:
            self.logger.info("Making TTS request...")
            async with session.post(
                    url=FAKEYOU_INFERENCE_URL,
                    json={
                        "tts_model_token": model_token,
                        "uuid_idempotency_token": str(uuid.uuid4()),
                        "inference_text": text
                    },
                    headers=self._headers
            ) as response:
                response.raise_for_status()
                job_token = (await response.json()).get("inference_job_token")
                self.logger.info(f"Job token obtained: {job_token}")
                return job_token
        except aiohttp.ClientError as e:
            self.logger.error(f"Request failed: {e}")
            raise

    async def _poll_tts_status(self,
                               session: aiohttp.ClientSession,
                               inference_job_token: str,
                               delay: float = 2,
                               max_attempts: int = 50) -> str:
        """
        Polls the FakeYou API to check the status of the TTS request.

        Args:
           session (aiohttp.ClientSession): An active aiohttp session for making HTTP requests.
           inference_job_token (str): The job token obtained from the TTS request.
           delay (float): The delay in seconds between polling attempts.
           max_attempts (int): The maximum number of polling attempts.

        Returns:
           str: URL to the generated audio file.

        Raises:
           aiohttp.ClientError: If the HTTP request fails.
           RuntimeError: If the polling exceeds the maximum attempts.
        """
        attempts = 0
        try:
            self.logger.info("Polling TTS status...")
            while attempts < max_attempts:
                await asyncio.sleep(delay)
                attempts += 1
                async with session.get(
                    f"{FAKEYOU_JOB_URL}{inference_job_token}",
                    headers=self._headers
                ) as response:
                    response.raise_for_status()
                    json_response = await response.json()
                    self.logger.debug(f"Polling attempt: {attempts}/{max_attempts}: {json_response['state']['status']}")
                    if json_response["state"]["maybe_public_bucket_wav_audio_path"]:
                        audio_path = BASE_STORAGE_URL + json_response["state"]["maybe_public_bucket_wav_audio_path"]
                        self.logger.info("Audio file is ready.")
                        return audio_path

            raise RuntimeError("Polling exceeded maximum attempts")
        except aiohttp.ClientError as e:
            self.logger.error(f"Polling failed: {e}")
            raise

    async def download_audio(self,
                             url: str,
                             output_path: str,
                             session: Optional[aiohttp.ClientSession] = None) -> None:
        """
        Downloads the audio file from the specified URL.

        Args:
           url (str): URL of the audio file to download.
           output_path (str): The file path where the audio file will be saved.
           session (Optional[aiohttp.ClientSession]): An active aiohttp session for making HTTP requests.

        Returns:
            None

        Raises:
           aiohttp.ClientError: If the HTTP request fails.
        """
        created_session = False
        if session is None:
            session = aiohttp.ClientSession()
            created_session = True

        try:
            async with session.get(url) as response:
                response.raise_for_status()
                async with aiofiles.open(output_path, "wb") as f:
                    await f.write(await response.read())
                self.logger.info(f"Audio file saved to: {output_path}")
        except aiohttp.ClientError as e:
            self.logger.error(f"Download failed: {e}")
            raise
        finally:
            if created_session:
                await session.close()

    async def fetch_audio(self,
                          model_token: str,
                          text: str,
                          session: Optional[aiohttp.ClientSession] = None) -> str:
        """
        Combines the steps to make a TTS request and poll the status.

        Args:
            model_token (str): TTS model token for which the TTS request is made.
            text (str): The text phrase that will be converted to speech.
            session (Optional[aiohttp.ClientSession]): An active aiohttp session for making HTTP requests.

        Returns:
            str: URL to the generated audio file.

        Raises:
            aiohttp.ClientError: If the HTTP request fails.
            RuntimeError: If the polling exceeds the maximum attempts.
        """
        created_session = False
        if session is None:
            session = aiohttp.ClientSession()
            created_session = True

        try:
            job_token = await self._make_tts_request(session, model_token, text)
            if job_token:
                audio_url = await self._poll_tts_status(session, job_token)
                return audio_url
        except aiohttp.ClientError as e:
            self.logger.error(f"Client error in fetch_audio: {e}")
            raise
        except RuntimeError as e:
            self.logger.error(f"Runtime error in fetch_audio: {e}")
            raise
        finally:
            if created_session:
                await session.close()

    async def fetch_and_save_audio(self,
                                   model_token: str,
                                   text: str,
                                   output_path: str,
                                   filename: str,
                                   session: Optional[aiohttp.ClientSession] = None) -> str:
        """
        Combines the steps to make a TTS request, poll the status, and download the generated audio.

        Args:
            model_token (str): TTS model token for which the TTS request is made.
            text (str): The text phrase that will be converted to speech.
            output_path (str): The directory where the audio file will be saved.
            filename (str): The name of the audio file.
            session (Optional[aiohttp.ClientSession]): An active aiohttp session for making HTTP requests.

        Returns:
            str: URL to the generated audio file.

        Raises:
            aiohttp.ClientError: If the HTTP request fails.
            RuntimeError: If the polling exceeds the maximum attempts.
        """
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        created_session = False
        if session is None:
            session = aiohttp.ClientSession()
            created_session = True

        try:
            audio_url = await self.fetch_audio(model_token, text, session)
            output_audio_path = os.path.join(output_path, filename)
            await self.download_audio(audio_url, output_audio_path, session)
            return audio_url
        except aiohttp.ClientError as e:
            self.logger.error(f"Client error in fetch_and_save_audio: {e}")
            raise
        except RuntimeError as e:
            self.logger.error(f"Runtime error in fetch_and_save_audio: {e}")
            raise
        finally:
            if created_session:
                await session.close()

    async def fetch_tasks(self,
                          audio_tasks: List[Tuple[str, str]],
                          concurrent_tasks: int = 3,
                          delay_after_fail: float = 2) -> AsyncGenerator[str, None]:
        """
        An asynchronous generator that handles a fixed number of tasks in parallel.
        Automatically retries failed tasks. Doesn't change the order when yields.

        Args:
            audio_tasks (List[Tuple[str, str]]): A list of tuples containing model tokens and texts.
            concurrent_tasks (int): The number of tasks to run parallel.
            delay_after_fail (float): The delay in seconds before trying to complete failed tasks again.

        Yields:
            AsyncGenerator[str, None]: URL to the generated audio file.

        Raises:
            None
        """

        indexed_audio_tasks = deque((index, model_token, text) for index, (model_token, text) in enumerate(audio_tasks))
        results = [None]*len(audio_tasks)
        next_index_to_yield = 0

        async def worker(task_idx, model_tkn, txt, s):
            try:
                audio_url = await self.fetch_audio(model_tkn, txt, s)
                results[task_idx] = audio_url
            except Exception as e:
                self.logger.error(f"Task with index '{task_idx}' failed: {e}")
                indexed_audio_tasks.appendleft((task_idx, model_tkn, txt))
                await asyncio.sleep(delay_after_fail)

        async with aiohttp.ClientSession() as session:
            tasks = []
            for _ in range(min(concurrent_tasks, len(indexed_audio_tasks))):
                task_index, model_token, text = indexed_audio_tasks.popleft()
                tasks.append(asyncio.create_task(worker(task_index, model_token, text, session)))

            while tasks or indexed_audio_tasks:
                done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for completed_task in done:
                    tasks.remove(completed_task)
                while next_index_to_yield < len(results) and results[next_index_to_yield] is not None:
                    yield results[next_index_to_yield]
                    next_index_to_yield += 1

                while len(tasks) < concurrent_tasks and indexed_audio_tasks:
                    task_index, model_token, text = indexed_audio_tasks.popleft()
                    tasks.append(asyncio.create_task(worker(task_index, model_token, text, session)))

    async def fetch_and_save_tasks(self,
                                   audio_tasks: List[Tuple[str, str, str]],
                                   output_path: str,
                                   concurrent_tasks: int = 3,
                                   delay_after_fail: float = 2) -> None:
        """
        Handles a fixed number of tasks in parallel. Automatically retries failed tasks.
        Saves generated audio files to the 'output_path' directory.

        Args:
            audio_tasks (List[Tuple[str, str, str]]): A list of tuples containing model tokens, texts, and filenames.
            output_path (str): The directory where the audio files will be saved.
            concurrent_tasks (int): The number of tasks to run parallel.
            delay_after_fail (float): The delay in seconds before trying to complete failed tasks again.

        Returns:
            None

        Raises:
            None
        """
        audio_tasks = deque(audio_tasks)

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        number_of_tasks = len(audio_tasks)
        completed_tasks = 0
        self.logger.info(f"Generation progress: {completed_tasks}/{number_of_tasks}")

        async def worker(model_tkn, txt, flnm, s) -> bool:
            try:
                await self.fetch_and_save_audio(model_tkn, txt, output_path, flnm, s)
                return True
            except Exception as e:
                self.logger.error(f"Task with filename '{flnm}' failed: {e}")
                audio_tasks.appendleft((model_tkn, txt, flnm))
                await asyncio.sleep(delay_after_fail)
                return False

        async with aiohttp.ClientSession() as session:
            tasks = []
            for _ in range(min(concurrent_tasks, len(audio_tasks))):
                model_token, text, filename = audio_tasks.popleft()
                tasks.append(asyncio.create_task(worker(model_token, text, filename, session)))

            while tasks or audio_tasks:
                done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for completed_task in done:
                    tasks.remove(completed_task)
                    if completed_task.result():
                        completed_tasks += 1
                        self.logger.info(f"Generation progress: {completed_tasks}/{number_of_tasks}")

                while len(tasks) < concurrent_tasks and audio_tasks:
                    model_token, text, filename = audio_tasks.popleft()
                    tasks.append(asyncio.create_task(worker(model_token, text, filename, session)))
