"""AI Robot helper — handles @星辰AI助手 detection and API calls."""

import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

# API configuration — Dify Workflow API (from Django settings / environment)
API_URL = settings.AI_ROBOT_API_URL
API_KEY = settings.AI_ROBOT_API_KEY
DIFY_BASE_URL = API_URL.rsplit('/v1/', 1)[0] + '/v1'  # e.g. http://host:port/v1

# The variable name in the Dify workflow that accepts file input
DIFY_FILE_VAR = "input_file"

# Username of the AI robot
ROBOT_USERNAME = "ai_robot"
ROBOT_DISPLAY_NAME = "星辰AI助手"

# File extensions for Dify file type detection
_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}
_DOC_EXT = {".pdf", ".doc", ".docx", ".txt", ".md", ".ppt", ".pptx"}
_ALLOWED_EXT = _IMAGE_EXT | _DOC_EXT


def _dify_file_type(filename: str) -> str:
    """Return 'image' or 'document' based on file extension."""
    from pathlib import Path
    return "image" if Path(filename).suffix.lower() in _IMAGE_EXT else "document"


def _dify_mime(filename: str) -> str:
    """Return MIME type for a given filename."""
    from pathlib import Path
    return {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
        ".svg": "image/svg+xml",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".ppt": "application/vnd.ms-powerpoint",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }.get(Path(filename).suffix.lower(), "application/octet-stream")


def get_robot_user():
    """Return the AI robot User instance (must be called from sync context).
    Auto-creates the robot user if it doesn't exist."""
    from myapp.members.models import User
    try:
        return User.objects.get(username=ROBOT_USERNAME)
    except User.DoesNotExist:
        logger.info("AI robot user not found — auto-creating now")
        robot = User.objects.create(
            username=ROBOT_USERNAME,
            display_name=ROBOT_DISPLAY_NAME,
            avatar_url='/static/avater.jpg',
        )
        robot.set_unusable_password()
        robot.save()
        logger.info(f"AI robot user created (id={robot.id})")
        return robot


def message_mentions_robot(content, robot_name=ROBOT_DISPLAY_NAME):
    """Check if a message content contains @星辰AI助手."""
    if not content:
        return False
    return f"@{robot_name}" in content


def format_conversation_history(messages):
    """Format a list of messages into a readable conversation history string."""
    lines = []
    for m in messages:
        sender = m.get('display_name') or m.get('sender') or 'unknown'
        content = m.get('content', '')
        if content:
            lines.append(f"{sender}: {content}")
    return '\n'.join(lines)


def _get_dify_file_id_from_url(file_url):
    """Download a file from an HTTP URL or local media path and upload it to Dify.
    Returns (file_id, filename) tuple, or (None, None) on failure.
    """
    import httpx
    from pathlib import Path
    try:
        file_bytes = None
        content_type = 'application/octet-stream'
        filename = 'file'

        if file_url.startswith('/media/') or file_url.startswith('media/'):
            # Read directly from filesystem
            rel_path = file_url.lstrip('/')
            fs_path = Path(settings.MEDIA_ROOT) / rel_path[len('media/'):]
            if fs_path.exists():
                file_bytes = fs_path.read_bytes()
                filename = fs_path.name
                content_type = _dify_mime(filename)
                logger.info(f"Read file from disk: {fs_path} ({len(file_bytes)} bytes)")
        else:
            # Download via HTTP
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                dl_resp = client.get(file_url)
                dl_resp.raise_for_status()
                file_bytes = dl_resp.content
                filename = file_url.rsplit('/', 1)[-1] or 'file'
                content_type = _dify_mime(filename)

        if file_bytes is None:
            logger.error(f"Could not read file from: {file_url}")
            return None, None

        # Upload to Dify's file upload endpoint
        upload_url = f"{DIFY_BASE_URL}/files/upload"
        upload_headers = {
            "Authorization": f"Bearer {API_KEY}",
        }
        files = {
            "file": (filename, file_bytes, content_type),
        }
        data = {"user": "ai_robot"}
        with httpx.Client(timeout=60.0) as client:
            up_resp = client.post(upload_url, headers=upload_headers, files=files, data=data)
            up_resp.raise_for_status()
            result = up_resp.json()
            file_id = result.get('id')
            logger.info(f"Dify file upload OK: {filename} -> id={file_id}")
            return file_id, filename
    except Exception as e:
        logger.error(f"Failed to upload file to Dify: {e}")
        return None, None


