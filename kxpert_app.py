import streamlit as st
import openai
from google.cloud import bigquery
import base64

# OpenAI and Google BigQuery credentials
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
VALID_PASSWORDS = st.secrets["VALID_PASSWORDS"].split(",")

openai.api_key = OPENAI_API_KEY
PROJECT_ID = st.secrets["BIGQUERY_PROJECT_ID"]
DATASET_ID = st.secrets["BIGQUERY_DATASET_ID"]
TABLE_ID = st.secrets["BIGQUERY_TABLE_ID"]

# Function to load data from BigQuery
def load_data_from_bigquery(PROJECT_ID, DATASET_ID, TABLE_ID):
    try:
        client = bigquery.Client()
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
        query = f"SELECT string_field_0 AS category, string_field_1 AS content FROM `{table_ref}`"
        query_job = client.query(query)
        results = query_job.result()
        return [{"category": row["category"], "content": row["content"] or "No content available"} for row in results]
    except Exception as e:
        return f"Error loading data from BigQuery: {e}"

# Function to query GPT model
def query_gpt(prompt, table_data):
    try:
        # Prepare relevant table information for the query
        table_context = "\n".join(
            [f"Category: {entry['category']}, Content: {entry['content']}" for entry in table_data]
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"{table_context}\n\n{prompt}"}
            ]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        return f"Error: {e}"

# Add background
def add_bg_from_local(image_file):
    with open(image_file, "rb") as file:
        data = file.read()
        encoded_image = base64.b64encode(data).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/jpg;base64,{encoded_image}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

add_bg_from_local("vecteezy_teal-background-high-quality_30679827.jpg")

def add_circle_image_to_bg(image_path):
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
        <style>
        .title-wrapper {{
            position: relative;
            margin-bottom: 50px;
        }}
        .circle-image {{
            position: absolute;
            top: 3px;  /* Adjust vertical position */
            left: calc(100% - 292px);  /* Position it near the end of the title */
            transform: translateX(-50%);
            border-radius: 100%;
            width: 40px;
            height: 40px;
        }}
        </style>
        <div class="title-wrapper">
            <h1 style="margin: 0;">My Knowledge Xpert</h1>
            <img class="circle-image" src="data:image/png;base64,{encoded_image}" />
        </div>
        """,
        unsafe_allow_html=True
    )
add_circle_image_to_bg("Ke image.jfif")

    # Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'uploaded_content' not in st.session_state:
    st.session_state.uploaded_content = []
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'user_query' not in st.session_state:
    st.session_state.user_query = ""

# Login system
if not st.session_state.logged_in:
    st.markdown("### Login")
    password = st.text_input(
        "Enter the password:",
        type="password",
        key="password_input"
    )

    if password and st.session_state.get("password_input") in VALID_PASSWORDS:
        st.session_state.logged_in = True
        st.success("Access granted! You can now use the chat.")
        st.experimental_rerun()
    elif password:
        st.error("Access denied! Incorrect password.")

if st.session_state.logged_in:
    # Load BigQuery data
    if not st.session_state.uploaded_content:
        if st.button("Connect to Database"):
            with st.spinner("Loading data..."):
                bigquery_data = load_data_from_bigquery(PROJECT_ID, DATASET_ID, TABLE_ID)
                if isinstance(bigquery_data, list):  # Ensure data was loaded successfully
                    st.session_state.uploaded_content = bigquery_data
                    st.success("Data loaded successfully!")
                else:
                    st.error("Failed to load data. Please check your BigQuery configuration.")
            st.experimental_rerun()

    # Chat interface
    if st.session_state.uploaded_content:
        # Display conversation history
        for exchange in st.session_state.conversation_history:
            # User query (right-aligned)
            st.markdown(
                f"""
                <div style='text-align: right; font-style: italic; font-size: 18px; padding: 10px 0;'>
                    <b>Q:   </b> {exchange['query']}
                </div>
                """,
                unsafe_allow_html=True
            )
            # AI response (left-aligned with spacing and black color)
            st.markdown(
                f"""
                <div style='text-align: left; color: #FBFBFB; font-size: 18px; padding: 10px 0;'>
                    <b><i>Response</i></b>: {exchange['response']}
                </div>
                """,
                unsafe_allow_html=True
            )

        # Process query when user submits
        def process_query():
            if st.session_state.user_query.strip():
             
                # Generate the response
                response = query_gpt(st.session_state.user_query, st.session_state.uploaded_content)
                # Append to conversation history
                st.session_state.conversation_history.append(
                    {"query": st.session_state.user_query, "response": response}
                )
                # Clear the input field
                st.session_state.user_query = ""

        # User query input
        st.text_input(
            "Ask?",
            value=st.session_state.user_query,
            key="user_query",
            on_change=process_query
        )

        # Clear conversation
        if st.button("Clear Conversation"):
            st.session_state.conversation_history = []
            st.experimental_rerun()
