import tiktoken
import json
from io import BytesIO
from datetime import datetime
from demo import sys_new_activity


class Agent:
    def __init__(self, openai_client):
        self.openai_client = openai_client
        self.total_tokens = 0
        self.cost = 0.0 

    def num_tokens(self, string: str, encoding_name: str) -> int:
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens
    
    def extract_after_keyword(self, text, keyword="keyword"):
        cleaned_text = re.sub(r'\s+', ' ', text)
        pattern = re.compile(r'\b' + re.escape(keyword) + r':\s*(.*)', re.IGNORECASE)
        match = pattern.search(cleaned_text)
        return match.group(1) if match else None

    def gpt(self, prompt, max_tokens, temp, model):
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "sys_new_activity",
                    "description": "System function to add a new activity and refresh schedule",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date_str": {
                                "type": "string",
                                "description": "Date in 'mm/dd/yyyy' format",
                            },
                            "start_time": {
                                "type": "string", 
                                "description": "Start time in 'HH:MM' 24-hour format"},
                            "end_time": {
                                "type": "string", 
                                "description": "End time in 'HH:MM' 24-hour format"},
                            "title": {
                                "type": "string", 
                                "description": "Title of the activity"},
                            "Description": {
                                "type": "string", 
                                "description": "Description of the activity"},
                            "priority": {
                                "type": "string", 
                                "enum": ["0", "1", "2", "3", "4", "5"],
                                "description": "Priority of the activity (0-5), 5 is highest"},
                        },
                        "required": ["date_str", "start_time", "end_time", "title", "Description", "priority"],
                    },
                },   
            }
        ]

        response = self.openai_client.chat.completions.create(
            model=model,
            messages=prompt,
            temperature=temp,
            max_tokens=max_tokens,
            tools=tools,
            tool_choice="auto"
        )

        print(response.choices[0].message)

        for tool_call in response.choices[0].message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            sys_new_activity(args['date_str'], args['start_time'], args['end_time'], args['title'], args['Description'], int(args['priority']))

        response = response.choices[0].message.content
        prompt_tokens = self.num_tokens(str(prompt), "cl100k_base")
        response_tokens = self.num_tokens(str(response), "cl100k_base")

        # 价目表中的费率，单位是 $/1K tokens
        pricing = {
            'gpt-4o-mini': {'input': 0.0015, 'output': 0.006},
        }

        # 选择当前模型的费率
        rates = pricing.get(model, {'input': 0.0, 'output': 0.0})

        # 计算成本
        self.cost += (prompt_tokens * rates['input'] + response_tokens * rates['output']) / 1000  # 因为费率是每1000个tokens
        self.total_tokens += prompt_tokens + response_tokens

        return response

    def convert_image_to_base64(self, data):
        def encode_image(image):
            # Use certifi to handle SSL certificate verification
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")

        base64_image = encode_image(data)
        image_prompt = [{
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        }]
        
        return image_prompt

    def query(self, history, text_input, image_input):
        # history is a json file describing the current calender
        # text_input is user's text input for scheduling
        # image_input is user's image input for scheduling

        # rag_prompt = [
        #     {"role": "system", "content": "You are a helpful assistant to analyze user's intention and call functions."},
        #     {"role": "user", "content": f"Please analyze if user wants to add an event: {text_input}."},
        # ]
        
        current_date = datetime.now().date() 

        # Refine the prompt so that agent would only make function call.
        rag_prompt = [
            {"role": "system", "content": "You are a helpful assistant to analyze user's intention and call functions based on the current schdule."},
            {"role": "user", "content": f"Add the event using function call based on user's query: {text_input}. Today is {current_date}"},
        ]

        if history:
            rag_prompt.append({"role": "user", "content": f"The current schdule is {history}"})
        

        if image_input:
            image_prompt = self.convert_image_to_base64(image_input)
            rag_prompt.append({"role": "user", "content": image_prompt})

        response = self.gpt(rag_prompt, 256, 0.3, 'gpt-4o-mini')

        return response