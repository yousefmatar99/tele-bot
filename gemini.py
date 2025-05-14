import json
from google import genai
from google.genai import types
import bot_secrets


def generate(prompt: str, args: str):
    client = genai.Client(
        api_key=bot_secrets.GEMINI_API_KEY,
    )

    model = "gemini-2.0-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=args),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        top_k=40,
        max_output_tokens=8192,
        response_mime_type="application/json",
        system_instruction=[
            types.Part.from_text(text=prompt),
        ],
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )

    return json.loads(response.text)


text = """given the next vector, the vector represents 3*3 grid for tic tec toe game, you are '2', 
return a index for your move"""
arr = ["0" for _ in range(9)]

text = """ 
"""
arr = []
d = generate(text, ", ".join(arr))
print(d)
