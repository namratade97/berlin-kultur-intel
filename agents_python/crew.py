import os
from langchain_community.tools.tavily_search import TavilySearchResults
from crewai import Agent, LLM, Task, Crew, Process
from dotenv import load_dotenv

from crewai_tools import TavilySearchTool 

os.environ["OTEL_SDK_DISABLED"] = "true"

load_dotenv()



gateway_llm = LLM(
    model="openai/berlin-crew-model",
    base_url="http://localhost:4000/v1",
    api_key="sk-1234"
)

# 1. Setting up Search Tool
search_tool = TavilySearchTool(max_results=2)

# 2. Defining the Specialist Agents
def create_berlin_crew(event_raw_data: dict, output_model):
    
    # AGENT 1: The Fact Checker (Verification)
    fact_checker = Agent(
        role='Senior Event Verifier',
        goal=f"Verify if the event '{event_raw_data.get('eventName')}' is actually happening at {event_raw_data.get('venueName')}.",
        backstory="""You are a meticulous researcher. Your job is to prevent hallucinations. 
        You use search engines to cross-reference event dates, locations, and status.""",
        tools=[search_tool],
        max_rpm=2,
        max_iter=3,
        max_tokens=2000,
        llm=gateway_llm, 
        verbose=True
    )

    # AGENT 2: The Cultural Critic (Vibe & Style)
    cultural_critic = Agent(
        role='Berlin Cultural Critic',
        goal="Refine the 'vibeProfile' and 'summary' to be authentic and high-quality.",
        backstory="""You have lived in Berlin for 20 years. You know the difference between 'Techno' 
        and 'Industrial Dubstep'. You ensure the summaries are evocative and culturally accurate. Your summary must be EXACTLY 1-2 sentences.""",
        llm=gateway_llm,
        max_tokens=1200,
        verbose=True
    )

    # 3. Defining the Tasks
    verify_task = Task(
        description=f"Search for '{event_raw_data.get('eventName')}' in Berlin. Confirm if it exists and if the venue is correct.",
        expected_output="A brief report confirming the event's validity and any corrected details.",
        agent=fact_checker
    )

    refine_task = Task(
        description=f"Based on the verification and this raw data: {event_raw_data}, write a definitive Cultural Dossier.",
        expected_output="A structured JSON object with event details and a high-quality summary. Return ONLY a valid JSON object. Do not include any markdown formatting, backticks, or introductory text. Start your response with '{' and end with '}'.",
        agent=cultural_critic,
        context=[verify_task],
        output_pydantic=output_model
    )

    # 4. Assembling the Crew
    return Crew(
        agents=[fact_checker, cultural_critic],
        tasks=[verify_task, refine_task],
        process=Process.sequential # Fact check first, then criticize
    )