from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile")

history = [
    SystemMessage(content="You are a helpful assistant.")
]

def chat(user_message: str) -> str:
    history.append(HumanMessage(content=user_message))

    response = llm.invoke(history)

    history.append(AIMessage(content=response.content))
    return response.content

def main():
    print("Chatbot ready. Type 'quit' to exit.\n")
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "quit":
            break
        reply = chat(user_input)
        print(f"Assistant: {reply}\n")

if __name__ == "__main__":
    main()