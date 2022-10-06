import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry


def has_markdown_lint_errors(file_content: str, file_path='file', fix=False) -> dict:
    retry = Retry(total=2)
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount('http://', adapter)
    return session.request(
        'POST',
        f'http://localhost:6161/markdownlint?filename={file_path}&fix={fix}',
        data=file_content.encode('utf-8'),
        timeout=20
    ).json()
