import os
import sys
import shutil
from src.tools.registry import ToolRegistry
from src.agent.main_agent import MainAgent


def run_demo():
    print("Initializing real ToolRegistry and registering 10 tools...")
    db_path = "./demo_chroma_db_extended"
    registry = ToolRegistry(db_path=db_path)
    registry.register_all()

    print("Initializing MainAgent with DeepSeek-V3.2-fast...")
    agent = MainAgent(registry=registry)

    # Zorlu ve Çeşitlendirilmiş Senaryolar
    queries = [
        # 1. Hava Durumu (Standart Retrieval Testi)
        "What is the weather like in Tokyo right now? Use celsius.",
        
        # 2. Matematik / Code Executor Testi
        "Calculate the square root of 15241578750190521 using python.",
        
        # 3. Currency / Forex Testi
        "Convert 1500 USD to EUR.",
        
        # 4. Database Testi (SQL)
        "Can you query the main database and give me the names of the employees?",
        
        # 5. Translation Testi
        "Translate 'Artificial Intelligence is the future' into German.",
        
        # 6. Timer vs Calendar Zorluk Testi (False-Positive Check)
        "Set an alarm for 07:30 AM tomorrow with the message 'Wake up'.",

        # 7. Hallucination / Reject Testi
        "Can you teleport me to Mars using quantum entanglement?",
        
        # 8. Small Talk
        "Hey! How are you doing today?",
    ]

    output_file = "agent_extended_thinking_process.txt"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=== EXTENDED AGENT THINKING PROCESS & TOOL RETRIEVAL LOGS ===\n\n")

        for i, query in enumerate(queries, 1):
            print(f"Running Scenario {i}/{len(queries)}...")
            f.write(f"{'='*70}\n")
            f.write(f"SCENARIO {i}: USER QUERY: '{query}'\n")
            f.write(f"{'='*70}\n\n")

            final_response = agent.run(query)

            # Yazdır agent loglarını
            for log in agent.logger.get_logs():
                f.write(f"[{log['step'].upper()}] {log['message']}\n")
                if log['data']:
                    for key, val in log['data'].items():
                        f.write(f"    --> {key}: {val}\n")
            
            f.write(f"\n[FINAL ASSISTANT RESPONSE]:\n{final_response}\n\n")

    print(f"\nExtended Demo finished! Logs written to: {output_file}")
    
    # Cleanup DB
    shutil.rmtree(db_path, ignore_errors=True)

if __name__ == "__main__":
    run_demo()
