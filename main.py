from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq()
history = [
    {"role": "system", "content": "You are a helpful assistant."}
]

def chat(user_message: str) -> str:
    history.append({"role": "user", "content": user_message})
    
    stream = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=history,
        stream=True
    )

    full_response = ""
    print("Assistant: ", end="", flush=True)
    
    for chunk in stream:
        text = chunk.choices[0].delta.content or ""
        print(text, end="", flush=True)
        full_response += text
    
    print()
    history.append({"role": "assistant", "content": full_response})
    return full_response

def main():
    print("Chatbot ready. Type 'quit' to exit.\n")
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "quit":
            break
        chat(user_input)

if __name__ == "__main__":
    main()