import tiktoken
import json
from io import BytesIO
from datetime import datetime
import base64

DATA_FILE = 'schedule_data.json'

# Load data function
def load_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

# Save data function
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Date selection function
def select_date():
    selected_date = st.date_input("Select Date", date.today(), key='date_selector')
    selected_date_str = selected_date.strftime('%m/%d/%Y')
    return selected_date_str

# system functions
# =====================================================================================
def sys_new_activity(date_str, start_time, end_time, title, description, priority):
    """
    System function to add a new activity and refresh schedule.

    Parameters:
    - date_str (str): Date in 'mm/dd/yyyy' format.
    - start_time (str): Start time in 'HH:MM' 24-hour format.
    - end_time (str): End time in 'HH:MM' 24-hour format.
    - title (str): Title of the activity.
    - description (str): Description of the activity.
    - priority (int): Priority of the activity (0-5).

    """
    # Load current schedule data
    schedule_data = load_data()
    
    # Check if the date is valid
    try:
        datetime.strptime(date_str, '%m/%d/%Y')
    except ValueError:
        print("Invalid date format. Please use 'mm/dd/yyyy'.")
        return

    # Ensure start and end times are in valid format and logic
    try:
        if datetime.strptime(start_time, '%H:%M') >= datetime.strptime(end_time, '%H:%M'):
            print("Start time must be earlier than end time.")
            return
    except ValueError:
        print("Invalid time format. Please use 'HH:MM'.")
        return

    # Check if title is non-empty
    if not title.strip():
        print("Title cannot be empty.")
        return

    # Create new activity
    new_activity = {
        'start_time': start_time,
        'end_time': end_time,
        'title': title,
        'description': description,
        'priority': priority
    }

    # Add and sort activities
    activities = schedule_data.get(date_str, [])
    activities.append(new_activity)
    activities.sort(key=lambda x: x['start_time'])
    schedule_data[date_str] = activities
    
    # Save updated schedule
    save_data(schedule_data)
    print("Activity added successfully.")
