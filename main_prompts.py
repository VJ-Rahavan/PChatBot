from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from typing import Literal
 
load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile")


# ── 1. Few-Shot Prompting ────────────────────────────────────────────────────

def few_shot_sentiment():
    examples = [
        {"input": "I love this product!", "output": "Positive"},
        {"input": "This is the worst experience ever.", "output": "Negative"},
        {"input": "It's okay, nothing special.", "output": "Neutral"},
        {"input": "Absolutely fantastic, exceeded expectations!", "output": "Positive"},
    ]

    example_prompt = ChatPromptTemplate.from_messages([
        ("human", "{input}"),
        ("ai", "{output}"),
    ])

    few_shot_prompt = FewShotChatMessagePromptTemplate(
        example_prompt=example_prompt,
        examples=examples,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Classify the sentiment of the user's message as Positive, Negative, or Neutral."),
        few_shot_prompt,
        ("human", "{input}"),
    ])

    chain = prompt | llm | StrOutputParser()

    test_inputs = [
        "The delivery was late and the item was broken.",
        "I'm so happy with my purchase!",
        "It does the job.",
    ]

    print("=" * 50)
    print("1. FEW-SHOT PROMPTING — Sentiment Classification")
    print("=" * 50)
    for text in test_inputs:
        result = chain.invoke({"input": text})
        print(f"  Input : {text}")
        print(f"  Output: {result}\n")


# ── 2. Chain of Thought Prompting ────────────────────────────────────────────

def chain_of_thought():
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a math tutor. When given a problem, think through it step by step "
         "before giving the final answer. Show your reasoning clearly."),
        ("human", "{problem}"),
    ])

    chain = prompt | llm | StrOutputParser()

    problems = [
        "A train travels 60 mph for 2.5 hours, then 80 mph for 1.5 hours. What is the total distance?",
        "If a shirt costs $40 after a 20% discount, what was the original price?",
    ]

    print("=" * 50)
    print("2. CHAIN OF THOUGHT PROMPTING — Math Reasoning")
    print("=" * 50)
    for problem in problems:
        result = chain.invoke({"problem": problem})
        print(f"  Problem: {problem}")
        print(f"  Reasoning:\n{result}\n")


# ── 3. Structured Output ─────────────────────────────────────────────────────

class MovieReview(BaseModel):
    title: str = Field(description="Title of the movie")
    genre: Literal["Action", "Comedy", "Drama", "Horror", "Sci-Fi", "Other"] = Field(description="Genre of the movie")
    rating: int = Field(description="Rating out of 10", ge=1, le=10)
    summary: str = Field(description="One-sentence summary of the review")
    recommended: bool = Field(description="Whether the reviewer recommends the movie")


def structured_output():
    structured_llm = llm.with_structured_output(MovieReview)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a movie critic. Analyze the user's review and extract structured information."),
        ("human", "{review}"),
    ])

    chain = prompt | structured_llm

    reviews = [
        "I just watched Interstellar again. The visuals are stunning and the score is haunting. "
        "A complex but rewarding sci-fi experience. Easily a 9 out of 10, must watch!",
        "The new horror film was disappointing — jump scares with no real tension. "
        "I'd give it a 4, not worth your time.",
    ]

    print("=" * 50)
    print("3. STRUCTURED OUTPUT — Movie Review Extraction")
    print("=" * 50)
    for review in reviews:
        result: MovieReview = chain.invoke({"review": review})
        print(f"  Review   : {review[:60]}...")
        print(f"  Title    : {result.title}")
        print(f"  Genre    : {result.genre}")
        print(f"  Rating   : {result.rating}/10")
        print(f"  Summary  : {result.summary}")
        print(f"  Recommend: {result.recommended}\n")


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    few_shot_sentiment()
    chain_of_thought()
    structured_output()
