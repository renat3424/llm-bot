import asyncio
import os
import aiohttp
from groq import AsyncGroq
from dotenv import load_dotenv
import json

load_dotenv()
headers = {
        "Authorization": f"Bearer {os.getenv('API_KEY')}",
        "Content-Type": "application/json"
    }


url = "https://api.groq.com/openai/v1/models"

async def get_models():
    async with aiohttp.ClientSession() as client:
        async with client.get(url, headers=headers) as resp:

            data=await resp.text()
            print(data)
            data=json.loads(data)['data']
            available_models=[]

            for model in data:
                if not 'whisper' in model['id'] and model['active']:
                    available_models.append({'id': model['id'],
                                                'by': model['owned_by']})
            return available_models


async def send_question(messages, model):
    try:
        client = AsyncGroq(api_key=os.getenv('API_KEY'))
        chat_completion=await client.chat.completions.create(messages=messages, model=model, max_tokens=1024, temperature=0.5)
        return chat_completion.choices[0].message.content
    except Exception as e:
        return '!Exception: '+str(e)



async def image_processing(message, base64_image, model):
    try:
        client = AsyncGroq(api_key=os.getenv('API_KEY'))
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": message if message is not None else 'Describe the image, including any text in the original language (Russian or English, without translation). If the image contains a question, provide the answer.'},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    },
                ],
            }
        ]
        chat_completion = await client.chat.completions.create(messages=messages, model=model, top_p=1, max_tokens=1024)
        return chat_completion.choices[0].message.content
    except Exception as e:
        return '!Exception: '+str(e)