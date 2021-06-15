import asyncio
import base64
import hashlib
import hmac
import logging
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

import requests

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel("INFO")


def upload_file_to_dataset(
    base_url: str,
    api_key: str,
    api_secret: str,
    dataset_name: str,
    dataset_version: str,
    filename: str,
    directory: str,
    ) -> Tuple[bool, str]:
    content_type = "application/text"

    print('{}/{}'.format(directory, filename))
    # dataset_file_content = Path(f"{directory}/{filename}").read_bytes()
    dataset_file_content = Path('{}/{}'.format(directory, filename)).read_bytes()
    md5_hash_bytes = hashlib.md5(dataset_file_content).digest()
    md5_hash_b64 = base64.b64encode(md5_hash_bytes).decode("utf-8")

    params = {
        "filename": filename,
        "datasetFileContentType": content_type,
        "md5": md5_hash_b64,
    }
    # endpoint = f"{base_url}/{dataset_name}/versions/{dataset_version}/files/uploadUrl"
    endpoint = "{}/{}/versions/{}/files/uploadUrl".format(base_url, dataset_name, dataset_version)
    headers = generate_signature_headers(api_key, api_secret.encode("utf-8"))

    upload_url_response = requests.get(
        endpoint, headers=headers, params=params)

    # retrieve upload URL for dataset file
    if upload_url_response.status_code != 200:
        # logger.warning(f"Unable to get upload url for :{filename}")
        logger.warning("Unable to get upload url for :{}".format(filename))
        logger.warning(upload_url_response.content)
        return False, filename

    upload_url = upload_url_response.json()["temporaryUploadUrl"]

    # max file size supported by Python requests library 2.14 gb
    # in the future we will support bigger files using Multipart upload
    headers = {"Content-MD5": md5_hash_b64, "Content-Type": content_type}
    logger.info("Start file upload for: {}".format(filename))
    upload_response = requests.put(
        upload_url, data=dataset_file_content, headers=headers
    )

    if upload_response.status_code != 200:
        logger.warning("Unable to upload file: {}".format(filename))
        logger.warning(upload_response.content)
        return False, filename

    logger.info("Upload of '{}' successful".format(filename))
    return True, filename


def generate_signature_headers(key_id: str, hmac_secret_key: bytearray):
    now_utc = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %Z")

    # signature_string = f"date: {now_utc}".encode("utf-8")
    signature_string = "date: {}".format(now_utc).encode("utf-8")

    hmac_digest = hmac.new(
        hmac_secret_key, signature_string, hashlib.sha512).digest()
    hmac_digest_b64 = base64.b64encode(hmac_digest).decode("utf-8")
    hmac_digest_b64_url_encoded = urllib.parse.quote_plus(hmac_digest_b64)

    return {
        "Date": now_utc,
        # "Authorization": f'Signature keyId="{key_id}",algorithm="hmac-sha512",'
        # f'signature="{hmac_digest_b64_url_encoded}" ',
        "Authorization": 'Signature keyId="{}",algorithm="hmac-sha512",'
        'signature="{}" '.format(key_id, hmac_digest_b64_url_encoded),
    }


async def main():

    api_key = "eyJvcmciOiI1ZTU1NGUxOTI3NGE5NjAwMDEyYTNlYjEiLCJpZCI6ImQ5ODkzZTkwNTE3OTQ1ODBiZjQxYjUzMWIyMjU5YzgxIiwiaCI6Im11cm11cjEyOCJ9"  # "<API_KEY>"
    hmac_secret = "ZjM0YjczOWExODhjNGMwNmExNGIzMzYwYTZjZGQzNzU="  # "<API_SECRET>"
    dataset_name = "scintillatiedata" # "<DATASET_NAME>"
    dataset_version = "v1" # "<DATASET_VERSION>"
    base_url = "https://api.dataplatform.knmi.nl/dataset-content/v1/datasets"

    # folder that contains the files to be uploaded
    upload_directory = "./data" #"./my-dataset-files"

    # Verify that the directory exists
    if not Path(upload_directory).is_dir():
        raise Exception(
            # f"Invalid or non-existing directory: {upload_directory}")
            "Invalid or non-existing directory: {}".format(upload_directory))

    loop = asyncio.get_event_loop()

    # Allow up to 20 separate threads to upload dataset files concurrently
    executor = ThreadPoolExecutor(max_workers=20)
    futures = []

    # Create tasks that upload the dataset files
    folder_content = Path(upload_directory).glob("*.ismr")
    files_to_upload = [x for x in folder_content if x.is_file()]
    logger.info("Number of files to upload: {}".format(len(files_to_upload)))
    for file_to_upload in files_to_upload:
        # Create future for dataset file
        future = loop.run_in_executor(
            executor,
            upload_file_to_dataset,
            base_url,
            api_key,
            hmac_secret,
            dataset_name,
            dataset_version,
            file_to_upload.name,
            upload_directory,
        )
        futures.append(future)

    # Wait for all tasks to complete and gather the results
    future_results = await asyncio.gather(*futures)
    logger.info("Finished '{}' uploading".format(dataset_name))

    failed_uploads = list(filter(lambda x: not x[0], future_results))

    if len(failed_uploads) > 0:
        logger.info("Failed to upload the following dataset files")
        logger.info(list(map(lambda x: x[1], failed_uploads)))


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
