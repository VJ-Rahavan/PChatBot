from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

load_dotenv()

def get_llm(provider: str):
    if provider == "groq" or provider == "1":
        return ChatGroq(model="llama-3.3-70b-versatile")
    elif provider == "gemini" or provider == "2":
        return ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    else:
        raise ValueError(f"Unknown provider: {provider}")

SYSTEM_PROMPT = "You are a helpful assistant."

history = [
    SystemMessage(content=SYSTEM_PROMPT)
]

def clear_history():
    history.clear()
    history.append(SystemMessage(content=SYSTEM_PROMPT))

def chat(llm, user_message: str) -> str:
    history.append(HumanMessage(content=user_message))
    response = llm.invoke(history)
    history.append(AIMessage(content=response.content))
    return response.content

def main():
    print("Select provider:")
    print("1. groq")
    print("2. gemini")
    provider = input("Enter provider: ").strip().lower()

    llm = get_llm(provider)
    c = "Groq" if provider in ["groq", "1"] else "Gemini"
    print(f"\nChatbot ready ({c}). Type 'quit' to exit, 'clear' to reset history.\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "quit":
            break
        if user_input.lower() == "clear":
            clear_history()
            print("History cleared.\n")
            continue
        reply = chat(llm, user_message=user_input)
        print(f"Assistant: {reply}\n")

if __name__ == "__main__":
    main()