from collections import deque

history = deque(maxlen=15)

def add_interaction(llm_response):
    history.append({
        "your_response": llm_response,
    })
        
