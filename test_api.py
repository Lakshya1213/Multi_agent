from openai import OpenAI

API_KEY = "llmapi_12012d53f7ea92fee92d5888c4cd098a2de420d2a24051afde16257a551c135b"

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.llmapi.ai/v1"
)

# Take question from user
question = input("Ask your question: ")

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": question}
        ]
    )

    print("\nAnswer:")
    print(response.choices[0].message.content)

except Exception as e:
    print("Error:", e)