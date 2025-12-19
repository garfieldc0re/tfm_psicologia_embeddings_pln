#Agente adk
# src/agent.py
# src/agent.py

from google.adk.agents.llm_agent import Agent
import tools

agente = Agent(
    name="agente_tfm",
    model="gemini-1.5-flash",
    description="Agente para analizar actitudes en posts de psicología.",
    tools=[
        tools.cargar_posts,
        tools.filtrar_por_subreddit,
        tools.analizar_actitud,
    ],
)

