import streamlit as st
import json
import os
from datetime import datetime, date
from agent import Agent
from PIL import Image

# Data file path
DATA_FILE = 'schedule_data.json'

# Initialize if data file does not exist
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({}, f)

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

def display_schedule(schedule_data, selected_date_str):
    st.header(f"Schedule for {selected_date_str}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Add Activity Manually"):
            st.session_state['adding_activity'] = True
    with col2:
        if st.button("Add Activity with AI Assistant"):
            st.session_state['using_ai_assistant'] = True
    
    activities = schedule_data.get(selected_date_str, [])
    if activities:
        activities.sort(key=lambda x: x['start_time'])
        for idx, activity in enumerate(activities):
            with st.expander(f"{activity['start_time']} - {activity['end_time']}: {activity['title']}", expanded=False):
                st.write(f"**Priority:** {activity['priority']}")
                st.write(f"**Description:** {activity['description']}")
                col1, col2 = st.columns(2)
                if col1.button("Modify", key=f"modify_{selected_date_str}_{idx}"):
                    st.session_state['modifying_activity_index'] = idx
                if col2.button("Delete", key=f"delete_{selected_date_str}_{idx}"):
                    activities.pop(idx)
                    schedule_data[selected_date_str] = activities
                    save_data(schedule_data)
                    st.success("Activity deleted successfully.")
                    st.rerun()
    else:
        st.info("No activities scheduled for this date.")

# Add new activity function (UI)
def submit_activity(schedule_data, selected_date_str):
    activities = schedule_data.get(selected_date_str, [])
    st.subheader("Add New Activity")
    with st.form(key='add_activity_form'):
        # Row for Start Time
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        # Start Time Inputs
        start_hour = col1.text_input("Start Hour", max_chars=2, key='start_hour')
        start_minute = col2.text_input("Start Minute", max_chars=2, key='start_minute')
        
        # End Time Inputs
        end_hour = col3.text_input("End Hour", max_chars=2, key='end_hour')
        end_minute = col4.text_input("End Minute", max_chars=2, key='end_minute')

        activity_title = st.text_input("Title")
        activity_description = st.text_area("Description")
        activity_priority = st.slider("Priority (0-5, 5 is highest)", min_value=0, max_value=5, value=0)

        # Submit and Cancel buttons in one row
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("Add Activity")
        with col2:
            cancel = st.form_submit_button("Cancel")

        if submit:
            try:
                start_time = f"{int(start_hour):02d}:{int(start_minute):02d}"
                end_time = f"{int(end_hour):02d}:{int(end_minute):02d}"
                # Check if start time is before end time
                if datetime.strptime(start_time, '%H:%M') >= datetime.strptime(end_time, '%H:%M'):
                    st.error("Start time must be earlier than end time.")
                elif activity_title.strip() == "":
                    st.error("Title cannot be empty.")
                else:
                    new_activity = {
                        'start_time': start_time,
                        'end_time': end_time,
                        'title': activity_title,
                        'description': activity_description,
                        'priority': activity_priority
                    }
                    activities.append(new_activity)
                    # Reorder activities based on starting time
                    activities.sort(key=lambda x: x['start_time'])
                    schedule_data[selected_date_str] = activities
                    save_data(schedule_data)
                    st.success("Activity added successfully.")
                    # Reset adding_activity flag
                    st.session_state['adding_activity'] = False
                    st.rerun()
            except ValueError:
                st.error("Please enter valid times (00-23 for hour and 00-59 for minutes).")

        if cancel:
            st.session_state['adding_activity'] = False
            st.rerun()


