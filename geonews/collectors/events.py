from ..database import save_event

EVENTS = [
    {
        
    }
]

def seed_events():
    return sum(1 for e in EVENTS if e.get("name") and e.get("event_date") and save_event(e))
