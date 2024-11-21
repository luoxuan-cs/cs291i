from agent import Agent
from openai import OpenAI
import openai
from demo import load_data, save_data
import json

client = OpenAI()

schdule = load_data()

agent = Agent(client)
text_query = "I have an exam today at 8am to 9am. I must arrive before 8am"
# text_query = "This weekend "
response, cot_response, history = agent.query(schdule, text_query, None)
# save_data(history)
print(cot_response)
# print(agent.query(schdule, text_query, None))