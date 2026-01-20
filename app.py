import asyncio
import os
import base64
import time
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
from agentbrowser.browser.manager import BrowserManager
from agentbrowser.agent.logic import Agent
from google.genai import types

# Load environment variables
load_dotenv()

# Page Config
st.set_page_config(
    page_title="AgentBrowser (Gemini 2.5)",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS similar to Anthropic's demo
st.markdown("""
<style>
    .stChatInputContainer {
        position: sticky;
        bottom: 0;
        background: white;
        z-index: 999;
        padding-bottom: 20px;
    }
    .element-container img {
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "history" not in st.session_state:
        st.session_state.history = [] # For Gemini API
    
    if "browser_manager" not in st.session_state:
        st.session_state.browser_manager = None
        
    if "agent" not in st.session_state:
        st.session_state.agent = None

    if "last_screenshot" not in st.session_state:
        st.session_state.last_screenshot = None

async def get_agent_browser(api_key):
    """Lazy init of browser and agent."""
    if st.session_state.browser_manager is None:
        st.session_state.browser_manager = BrowserManager(headless=False, api_key=api_key)
        await st.session_state.browser_manager.start()
        # Initial navigation
        await st.session_state.browser_manager.navigate("https://www.google.com")
        
    if st.session_state.agent is None:
        st.session_state.agent = Agent(api_key=api_key)
        
    return st.session_state.agent, st.session_state.browser_manager

def render_message(role, content, image_data=None):
    with st.chat_message(role):
        st.markdown(content)
        if image_data:
            st.image(image_data, use_container_width=True)

async def run_interaction(user_prompt):
    api_key = st.session_state.get("api_key") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("API Key not found!")
        return

    agent, browser = await get_agent_browser(api_key)
    
    # 1. Capture initial state/screenshot for this turn
    if st.session_state.last_screenshot is None:
        st.session_state.last_screenshot = await browser.capture_screenshot()
    
    # Update Gemini History
    # We always send the LATEST screenshot + User Prompt
    st.session_state.history.append(
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=user_prompt),
                types.Part.from_bytes(data=st.session_state.last_screenshot, mime_type="image/jpeg")
            ]
        )
    )
    
    # Display User Message
    st.session_state.messages.append({"role": "user", "content": user_prompt, "image": st.session_state.last_screenshot})
    render_message("user", user_prompt, st.session_state.last_screenshot)
    
    # --- Agent Loop (Reasoning + Acting) ---
    # In Streamlit, we might want to limit steps per interaction or let it run until "task_completed"
    # For better UX, let's do a loop but yield updates
    
    with st.chat_message("assistant"):
        status_container = st.status("Agent thinking...", expanded=True)
        
        while True:
            try:
                # THINK
                status_container.write("🧠 Reasoning...")
                response = await agent.think(st.session_state.history)
                
                if not response.candidates:
                     status_container.error("Agent returned no content.")
                     break
                     
                candidate = response.candidates[0]
                agent_content = candidate.content
                st.session_state.history.append(agent_content)
                
                # Show Thoughts
                thought_text = ""
                if agent_content.parts:
                    for p in agent_content.parts:
                        if p.text:
                            thought_text += p.text + "\n"
                
                if thought_text:
                    status_container.write(f"💭 {thought_text}")

                # Check Tools
                tool_calls = [part.function_call for part in agent_content.parts if part.function_call]
                
                if not tool_calls:
                    status_container.warning("No tools called. Waiting for user input.")
                    break
                
                task_done = False
                
                # EXECUTE TOOLS
                for call in tool_calls:
                    tool_name = call.name
                    tool_args = {k:v for k,v in call.args.items()}
                    
                    status_container.write(f"🛠️ **{tool_name}**: `{tool_args}`")
                    
                    result_text = ""
                    
                    if tool_name == "task_completed":
                        result = tool_args.get('result', '')
                        st.success(f"Task Completed: {result}")
                        result_text = f"Task Completed: {result}"
                        task_done = True
                        
                    elif tool_name == "ask_user":
                        question = tool_args.get('question', '')
                        st.warning(f"Agent asks: {question}")
                        result_text = "Waiting for user answer..." # In a real app we'd pause here
                        task_done = True # Stop loop to let user reply
                        
                    elif tool_name == "browser_action":
                        result_text = await browser.execute_action(**tool_args)
                        status_container.code(result_text)
                    
                    else:
                        result_text = f"Unknown tool: {tool_name}"

                    # CAPTURE NEW STATE
                    status_container.write("📸 Capturing state...")
                    await asyncio.sleep(1) # Wait for UI
                    new_screenshot = await browser.capture_screenshot()
                    st.session_state.last_screenshot = new_screenshot
                    
                    # Add to history
                    st.session_state.history.append(
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_function_response(
                                    name=tool_name,
                                    response={"result": result_text}
                                ),
                                types.Part.from_bytes(data=new_screenshot, mime_type="image/jpeg")
                            ]
                        )
                    )
                    
                    # Show Screenshot update in the stream
                    st.image(new_screenshot, caption=f"State after {tool_name}", width=400)

                    if task_done:
                        break
            
                if task_done:
                    status_container.update(label="Task Finished", state="complete", expanded=False)
                    break
                    
            except Exception as e:
                status_container.error(f"Error: {e}")
                break

def main():
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        st.title("🤖 Configuration")
        api_key = st.text_input("Gemini API Key", value=os.getenv("GEMINI_API_KEY", ""), type="password")
        if api_key:
            st.session_state.api_key = api_key
            
        st.divider()
        if st.button("Reset Session"):
            st.session_state.messages = []
            st.session_state.history = []
            st.rerun()

    # Main Chat
    st.title("🌐 AgentBrowser Interface")
    
    # Render History
    for msg in st.session_state.messages:
        render_message(msg["role"], msg["content"], msg.get("image"))

    # Chat Input
    if prompt := st.chat_input("What should I do?"):
        if not st.session_state.get("api_key"):
            st.error("Please provide an API Key.")
            return

        # Run async loop
        asyncio.run(run_interaction(prompt))
        st.rerun()

if __name__ == "__main__":
    main()
