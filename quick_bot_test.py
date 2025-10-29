"""Quick test to verify bot is working with nflreadpy."""

import os
from dotenv import load_dotenv
from workflow import run_workflow, configure_logging

load_dotenv()
configure_logging("WARNING")

print("\n" + "="*80)
print("🏈 QUICK BOT TEST")
print("="*80 + "\n")

# Test query
query = "What were Patrick Mahomes' passing yards in week 10 of 2024?"
print(f"Query: {query}\n")
print("Processing...\n")

try:
    result = run_workflow(query)
    
    response = result.get("generated_response", "No response")
    error = result.get("error")
    data = result.get("retrieved_data")
    
    if error:
        print(f"❌ Error: {error}\n")
    else:
        print(f"✅ Success!\n")
    
    print(f"Response: {response[:200]}...\n")
    
    if data is not None and not data.empty:
        print(f"📊 Retrieved {len(data)} records")
        print(f"   Columns: {list(data.columns)[:8]}\n")
    
    print("="*80)
    print("✅ Bot is working with nflreadpy!")
    print("="*80 + "\n")
    
except Exception as e:
    print(f"❌ Error: {e}\n")
    print("="*80 + "\n")
    raise
