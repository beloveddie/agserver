# routers/voice.py
import json, base64, asyncio, os
import websockets
from fastapi import APIRouter, Form, WebSocket, Request
from fastapi.websockets import WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from twilio.twiml.voice_response import VoiceResponse, Connect


from config import OPENAI_API_KEY, SYSTEM_MESSAGE, VOICE, LOG_EVENT_TYPES, SHOW_TIMING_MATH
from services.openai_service import initialize_session

from datetime import datetime
from config import db


router = APIRouter()

@router.get("/", response_class=JSONResponse)
async def index_page():
    return {"message": "Agserver is running!"}

@router.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request, From: str = Form(...)):
    global caller
    caller = From
    print(f"Incoming call from {From}")
    response = VoiceResponse()
    # response.say("Welcome, I'm Agserver, you're rural farming assistant. You can ask me for help with anythin regarding your farm.")
    # response.pause(length=1)
    # response.say("O.K. you can start talking!")

    host = request.url.hostname
    stream_url = f'wss://{host}/media-stream?caller={From}'

    connect = Connect()
    connect.stream(url=stream_url)
    response.append(connect)

    return HTMLResponse(content=str(response), media_type="application/xml")

@router.websocket("/media-stream")
@router.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
    print(f"🔗 Voice stream initiated by: {caller}")
    print("Client connected")
    await websocket.accept()

    session_log = {
    "caller": caller,
    "started_at": datetime.utcnow(),
    "escalated": False}


    exit_signal = {"stop": False}  # ✅ Shared flag for graceful shutdown

    async with websockets.connect(
        'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17',
        extra_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
    ) as openai_ws:
        await initialize_session(openai_ws)

        # Session state
        stream_sid = None
        latest_media_timestamp = 0
        last_assistant_item = None
        mark_queue = []
        response_start_timestamp_twilio = None

        async def receive_from_twilio():
            nonlocal stream_sid, latest_media_timestamp
            try:
                while not exit_signal["stop"]:
                    try:
                        message = await websocket.receive_text()
                        data = json.loads(message)

                        if data['event'] == 'media' and openai_ws.open:
                            latest_media_timestamp = int(data['media']['timestamp'])
                            await openai_ws.send(json.dumps({
                                "type": "input_audio_buffer.append",
                                "audio": data['media']['payload']
                            }))

                        elif data['event'] == 'start':
                            stream_sid = data['start']['streamSid']
                            print(f"📞 Incoming stream started: {stream_sid}")
                            latest_media_timestamp = 0
                            last_assistant_item = None

                        elif data['event'] == 'mark' and mark_queue:
                            mark_queue.pop(0)

                    except WebSocketDisconnect:
                        print("❌ WebSocket client disconnected during receive.")
                        break
                    except Exception as e:
                        print(f"⚠️ Error in receive loop: {e}")
                        break
            finally:
                if openai_ws.open:
                    await openai_ws.close()
                print("📴 receive_from_twilio finished cleanly.")

        async def send_to_twilio():
            nonlocal stream_sid, last_assistant_item, response_start_timestamp_twilio

            from services.escalation_service import check_if_escalation_needed, route_to_expert
            from services.twilio_service import send_sms_to_expert, send_sms_to_user
            from utils.language_utils import detect_language

            user_transcript = ""

            def get_escalation_confirmation(language: str, expert_name: str) -> str:
                if language == "Pidgin":
                    return f"I don send your question give {expert_name}. E go call or message you soon."
                elif language == "Igbo":
                    return f"A zịrila {expert_name} ozi gbasara ajụjụ gị. Ọ ga-akpọ gị ma ọ bụ zipu ozi n'oge na-adịghị anya."
                return f"Alright! I've sent your question to {expert_name}. They'll reach out to you soon."

            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)

                    if response.get("type") == "conversation.item.create":
                        content_blocks = response.get("item", {}).get("content", [])
                        for block in content_blocks:
                            if block.get("type") == "input_text":
                                user_transcript = block["text"]
                                session_log["user_transcript"] = user_transcript
                                print(f"🎙️ User said: {user_transcript}")

                    if response['type'] in LOG_EVENT_TYPES:
                        print(f"📥 Event: {response['type']}", response)

                    if response.get('type') == 'response.audio.delta' and 'delta' in response:
                        payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                        await websocket.send_json({
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {"payload": payload}
                        })

                        if response_start_timestamp_twilio is None:
                            response_start_timestamp_twilio = latest_media_timestamp
                        if response.get('item_id'):
                            last_assistant_item = response['item_id']
                        await send_mark(websocket, stream_sid)

                    if response.get('type') == 'input_audio_buffer.speech_started':
                        print("🔊 User speech interruption detected.")
                        if last_assistant_item:
                            await handle_speech_started_event()

                    if response.get('type') == 'response.done':
                        print("🧠 Parsing assistant response...")
                        initial_ai_reply = ""
                        try:
                            output = response.get("response", {}).get("output", [])
                            if output:
                                content_items = output[0].get("content", [])
                                for item in content_items:
                                    if item.get("type") == "audio":
                                        initial_ai_reply = item.get("transcript", "")
                                        break
                        except Exception as e:
                            print("⚠️ Failed to parse assistant response:", e)

                        print(f"🧠 Initial AI response: {initial_ai_reply}")

                        if check_if_escalation_needed(initial_ai_reply):
                            print("🚨 Escalation needed.")
                            user_language = detect_language(user_transcript)
                            expert = route_to_expert(user_transcript, user_language)

                            if expert:
                                print(f"👨🏾‍🌾 Notifying expert: {expert['name']}")

                                # ✅ Update session log with escalation metadata
                                session_log["escalated"] = True
                                session_log["language"] = user_language
                                session_log["expert"] = {
                                    "name": expert["name"],
                                    "phone": expert["phone"]
                                }

                                try:
                                    send_sms_to_expert(
                                        expert=expert,
                                        user_question=user_transcript,
                                        user_phone=caller,
                                        user_language=user_language
                                    )

                                    # Send SMS to user about expert routing
                                    user_sms_message = f"Thank you for your question. We've connected you with {expert['name']}, who will contact you shortly to help with your farming query."
                                    send_sms_to_user(caller, user_sms_message)

                                    confirmation_text = get_escalation_confirmation(user_language, expert["name"])
                                    
                                    # Update the final response that will be saved to DB
                                    final_response = f"{initial_ai_reply}\n\n{confirmation_text}"
                                    session_log["ai_response"] = final_response

                                    await openai_ws.send(json.dumps({
                                        "type": "conversation.item.create",
                                        "item": {
                                            "type": "message",
                                            "role": "assistant",
                                            "content": [{"type": "text", "text": confirmation_text}]
                                        }}))
                                    await openai_ws.send(json.dumps({"type": "response.create"}))
                                    print("✅ Confirmation message sent to user.")

                                    # 🕓 Wait for response.done after the AI finishes speaking
                                    import audioop

                                    # 🧠 Utility: Calculate audio duration (G711 µ-law @ 8000Hz = 8kbps = 1 byte per ms)
                                    def calculate_ulaw_duration_ms(decoded_audio: bytes) -> int:
                                        return len(decoded_audio)  # 1 byte ≈ 1 ms for G.711 u-law

                                    # ⏳ Track playback time
                                    total_playback_duration_ms = 0

                                    # 🕓 Wait for OpenAI to finish, while sending last bits to Twilio
                                    while True:
                                        try:
                                            openai_followup = await openai_ws.recv()
                                            parsed = json.loads(openai_followup)

                                            if parsed.get("type") == "response.audio.delta" and "delta" in parsed:
                                                raw_bytes = base64.b64decode(parsed['delta'])
                                                duration_ms = calculate_ulaw_duration_ms(raw_bytes)
                                                total_playback_duration_ms += duration_ms

                                                encoded_payload = base64.b64encode(raw_bytes).decode("utf-8")
                                                await websocket.send_json({
                                                    "event": "media",
                                                    "streamSid": stream_sid,
                                                    "media": {"payload": encoded_payload}
                                                })

                                            elif parsed.get("type") == "response.done":
                                                print(f"✅ Assistant finished speaking. Estimated playback: {total_playback_duration_ms}ms")
                                                break

                                        except Exception as e:
                                            print("⚠️ Error while streaming final audio to Twilio:", e)
                                            break

                                    # ⏱️ Convert to seconds and wait a bit more for safe playback buffer
                                    safe_wait_time = (total_playback_duration_ms / 1000) + 0.8  # 0.8s buffer
                                    print(f"⏳ Waiting {safe_wait_time:.2f}s to let Twilio finish playback...")
                                    await asyncio.sleep(safe_wait_time)

                                    # ✅ Log session playback & end time
                                    session_log["audio_playback_ms"] = total_playback_duration_ms
                                    session_log["ended_at"] = datetime.utcnow()

                                    # 🧠 Save to MongoDB (wrapped for production safety)
                                    try:
                                        db.calls.insert_one(session_log)
                                        print("📦 Session logged to MongoDB.")
                                    except Exception as e:
                                        print(f"⚠️ Failed to save session log: {e}")

                                    # ✅ Now gracefully shutdown
                                    exit_signal["stop"] = True
                                    await openai_ws.send(json.dumps({"type": "session.close"}))
                                    await websocket.close()
                                    print("🔒 Session closed and WebSocket disconnected.")
                                except Exception as e:
                                    print(f"⚠️ Error during escalation process: {e}")
                                    session_log["escalation_error"] = str(e)
                                    # Save the initial response if escalation fails
                                    session_log["ai_response"] = initial_ai_reply
                            else:
                                print("⚠️ No expert available for that language.")
                                session_log["escalation_error"] = "No expert available"
                                # Save the initial response if no expert is available
                                session_log["ai_response"] = initial_ai_reply
                        else:
                            print("✅ No escalation needed.")
                        # Save the session log regardless
                        try:
                            session_log["ai_response"] = initial_ai_reply
                            session_log["ended_at"] = datetime.utcnow()
                            db.calls.insert_one(session_log)
                            print("📦 Session logged to MongoDB.")
                        except Exception as e:
                            print(f"⚠️ Failed to save session log: {e}")

            except Exception as e:
                print(f"❌ Error in send_to_twilio: {e}")
                # Try to log the call even if there's an error
                try:
                    session_log["error"] = str(e)
                    session_log["ended_at"] = datetime.utcnow()
                    db.calls.insert_one(session_log)
                    print("📦 Session logged to MongoDB despite error.")
                except Exception as db_error:
                    print(f"⚠️ Failed to save error session log: {db_error}")

        async def handle_speech_started_event():
            nonlocal response_start_timestamp_twilio, last_assistant_item
            if mark_queue and response_start_timestamp_twilio is not None:
                elapsed = latest_media_timestamp - response_start_timestamp_twilio
                if last_assistant_item:
                    await openai_ws.send(json.dumps({
                        "type": "conversation.item.truncate",
                        "item_id": last_assistant_item,
                        "content_index": 0,
                        "audio_end_ms": elapsed
                    }))
                await websocket.send_json({"event": "clear", "streamSid": stream_sid})
                mark_queue.clear()
                last_assistant_item = None
                response_start_timestamp_twilio = None

        async def send_mark(connection, stream_sid):
            if stream_sid:
                await connection.send_json({
                    "event": "mark",
                    "streamSid": stream_sid,
                    "mark": {"name": "responsePart"}
                })
                mark_queue.append('responsePart')

        await asyncio.gather(receive_from_twilio(), send_to_twilio())