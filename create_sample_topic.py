# create_sample_topic.py
from app.db import create_topic, init_db

# Initialize database
init_db()

# Create a sample topic
sample_topic = {
    'name': 'AI Customer Service Tools',
    'description': 'Research and analyze AI customer service tools market',
    'search_terms': [
        'AI customer service tools 2026',
        'best AI chatbot for customer service'
    ],
    'urls': [
        'https://www.zendesk.com/',
        'https://www.intercom.com/'
    ],
    'schedule_frequency': 'weekly',
    'schedule_time': '09:00',
    'schedule_day': 'monday',
    'email': 'your_email@gmail.com'
}

topic_id = create_topic(sample_topic)
print(f"✅ Sample topic created with ID: {topic_id}")