# =====================================================================================

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

    def cot(self, prompt, max_tokens, temp, model):
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=prompt,
            temperature=temp,
            max_tokens=max_tokens,
        )
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

    def gpt(self, prompt, max_tokens, temp, model, verbose=False):
        # tools = [
        #     {
        #         "type": "function",
        #         "function": {
        #             "name": "sys_new_activity",
        #             "description": "System function to add a new activity and refresh schedule",
        #             "parameters": {
        #                 "type": "object",
        #                 "properties": {
        #                     "date_str": {
        #                         "type": "string",
        #                         "description": "Date in 'mm/dd/yyyy' format",
        #                     },
        #                     "start_time": {
        #                         "type": "string", 
        #                         "description": "Start time in 'HH:MM' 24-hour format"},
        #                     "end_time": {
        #                         "type": "string", 
        #                         "description": "End time in 'HH:MM' 24-hour format"},
        #                     "title": {
        #                         "type": "string", 
        #                         "description": "Title of the activity"},
        #                     "Description": {
        #                         "type": "string", 
        #                         "description": "Description of the activity"},
        #                     "priority": {
        #                         "type": "string", 
        #                         "enum": ["0", "1", "2", "3", "4", "5"],
        #                         "description": "Priority of the activity (0-5), 5 is highest"},
        #                 },
        #                 "required": ["date_str", "start_time", "end_time", "title", "Description", "priority"],
        #             },
        #         },   
        #     }
        # ]

        response = self.openai_client.chat.completions.create(
            model=model,
            messages=prompt,
            temperature=temp,
            max_tokens=max_tokens,
            # tools=tools,
            # tool_choice="auto"
        )

        if verbose:
            print(response.choices[0].message)

        # for tool_call in response.choices[0].message.tool_calls:
        #     args = json.loads(tool_call.function.arguments)
        #     sys_new_activity(args['date_str'], args['start_time'], args['end_time'], args['title'], args['Description'], int(args['priority']))

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
        # Find the data to change
        # Return the json data of that data
        # Read the json data and make changes
        # Apply changes to original json


        # history is a json file describing the current calender
        # text_input is user's text input for scheduling
        # image_input is user's image input for scheduling

        # rag_prompt = [
        #     {"role": "system", "content": "You are a helpful assistant to analyze user's intention and call functions."},
        #     {"role": "user", "content": f"Please analyze if user wants to add an event: {text_input}."},
        # ]
        
        current_date = datetime.now().date() 

        # Refine the prompt so that agent would only make function call.
        # rag_prompt = [
        #     {"role": "system", "content": "You are a helpful assistant to analyze user's intention and call functions based on the current schdule."},
        #     {"role": "user", "content": f"Add the event using function call based on user's query: {text_input}. Today is {current_date}"},
        # ]

        rag_prompt_data = [
            {"role": "system", "content": "You are a helpful assistant to analyze user's intention and decide which data's schdule need to change."},
            {"role": "user", "content": f"What data's schdule need to change based on user's query: {text_input}. Today is {current_date}. The return format should be 'MM/DD/YYYY', if multiple data need to change, separate the data by ';' , ONLY RETURN THE DATA."},
        ]

        # history is necessary
        if history:
            rag_prompt_data.append({"role": "user", "content": f"The current schdule is {history}"})
        

        if image_input:
            image_prompt = self.convert_image_to_base64(image_input)
            rag_prompt_data.append({"role": "user", "content": image_prompt})

        response = self.gpt(rag_prompt_data, 256, 0.3, 'gpt-4o-mini')

        filter_dates = response.split(";")
        filtered_data = {date: activities for date, activities in history.items() if date in filter_dates}
        # print(filtered_data)

        rag_prompt_change = [
            {"role": "system", "content": "You are a helpful assistant to analyze user's intention and change the schdule. You need to return the schdule as a json format which is the same as the schdule I give you"},
            {"role": "user", "content": f"Change the schdule based on user's query: {text_input}. The schdule need to be changed are {filtered_data}.The return result should ONLY be a json object that has the same format as this one without addtional content."},
        ]

        # response_change = self.gpt(rag_prompt_change, 1024, 0.3, 'gpt-4o-mini')
        max_retries = 3
        retries = 0
        while retries < max_retries:
            response_change = self.gpt(rag_prompt_change, 1024, 0.3, 'gpt-4o-mini')
            try:
                changed_data = json.loads(response_change)
                print("Valid JSON received.")
                print(changed_data)
                break
            except json.JSONDecodeError as e:
                changed_data = filtered_data
                print(f"Error parsing JSON (attempt {retries + 1}): {e}")
                print(response_change)
                retries += 1

        for date, activities in changed_data.items():
            history[date] = activities

        if image_input:
            cot_prompt = [
                {"role": "system", "content": "Please explain why you perform this action based on user's query."},
                {"role": "user", "content": f"User's query: {text_input}. Today is {current_date}."},
                {"role": "user", "content": image_prompt},
                {"role": "user", "content": f"The schdule need to be changed are {filtered_data}. Your changed schdule: {response_change}, please explain it."}
            ]
        else:
            cot_prompt = [
                {"role": "system", "content": "Please explain why you schedule the activity here based on user's query."},
                {"role": "user", "content": f"User's query: {text_input}. Today is {current_date}."},
                {"role": "user", "content": f"The schdule need to be changed are {filtered_data}. Your changed schdule: {response_change}, please explain it."}
            ]

        cot_response = self.cot(cot_prompt, 512, 0.3, 'gpt-4o-mini')

        return response, cot_response, history
        # return response, history

        
"""
两个场景，第一个是重复性的场景。
比如说每天早上8点吃早餐，根据n gram，ai就能直接schedule这个task here
但是如果某天早上我要traveling，ai需要动态调整，然后给出解释为啥和平时不一样

第二个场景，就是 一天10个会议，然后我们prompt LLM要注意mental health
结果LLM删除了2个重要会议，结果会议没参加，这显然不对。这个时候ai就应该如果删除重要的事情前query user

"""
