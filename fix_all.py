import os

# 1. Patch workflow.py for rate limits
path = "utils/workflow.py"
if os.path.exists(path):
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()

    if "import time" not in code:
        code = "import time\n" + code

    old_target = "                rel_result = relation_agent.extract(chunk, entity_result.entities, state[\"ontology\"])\n                all_triples.extend(rel_result.triples)"
    new_target = old_target + "\n            \n            # Anti-Rate-Limit for Groq\n            time.sleep(2.0)"

    if old_target in code:
        code = code.replace(old_target, new_target)
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        print("✅ Patched utils/workflow.py (Added rate-limit protection)")
    else:
        print("⚠️ utils/workflow.py already patched or pattern not found.")
else:
    print("❌ Could not find utils/workflow.py")

# 2. Update .env.example
env_example = """# Database Config
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Groq API
GROQ_API_KEY=gsk_your_api_key_here

# LLM Selection Settings
DEFAULT_LLM_PROVIDER=groq
DEFAULT_MODEL=llama-3.1-70b-versatile

# Document Processing Defaults
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
"""
with open(".env.example", "w", encoding="utf-8") as f:
    f.write(env_example)
print("✅ Patched .env.example")

# 3. Update requirements.txt
req_path = "requirements.txt"
if os.path.exists(req_path):
    with open(req_path, "r", encoding="utf-8") as f:
        req_code = f.read()
    
    if "langchain-groq>=0.1.3" not in req_code:
        req_code = req_code.replace("langchain-groq\n", "langchain-groq>=0.1.3\n")
        with open(req_path, "w", encoding="utf-8") as f:
            f.write(req_code)
    print("✅ Patched requirements.txt (Pinned langchain-groq version)")
else:
    print("❌ Could not find requirements.txt")

print("\n🎉 ALL SET! You can now start the application.")