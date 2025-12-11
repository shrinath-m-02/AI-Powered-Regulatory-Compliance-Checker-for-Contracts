import os
from dotenv import load_dotenv
from groq import Groq
load_dotenv()

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Explain the importance of fast language models",
        },
        # {
        #     "role":"system",
        #     "content":"Help to answer my queries in to the point and concise way ",
        # }
    ],
    model="llama-3.3-70b-versatile",
    max_tokens=500,
    temperature=0.3,
    top_p=1,
)

print(chat_completion.choices[0].message.content)

