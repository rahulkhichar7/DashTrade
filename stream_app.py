import streamlit as st
import datetime
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import ChatPromptTemplate
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from langchain import hub

llm = ChatGroq(
    api_key="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", 
    model_name="llama-3.3-70b-versatile", 
    temperature=0.7
)

# -----------------------------
# Tools
# -----------------------------
duckduckgo_tool = DuckDuckGoSearchRun()
tools = [
    Tool(
        name="DuckDuckGo Search",
        func=duckduckgo_tool.run,
        description="Use this for real-time queries like stock prices or news."
    )
]


prompt = hub.pull("hwchase17/react-chat")


LOG_FILE = "agent_log.txt"
def log_event(user_query, tool_name, tool_output, llm_response=None):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("----------\n")
        f.write(f"Timestamp: {datetime.datetime.now()}\n")
        f.write(f"User Query: {user_query}\n")
        f.write(f"Tool Used: {tool_name}\n")
        f.write(f"Tool Output:\n{tool_output}\n")
        if llm_response:
            f.write(f"LLM Response:\n{llm_response}\n")
        f.write("----------\n\n")


# --- STREAMLIT UI INTEGRATION ---

st.set_page_config(page_title="Dash Trade", page_icon="")
st.title("Dash Trade")

# Initialize session state for memory and messages
if 'memory' not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )

if 'messages' not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    memory=st.session_state.memory
)

# Main agent interaction logic
def run_agent(query: str):
    try:
        # Use invoke for the agent executor
        response = agent_executor.invoke({"input": query})
        output = response.get('output', "No output found.")
        
        # Log the successful interaction
        log_event(user_query=query, tool_name="DuckDuckGo + Agent",
                  tool_output="Fetched results if needed",
                  llm_response=output)
        return output
    except Exception as e:
        error_message = f"An error occurred: {e}"
        log_event(user_query=query, tool_name="ERROR", tool_output=str(e))
        return error_message

# Accept user input
if user_prompt := st.chat_input("What would you like to ask?"):

    st.session_state.messages.append({"role": "user", "content": user_prompt})

    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = run_agent(user_prompt)
            st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})