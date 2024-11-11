import streamlit as st
import json
import os
from datetime import datetime, date

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

# Display schedule function
def display_schedule(schedule_data, selected_date_str):
    st.header(f"Schedule for {selected_date_str}")
    # Add button next to schedule title
    if st.button("Add Activity"):
        st.session_state['adding_activity'] = True

    activities = schedule_data.get(selected_date_str, [])
    if activities:
        # Sort activities by start time
        activities.sort(key=lambda x: x['start_time'])
        for idx, activity in enumerate(activities):
            with st.expander(f"{activity['start_time']} - {activity['end_time']}: {activity['title']}", expanded=False):
                st.write(f"**Priority:** {activity['priority']}")
                st.write(f"**Description:** {activity['description']}")
                col1, col2 = st.columns(2)
                if col1.button("Modify", key=f"modify_{selected_date_str}_{idx}"):
                    st.session_state['modifying_activity_index'] = idx
                if col2.button("Delete", key=f"delete_{selected_date_str}_{idx}"):
                    # Delete the activity
                    activities.pop(idx)
                    schedule_data[selected_date_str] = activities
                    save_data(schedule_data)
                    st.success("Activity deleted successfully.")
                    st.rerun()
    else:
        st.info("No activities scheduled for this date.")

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

# Main function
def main():
    # Initialize session state variables
    if 'adding_activity' not in st.session_state:
        st.session_state['adding_activity'] = False
    if 'modifying_activity_index' not in st.session_state:
        st.session_state['modifying_activity_index'] = None

    # Load schedule data
    schedule_data = load_data()
    # Application title
    st.title("Schedule Application")
    # Date selection
    selected_date_str = select_date()
    # Display schedule
    display_schedule(schedule_data, selected_date_str)

    # If adding_activity is True, show the add activity form
    if st.session_state['adding_activity']:
        print("submit new activity:")
        submit_activity(schedule_data, selected_date_str)
    # If modifying_activity_index is not None, show the modify activity form
    elif st.session_state['modifying_activity_index'] is not None:
        print("modify activity:")
        modify_activity(schedule_data, selected_date_str)

if __name__ == "__main__":
    main()
