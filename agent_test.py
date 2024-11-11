from agent import Agent
from openai import OpenAI
import openai
from demo import sys_new_activity,load_data
import json

client = OpenAI()

schdule = load_data()

agent = Agent(client)
text_query = "This weekend I need to review for my midterm, it should take me 4 hours"
print(agent.query(schdule, text_query, None))