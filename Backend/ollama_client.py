
import json
import urllib.request
import urllib.error


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "ami-test"


def chat_with_yona(messages):
    """Send a conversation to the local Ollama model."""

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "keep_alive": "24h",
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            result = json.loads(response.read().decode("utf-8"))

        return result["message"]["content"]

    except urllib.error.URLError as error:
        raise ConnectionError(
            f"Unable to connect to Ollama: {error}"
        ) from error

    except (KeyError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"Invalid response from Ollama: {error}"
        ) from error
