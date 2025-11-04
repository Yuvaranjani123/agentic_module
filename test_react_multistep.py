"""
Test ReAct Multi-Step Query
Tests the ReAct agent with a complex multi-step query
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/agents"

def test_react_multi_step():
    """Test ReAct with 'calculate then compare' query."""
    print("\n" + "="*70)
    print("Testing ReAct Multi-Step Query")
    print("="*70)
    
    # The complex query that ReAct should handle well
    query = "Calculate premium for ActivAssure with 2 adults aged 32 and 45, 1 child aged 8, then compare the cost with ActivFit"
    
    print(f"\nQuery: {query}")
    print("\nExpected ReAct Flow:")
    print("  1. Thought: Need to calculate premium first")
    print("  2. Action: premium_calculator")
    print("  3. Observation: [Premium result]")
    print("  4. Thought: Now compare with ActivFit")
    print("  5. Action: policy_comparator")
    print("  6. Observation: [Comparison result]")
    print("  7. Thought: Have all info, finish")
    print("  8. Action: finish")
    
    print("\n" + "-"*70)
    print("TESTING WITH REACT (use_react=true)")
    print("-"*70)
    
    try:
        response = requests.post(
            f"{BASE_URL}/agentic/query/",
            json={
                "query": query,
                "use_react": True,
                "conversation_history": []
            },
            timeout=60
        )
        
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ Mode: {result.get('mode', 'N/A')}")
            print(f"✅ Success: {result.get('success', False)}")
            
            # Show reasoning trace
            trace = result.get('reasoning_trace', {})
            print(f"\n📊 Reasoning Trace:")
            print(f"   Iterations: {trace.get('iterations', 0)}")
            print(f"   Success: {trace.get('success', False)}")
            
            steps = trace.get('steps', [])
            print(f"   Total Steps: {len(steps)}")
            
            # Show each step
            print("\n📝 Step-by-Step Reasoning:")
            for i, step in enumerate(steps[:20], 1):  # Limit to first 20 steps
                step_type = step.get('step_type', '')
                
                if step_type == 'thought':
                    content = step.get('content', '')[:100]
                    print(f"\n   💭 Thought {step.get('step_number', '?')}: {content}...")
                elif step_type == 'action':
                    tool = step.get('tool_used', 'unknown')
                    print(f"   🔧 Action: {tool}")
                elif step_type == 'observation':
                    obs = str(step.get('tool_output', ''))[:100]
                    print(f"   👀 Observation: {obs}...")
                elif step_type == 'final_answer':
                    print(f"   ✅ Final Answer Generated")
            
            # Show final answer
            final_answer = result.get('final_answer', 'No answer')
            print(f"\n🎯 Final Answer:")
            print(f"   {final_answer[:300]}...")
            
            # Show metadata
            metadata = result.get('agentic_metadata', {})
            print(f"\n📈 Metadata:")
            print(f"   Reasoning Iterations: {metadata.get('reasoning_iterations', 0)}")
            print(f"   Tools Used: {metadata.get('tools_used', [])}")
            print(f"   Dynamic Routing: {metadata.get('dynamic_routing', False)}")
            print(f"   ReAct Enabled: {metadata.get('react_enabled', False)}")
            
        else:
            print(f"❌ Error: {response.text}")
    
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>60s)")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "-"*70)
    print("TESTING WITH TRADITIONAL MODE (use_react=false)")
    print("-"*70)
    
    try:
        response = requests.post(
            f"{BASE_URL}/agentic/query/",
            json={
                "query": query,
                "use_react": False,
                "conversation_history": []
            },
            timeout=60
        )
        
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ Mode: {result.get('mode', 'N/A')}")
            print(f"✅ Success: {result.get('success', False)}")
            
            # Show tasks
            tasks = result.get('tasks', [])
            print(f"\n📋 Tasks Decomposed: {len(tasks)}")
            for task in tasks:
                print(f"   - {task.get('description', '')[:80]}... [{task.get('status', 'unknown')}]")
            
            # Show metadata
            metadata = result.get('agentic_metadata', {})
            print(f"\n📈 Metadata:")
            print(f"   Tasks Executed: {metadata.get('tasks_executed', 0)}")
            print(f"   Agents Involved: {metadata.get('agents_involved', [])}")
            print(f"   ReAct Enabled: {metadata.get('react_enabled', False)}")
            
        else:
            print(f"❌ Error: {response.text}")
    
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>60s)")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "="*70)
    print("Test Complete!")
    print("="*70)
    print("\nKey Observations:")
    print("  • ReAct mode should show iterative reasoning steps")
    print("  • ReAct should use multiple tools (calculator + comparator)")
    print("  • Traditional mode might miss the multi-step nature")
    print("  • ReAct enables 'calculate THEN compare' queries")


if __name__ == "__main__":
    print("="*70)
    print("ReAct Multi-Step Query Test")
    print("="*70)
    print("\nMake sure Django server is running:")
    print("  cd backend && python manage.py runserver")
    print()
    
    input("Press Enter to start test...")
    
    test_react_multi_step()