# Modify activity function
def modify_activity(schedule_data, selected_date_str):
    activities = schedule_data.get(selected_date_str, [])
    idx = st.session_state['modifying_activity_index']
    activity_to_modify = activities[idx]
    st.subheader("Modify Activity")
    with st.form(key='modify_activity_form'):
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        start_hour = col1.text_input("Start Hour", max_chars=2,
                                     value=activity_to_modify['start_time'].split(':')[0],
                                     key='mod_start_hour')
        start_minute = col2.text_input("Start Minute", max_chars=2,
                                       value=activity_to_modify['start_time'].split(':')[1],
                                       key='mod_start_minute')
        end_hour = col3.text_input("End Hour", max_chars=2,
                                   value=activity_to_modify['end_time'].split(':')[0],
                                   key='mod_end_hour')
        end_minute = col4.text_input("End Minute", max_chars=2,
                                     value=activity_to_modify['end_time'].split(':')[1],
                                     key='mod_end_minute')

        new_title = st.text_input("Title", value=activity_to_modify['title'])
        new_description = st.text_area("Description", value=activity_to_modify['description'])
        new_priority = st.slider("Priority (0-5, 5 is highest)", min_value=0, max_value=5,
                                 value=int(activity_to_modify['priority']))
        col1, col2 = st.columns(2)
        with col1:
            modify_submit = st.form_submit_button("Update Activity")
        with col2:
            cancel_submit = st.form_submit_button("Cancel")
        if modify_submit:
            try:
                start_time = f"{int(start_hour):02d}:{int(start_minute):02d}"
                end_time = f"{int(end_hour):02d}:{int(end_minute):02d}"
                if datetime.strptime(start_time, '%H:%M') >= datetime.strptime(end_time, '%H:%M'):
                    st.error("Start time must be earlier than end time.")
                elif new_title.strip() == "":
                    st.error("Title cannot be empty.")
                else:
                    activities[idx] = {
                        'start_time': start_time,
                        'end_time': end_time,
                        'title': new_title,
                        'description': new_description,
                        'priority': new_priority
                    }
                    # Reorder activities based on starting time
                    activities.sort(key=lambda x: x['start_time'])
                    schedule_data[selected_date_str] = activities
                    save_data(schedule_data)
                    st.success("Activity updated successfully.")
                    st.session_state['modifying_activity_index'] = None
                    st.rerun()
            except ValueError:
                st.error("Please enter valid times (00-23 for hour and 00-59 for minutes).")
        if cancel_submit:
            st.session_state['modifying_activity_index'] = None
            st.rerun()

# Add new activity with AI Assistant
def ai_assistant_add_activity(agent, schedule_data, selected_date_str):
    st.subheader("AI Schedule Assistant")
    
    # Text input for natural language command
    text_prompt = st.text_area("Describe the activity you want to add", 
                              placeholder="e.g., 'Schedule a team meeting tomorrow from 2pm to 3pm with high priority'")
    
    # Image upload
    image_file = st.file_uploader("Upload an image (optional)", type=['png', 'jpg', 'jpeg'])
    image_input = None
    if image_file is not None:
        image_input = Image.open(image_file)
        st.image(image_input, caption="Uploaded Image")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Submit to AI"):
            if text_prompt:
                with st.spinner("AI is processing your request..."):
                    # Get current schedule for context
                    current_schedule = schedule_data.get(selected_date_str, [])
                    
                    # Call the AI agent
                    response, explanation = agent.query(current_schedule, text_prompt, image_input)
                    
                    # Display AI response and explanation
                    st.success("Activity added successfully!")
                    
                    st.write("**AI Response:**")
                    st.write(response)
                    
                    st.write("**AI Explanation:**")
                    st.write(explanation)
                    
                    # Only reset the state, don't rerun immediately
                    st.session_state['using_ai_assistant'] = False
            else:
                st.error("Please provide a description of the activity.")

    with col2:
        if st.button("Cancel"):
            st.session_state['using_ai_assistant'] = False
            st.rerun()

def main():
    # Initialize session state variables
    if 'adding_activity' not in st.session_state:
        st.session_state['adding_activity'] = False
    if 'modifying_activity_index' not in st.session_state:
        st.session_state['modifying_activity_index'] = None
    if 'using_ai_assistant' not in st.session_state:
        st.session_state['using_ai_assistant'] = False

    # Initialize OpenAI client and Agent
    try:
        from openai import OpenAI
        client = OpenAI(api_key='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')
        agent = Agent(client)
    except Exception as e:
        st.error(f"Error initializing AI agent: {str(e)}")
        agent = None

    # Load schedule data
    schedule_data = load_data()
    
    # Application title
    st.title("AI-Powered Schedule Application")
    
    # Date selection
    selected_date_str = select_date()
    
    # Display schedule
    display_schedule(schedule_data, selected_date_str)

    # Show appropriate form based on state
    if st.session_state['adding_activity']:
        submit_activity(schedule_data, selected_date_str)
    elif st.session_state['modifying_activity_index'] is not None:
        modify_activity(schedule_data, selected_date_str)
    elif st.session_state['using_ai_assistant']:
        if agent:
            ai_assistant_add_activity(agent, schedule_data, selected_date_str)
        else:
            st.error("AI Assistant is not available. Please check your OpenAI configuration.")

if __name__ == "__main__":
    main()
