import streamlit as st
import os
from datetime import datetime
from groq import Groq

# Set up Streamlit UI
st.set_page_config(page_title="Groq Chatbot", page_icon="🤖", layout="wide")

st.title("🤖 Groq-Powered Chatbot with Tool Calling")

# Retrieve API Key securely
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("Please set the Groq API key in environment variables or Streamlit secrets!")
    st.stop()

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# Define system instructions
SYSTEM_PROMPT = """
You are a specialized AI assistant that can perform calculations and retrieve the current date and time using function calls.

Capabilities:
1. **Mathematical Calculations**: You can add, subtract, multiply, or divide numbers when requested.
   - Supported operations: `"add"`, `"subtract"`, `"multiply"`, `"divide"`.
   - You will return an error if division by zero is attempted or if invalid inputs are provided.
   - The function expects a JSON format: `{"operation": "add", "numbers": [4, 5, 6]}`.

2. **Fetching the Current Time**: You can provide the current date and time in `"YYYY-MM-DD HH:MM:SS"` format.

Rules:
- If the user asks for any **calculation**, invoke the `calculate` function.
- If the user asks for the **current time**, invoke the `get_time` function.
- If the user's question is unrelated to calculations or time, inform them that you can only perform these tasks.

When you need to call a function, respond in the following format:

**For calculations:**
[CALL:calculate] {"operation": "add", "numbers": [10, 20, 30]}
**For getting the time:**
[CALL:get_time]


Do **not** answer queries unrelated to calculations or time.

"""

# Define tool functions
def get_time():
    """Fetches the current date and time"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def calculate(operation, numbers):
    """Performs basic calculations on a list of numbers."""
    if not isinstance(numbers, list) or len(numbers) < 2:
        return "Error: Please provide a list of at least two numbers."

    try:
        if operation == "add":
            return sum(numbers)
        elif operation == "subtract":
            return numbers[0] - sum(numbers[1:])
        elif operation == "multiply":
            result = 1
            for num in numbers:
                result *= num
            return result
        elif operation == "divide":
            result = numbers[0]
            for num in numbers[1:]:
                if num == 0:
                    return "Error: Division by zero is not allowed."
                result /= num
            return result
        else:
            return "Error: Unsupported operation. Use 'add', 'subtract', 'multiply', or 'divide'."
    except Exception as e:
        return f"Error: {str(e)}"

# Streamlit Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! How can I assist you today?"}]

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
user_input = st.chat_input("Ask me anything...")
if user_input:
    # Append user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Call Groq API
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *st.session_state.messages,
                ],
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "get_time",
                            "description": "Fetch the current date and time",
                            "parameters": {}
                        },
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "calculate",
                            "description": "Perform mathematical calculations",
                            "parameters": {
                                "operation": {"type": "string", "description": "The operation to perform (add, subtract, multiply, divide)"},
                                "numbers": {"type": "array", "items": {"type": "number"}, "description": "A list of numbers to process"},
                            },
                        },
                    },
                ],
            )

            assistant_reply = response.choices[0].message.content

            # Handle tool calling if detected
            # Handle tool calling if detected
            if response.choices[0].message.tool_calls:  # ✅ Check if tool_calls exists
                for tool_call in response.choices[0].message.tool_calls:
                    tool_name = tool_call.function.name
                    print(tool_call)
                    tool_params = tool_call.function.get.parameters

                    if tool_name == "get_time":
                        tool_result = get_time()
                    elif tool_name == "calculate":
                        tool_result = calculate(
                            tool_params.get("operation"),
                            tool_params.get("numbers"),
                        )
                    else:
                        tool_result = "Unknown tool called."

                    assistant_reply += f"\n\n**Tool Result:** {tool_result}"


            st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
            st.markdown(assistant_reply)
