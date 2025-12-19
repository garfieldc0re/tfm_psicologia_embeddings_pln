# main.py

import asyncio
from google.adk.runners import InMemoryRunner
from src.agent import agente

async def main():
    runner = InMemoryRunner(agent=agente)
    
    print("Agente TFM Psicología + ADK")
    print("Escribe tu pregunta:\n")

    while True:
        user = input("> ")
        if user.lower() == "salir":
            break

        response = await runner.run_debug(user)
        print("\nAGENTE:\n", response, "\n")

if __name__ == "__main__":
    asyncio.run(main())

