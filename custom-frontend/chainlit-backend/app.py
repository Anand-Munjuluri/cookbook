from fastapi.responses import JSONResponse
from chainlit.auth import create_jwt
from chainlit.server import app
import chainlit as cl

# Mock responses
mock_responses = [
    {"choices": [{"delta": {"content": "Mock response 1"}}]},
    {"choices": [{"delta": {"content": "Mock response 2"}}]},
    # Add more mock responses as needed
]

# Index to keep track of the current mock response
mock_response_index = 0

# Mock function to simulate the behavior of OpenAI API
async def mock_openai_chat_completions(messages, stream=True):
    global mock_response_index
    response = mock_responses[mock_response_index]
    mock_response_index = (mock_response_index + 1) % len(mock_responses)

    # Define settings within the mock function
    settings = {
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 500,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
    }

    return [response]

@app.get("/custom-auth")
async def custom_auth():
    # Verify the user's identity with custom logic.
    token = create_jwt(cl.User(identifier="Test User"))
    return JSONResponse({"token": token})

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set(
        "message_history",
        [{"role": "system", "content": "You are a helpful assistant."}],
    )
    await cl.Message(content="Connected to Chainlit!").send()

@cl.on_message
async def on_message(message: cl.Message):
    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": message.content})

    msg = cl.Message(content="")
    await msg.send()

    # Use the mock_openai_chat_completions function instead of making a real API call
    responses = await mock_openai_chat_completions(messages=message_history, stream=True)

    for part in responses:
        if token := part.get("choices", [{}])[0].get("delta", {}).get("content", ""):
            await msg.stream_token(token)

    message_history.append({"role": "assistant", "content": msg.content})
    await msg.update()
