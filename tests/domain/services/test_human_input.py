import asyncio
import pytest

from bonsai_sensei.domain.services.human_input import (
    ConfirmationResult,
    create_ask_confirmation,
    create_ask_human,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_send_question_to_user(ask_human, sent_messages, tool_context):
    await ask_human("What species is it?", tool_context=tool_context)

    assert sent_messages == [("user-123", "What species is it?")], \
        "ask_human should send the question to the user"


@pytest.mark.asyncio
async def should_return_user_text_response(ask_human, tool_context):
    result = await ask_human("What species is it?", tool_context=tool_context)

    assert result == "Ficus retusa", "ask_human should return the user's text response"


@pytest.mark.asyncio
async def should_timeout_when_user_does_not_respond_to_question(pending_responses):
    async def send_without_response(user_id, text):
        pass

    ask = create_ask_human(send_without_response, pending_responses, timeout_seconds=0.01)

    with pytest.raises(asyncio.TimeoutError):
        await ask("What species is it?", tool_context=MockToolContext(user_id="user-123"))


@pytest.mark.asyncio
async def should_send_confirmation_prompt_to_user(ask_confirmation, sent_confirmations, tool_context):
    await ask_confirmation("Delete Naruto?", tool_context=tool_context)

    assert sent_confirmations[0][:2] == ("user-123", "Delete Naruto?"), \
        "ask_confirmation should send the prompt and user_id to the user"


@pytest.mark.asyncio
async def should_include_confirmation_id_in_send_call(ask_confirmation, sent_confirmations, tool_context):
    await ask_confirmation("Delete Naruto?", tool_context=tool_context)

    assert sent_confirmations[0][2] is not None, \
        "ask_confirmation should include a confirmation_id in the send call"


@pytest.mark.asyncio
async def should_return_truthy_when_user_accepts(tool_context, pending_responses):
    async def send_and_accept(user_id, question, confirmation_id):
        pending_responses[user_id]["response"] = ConfirmationResult(accepted=True)
        pending_responses[user_id]["event"].set()

    ask = create_ask_confirmation(send_and_accept, pending_responses)
    result = await ask("Delete Naruto?", tool_context=tool_context)

    assert result, "ask_confirmation should return truthy when user accepts"


@pytest.mark.asyncio
async def should_return_falsy_when_user_cancels(tool_context, pending_responses):
    async def send_and_cancel(user_id, question, confirmation_id):
        pending_responses[user_id]["response"] = ConfirmationResult(accepted=False)
        pending_responses[user_id]["event"].set()

    ask = create_ask_confirmation(send_and_cancel, pending_responses)
    result = await ask("Delete Naruto?", tool_context=tool_context)

    assert not result, "ask_confirmation should return falsy when user cancels"


@pytest.mark.asyncio
async def should_propagate_cancellation_reason(tool_context, pending_responses):
    async def send_and_cancel_with_reason(user_id, question, confirmation_id):
        pending_responses[user_id]["response"] = ConfirmationResult(accepted=False, reason="wrong bonsai")
        pending_responses[user_id]["event"].set()

    ask = create_ask_confirmation(send_and_cancel_with_reason, pending_responses)
    result = await ask("Delete Naruto?", tool_context=tool_context)

    assert result.reason == "wrong bonsai", \
        "ask_confirmation should propagate the cancellation reason"


@pytest.mark.asyncio
async def should_timeout_when_user_does_not_respond_to_confirmation(pending_responses):
    async def send_without_response(user_id, text, confirmation_id):
        pass

    ask = create_ask_confirmation(send_without_response, pending_responses, timeout_seconds=0.01)

    with pytest.raises(asyncio.TimeoutError):
        await ask("Delete Naruto?", tool_context=MockToolContext(user_id="user-123"))


@pytest.fixture
def pending_responses():
    return {}


@pytest.fixture
def sent_messages():
    return []


@pytest.fixture
def sent_confirmations():
    return []


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def ask_human(sent_messages, pending_responses):
    async def send_message(user_id, text):
        sent_messages.append((user_id, text))
        pending_responses[user_id]["response"] = "Ficus retusa"
        pending_responses[user_id]["event"].set()

    return create_ask_human(send_message, pending_responses)


@pytest.fixture
def ask_confirmation(sent_confirmations, pending_responses):
    async def send_confirmation(user_id, question, confirmation_id):
        sent_confirmations.append((user_id, question, confirmation_id))
        pending_responses[user_id]["response"] = ConfirmationResult(accepted=True)
        pending_responses[user_id]["event"].set()

    return create_ask_confirmation(send_confirmation, pending_responses)