async def _async_get_dify_file_id_from_url(file_url):
    """Async version: download a file from an HTTP URL or local media path and upload it to Dify.
    Returns (file_id, filename) tuple, or (None, None) on failure.
    """
    import httpx
    from pathlib import Path
    try:
        file_bytes = None
        content_type = 'application/octet-stream'
        filename = 'file'

        if file_url.startswith('/media/') or file_url.startswith('media/'):
            rel_path = file_url.lstrip('/')
            fs_path = Path(settings.MEDIA_ROOT) / rel_path[len('media/'):]
            if fs_path.exists():
                file_bytes = fs_path.read_bytes()
                filename = fs_path.name
                content_type = _dify_mime(filename)
                logger.info(f"Read file from disk: {fs_path} ({len(file_bytes)} bytes)")
        else:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                dl_resp = await client.get(file_url)
                dl_resp.raise_for_status()
                file_bytes = dl_resp.content
                filename = file_url.rsplit('/', 1)[-1] or 'file'
                content_type = _dify_mime(filename)

        if file_bytes is None:
            logger.error(f"Could not read file from: {file_url}")
            return None, None

        upload_url = f"{DIFY_BASE_URL}/files/upload"
        upload_headers = {
            "Authorization": f"Bearer {API_KEY}",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            up_resp = await client.post(
                upload_url, headers=upload_headers,
                files={"file": (filename, file_bytes, content_type)},
                data={"user": "ai_robot"},
            )
            up_resp.raise_for_status()
            result = up_resp.json()
            file_id = result.get('id')
            logger.info(f"Dify file upload OK: {filename} -> id={file_id}")
            return file_id, filename
    except Exception as e:
        logger.error(f"Failed to upload file to Dify: {e}")
        return None, None


async def call_ai_api_async(input_text, history_text, input_file=None):
    """Call the Dify Workflow API and return the response text (async version).
    input_file: optional HTTP URL to a file — will be uploaded to Dify first.
    """
    import httpx

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    inputs = {
        "input": input_text,
        "text": history_text,
    }

    # Upload file to Dify and pass as structured file variable
    if input_file:
        file_id, filename = await _async_get_dify_file_id_from_url(input_file)
        if file_id and filename:
            inputs[DIFY_FILE_VAR] = {
                "type": _dify_file_type(filename),
                "transfer_method": "local_file",
                "upload_file_id": file_id,
            }

    payload = {
        "inputs": inputs,
        "response_mode": "blocking",
        "user": "ai_robot",
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(API_URL, json=payload, headers=headers)
            if not resp.is_success:
                logger.error(f"API returned {resp.status_code}: {resp.text[:500]}")
            resp.raise_for_status()
            data = resp.json()
            outputs = data.get('data', {}).get('outputs', {})
            if isinstance(outputs, dict):
                return outputs.get('text') or outputs.get('response') or json.dumps(outputs, ensure_ascii=False)
            if isinstance(outputs, str):
                return outputs
            return json.dumps(data, ensure_ascii=False)
    except httpx.HTTPStatusError as e:
        body = e.response.text[:500] if hasattr(e, 'response') else ''
        logger.error(f"AI API HTTP error: {e} — body: {body}")
        return f"抱歉，星辰AI助手暂时无法回复（API请求失败，请检查工作流配置）"
    except Exception as e:
        logger.error(f"AI API call failed: {e}")
        return f"抱歉，星辰AI助手暂时无法回复（错误：{str(e)[:80]}）"


def call_ai_api_sync(input_text, history_text, input_file=None):
    """Call the Dify Workflow API and return the response text (sync version).
    input_file: optional HTTP URL to a file — will be uploaded to Dify first.
    """
    import httpx

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    inputs = {
        "input": input_text,
        "text": history_text,
    }

    # Upload file to Dify and pass as structured file variable
    if input_file:
        file_id, filename = _get_dify_file_id_from_url(input_file)
        if file_id and filename:
            inputs[DIFY_FILE_VAR] = {
                "type": _dify_file_type(filename),
                "transfer_method": "local_file",
                "upload_file_id": file_id,
            }

    payload = {
        "inputs": inputs,
        "response_mode": "blocking",
        "user": "ai_robot",
    }

    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(API_URL, json=payload, headers=headers)
            if not resp.is_success:
                logger.error(f"API returned {resp.status_code}: {resp.text[:500]}")
            resp.raise_for_status()
            data = resp.json()
            outputs = data.get('data', {}).get('outputs', {})
            if isinstance(outputs, dict):
                return outputs.get('text') or outputs.get('response') or json.dumps(outputs, ensure_ascii=False)
            if isinstance(outputs, str):
                return outputs
            return json.dumps(data, ensure_ascii=False)
    except httpx.HTTPStatusError as e:
        body = e.response.text[:500] if hasattr(e, 'response') else ''
        logger.error(f"AI API HTTP error: {e} — body: {body}")
        return f"抱歉，星辰AI助手暂时无法回复（API请求失败，请检查工作流配置）"
    except Exception as e:
        logger.error(f"AI API call failed: {e}")
        return f"抱歉，星辰AI助手暂时无法回复（错误：{str(e)[:80]}）"
