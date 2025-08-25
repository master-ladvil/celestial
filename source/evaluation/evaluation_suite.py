import asyncio
import time
import os
import json
import tiktoken
from dotenv import load_dotenv  # Import the dotenv function
from source.main import respond_and_speak, initialize_agent

# --- Pydantic model for the Judge's structured response ---
from pydantic import BaseModel, Field
from typing import Optional

# --- LangChain imports for the Judge ---
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Load environment variables from .env file at the very top
load_dotenv()


# --- Define the structure of the Judge's score ---
class QualityScore(BaseModel):
    correctness: int = Field(
        description="The factual accuracy of the answer, from 1 (completely wrong) to 5 (perfectly correct).")
    helpfulness: int = Field(
        description="How well the answer addresses the user's true intent and synthesizes information, from 1 (unhelpful) to 5 (very helpful).")
    clarity: int = Field(description="The structure and readability of the answer, from 1 (unclear) to 5 (very clear).")
    justification: str = Field(description="A brief justification for the scores provided.")
    overall_score: float = Field(description="The average of the three scores.")


# --- Mock Objects for Testing ---
class MockVoice:
    def __init__(self):
        self.last_response = None

    async def speak(self, text):
        print(f"AGENT RESPONSE: {text}")
        self.last_response = text

    async def stop(self):
        pass


# --- Test Cases with Golden Answers ---
TEST_CASES = [
    {
        "id": "time",
        "query": "what time is it right now",
        "golden_answer": "The current time is [current_time]."  # Placeholder, as time changes
    },
    {
        "id": "search",
        "query": "who is the current ceo of microsoft",
        "golden_answer": "The current CEO of Microsoft is Satya Nadella. He has held the position since February 2014."
    },
    {
        "id": "direct_answer",
        "query": "what is the speed of light",
        "golden_answer": "The speed of light in a vacuum is approximately 299,792 kilometers per second (or about 186,282 miles per second)."
    },
    {
        "id": "time and search",
        "query": "check the time and if it is morning search for blindness and if it is night search for night blindness",
        "golden_answer": "Here are some key points about blindness based on the search results: 1. The World Health Organization (WHO) provides a fact sheet on blindness... 2. Over 1 billion people worldwide are living with vision impairment..."
        # Summarized answer
    }
]


async def get_quality_score(judge_chain, query, golden_answer, actual_answer) -> Optional[QualityScore]:
    """Uses the LLM Judge to score the quality of the agent's answer."""
    try:
        response_json = await judge_chain.ainvoke({
            "query": query,
            "golden_answer": golden_answer,
            "actual_answer": actual_answer
        })
        return QualityScore(**response_json)
    except Exception as e:
        print(f"Error getting quality score: {e}")
        return None


async def run_evaluation():
    """Runs the full evaluation suite with latency, token, and quality scoring."""
    print("--- Starting Evaluation Suite for LangChain Baseline ---")

    # --- Initialize Agent, Tokenizer, and Judge ---
    agent_executor = await initialize_agent()
    mock_voice = MockVoice()
    tokenizer = tiktoken.get_encoding("cl100k_base")

    # Initialize the Judge LLM (GPT-4o Mini)
    judge_llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
    parser = JsonOutputParser(pydantic_object=QualityScore)

    judge_prompt_template = """
    You are an impartial AI evaluator. Your task is to assess the quality of an AI agent's response based on a user's query and a 'golden' or ideal answer.

    User Query: "{query}"
    Golden Answer: "{golden_answer}"
    Agent's Actual Answer: "{actual_answer}"

    Please evaluate the agent's answer based on the following criteria and provide a score from 1 to 5 for each.
    1.  **Correctness**: Is the information factually accurate? (1=wrong, 5=correct)
    2.  **Helpfulness**: Does it address the user's intent and synthesize information well? (1=unhelpful, 5=very helpful)
    3.  **Clarity**: Is it well-structured and easy to understand? (1=unclear, 5=very clear)

    Calculate the average of these three scores for the overall_score.
    Provide a brief justification for your scores.

    {format_instructions}
    """

    judge_prompt = PromptTemplate(
        template=judge_prompt_template,
        input_variables=["query", "golden_answer", "actual_answer"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    judge_chain = judge_prompt | judge_llm | parser

    results = []

    for test in TEST_CASES:
        print(f"\n--- Running Test Case: {test['id']} ---")
        print(f"Query: {test['query']}")

        prompt_text = f"Question: {test['query']}"
        prompt_tokens = len(tokenizer.encode(prompt_text))

        start_time = time.perf_counter()
        await respond_and_speak(test['query'], mock_voice, agent_executor)
        end_time = time.perf_counter()
        latency = end_time - start_time

        agent_answer = mock_voice.last_response or ""
        completion_tokens = len(tokenizer.encode(agent_answer))
        total_tokens = prompt_tokens + completion_tokens

        print("--- Getting Quality Score from Judge ---")
        score = await get_quality_score(judge_chain, test['query'], test['golden_answer'], agent_answer)
        quality_score = score.overall_score if score else "N/A"

        results.append({
            "id": test['id'],
            "latency": f"{latency:.2f}s",
            "tokens": total_tokens,
            "quality": f"{quality_score:.2f}/5.00" if isinstance(quality_score, float) else "N/A"
        })

        print(f"Latency: {latency:.2f}s, Tokens: {total_tokens}, Quality: {quality_score}")

    # --- Print Final Report ---
    print("\n\n--- LangChain Baseline Performance Report ---")
    print("-" * 70)
    print(f"{'Test Case':<20} | {'Latency':<10} | {'Tokens':<10} | {'Quality Score':<15}")
    print("-" * 70)
    for res in results:
        print(f"{res['id']:<20} | {res['latency']:<10} | {res['tokens']:<10} | {res['quality']:<15}")
    print("-" * 70)


if __name__ == "__main__":
    # Ensure the API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set.")
    else:
        asyncio.run(run_evaluation())
