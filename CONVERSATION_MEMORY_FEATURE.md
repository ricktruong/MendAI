# 💬 Conversation Memory Feature

## Overview

The chat now remembers conversations! This feature adds persistent conversation history so the AI can maintain context across multiple interactions and even page refreshes.

## 🎯 Key Features

### 1. **Session-Based Memory**
- Each patient conversation gets a unique session ID
- Sessions are stored on the backend (in-memory)
- Session IDs are saved in browser localStorage for persistence

### 2. **Automatic Restoration**
- When you return to a patient's dashboard, the conversation history is automatically restored
- Works across page refreshes and browser sessions
- Seamlessly continues where you left off

### 3. **Context Window Management**
- Intelligently manages conversation history to fit within token limits
- Keeps most recent messages for immediate context
- Summarizes older messages to preserve memory
- Maximum 50 messages per session (configurable)

### 4. **Session Expiration**
- Sessions automatically expire after 24 hours of inactivity
- Expired sessions are automatically cleaned up
- Prevents memory bloat on the server

### 5. **Clear Conversation**
- New "Clear Conversation" button in the chat interface
- Allows users to start fresh conversations
- Completely removes session history from backend and browser

## 🏗️ Architecture

### Backend Components

#### 1. **ConversationManager** (`backend/engine/engine/services/conversation_manager.py`)
```python
class ConversationManager:
    - get_conversation_history(session_id) → List of messages
    - add_message(session_id, role, content) → Stores message
    - get_context_for_llm(session_id, max_tokens) → Optimized context
    - clear_session(session_id) → Clears history
    - cleanup_expired_sessions() → Removes old sessions
```

**Features:**
- In-memory storage (can be upgraded to Redis)
- Automatic history trimming
- Token-aware context management
- Session expiration handling

#### 2. **Updated Chat Endpoint** (`backend/engine/engine/api/v0/endpoints/chat.py`)
```python
@router.post("/chat")
async def chat(request: ChatRequest):
    # 1. Extract user message
    # 2. Add to conversation history
    # 3. Get optimized context for LLM
    # 4. Send to biomedical LLM
    # 5. Store AI response
    # 6. Return updated messages
```

#### 3. **New API Endpoints**

**Get Conversation History:**
```
GET /api/v0/chat/history/{session_id}
Returns: { session_id, messages, count }
```

**Clear Conversation:**
```
DELETE /api/v0/chat/history/{session_id}
Returns: { success, message }
```

**Get Statistics:**
```
GET /api/v0/chat/stats
Returns: { total_sessions, total_messages, avg_messages_per_session }
```

### Frontend Components

#### Updated PatientDashboardPage

**Session Persistence:**
```typescript
// Save session ID to localStorage
localStorage.setItem(`chat_session_${patientId}`, sessionId);

// Restore on page load
const savedSessionId = localStorage.getItem(`chat_session_${patientId}`);
restoreConversationHistory(savedSessionId);
```

**Clear Conversation Button:**
- Red button in chat header
- Disabled when no conversation exists
- Confirms before clearing
- Removes session from backend and localStorage

## 📊 How It Works

### Message Flow:

```
1. User sends message
   ↓
2. Frontend → Backend Engine
   ↓
3. Engine adds message to ConversationManager
   ↓
4. Engine gets optimized conversation context
   ↓
5. Engine → Biomedical LLM (with full context)
   ↓
6. LLM generates response (with memory of past conversation)
   ↓
7. Engine stores AI response in ConversationManager
   ↓
8. Frontend displays response
   ↓
9. Session ID saved to localStorage
```

### Page Refresh:

```
1. User refreshes page
   ↓
2. Frontend checks localStorage for session_id
   ↓
3. If found: GET /api/v0/chat/history/{session_id}
   ↓
4. Backend returns conversation history
   ↓
5. Frontend displays restored messages
   ↓
6. User continues conversation seamlessly
```

## 🔧 Configuration

### Backend Settings (adjustable in `conversation_manager.py`):

```python
ConversationManager(
    max_history_per_session=50,  # Max messages to store
    session_ttl_hours=24         # Hours before expiration
)
```

### Context Window Settings:

```python
get_context_for_llm(
    session_id=session_id,
    max_tokens=2000  # Adjust based on LLM limits
)
```

## 💡 Smart Context Management

The system intelligently manages conversation context:

### Recent Conversation (< 10 messages):
- Returns all messages

### Medium Conversation (10-30 messages):
- Returns last 10 messages

### Long Conversation (> 30 messages):
- Summarizes older messages
- Keeps last 5 messages verbatim
- Total stays under token limit

## 🎨 User Experience

### What Users See:

1. **First Visit:**
   - Chat starts with greeting message
   - Session ID generated and saved

2. **During Conversation:**
   - AI remembers all previous questions
   - Responses build on earlier context
   - "Clear Conversation" button available

3. **Page Refresh:**
   - All messages automatically restored
   - Conversation continues seamlessly
   - No data loss

4. **Clear Conversation:**
   - Confirmation dialog appears
   - Chat resets to initial greeting
   - Fresh start with new session

## 🔒 Privacy & Security

- **In-Memory Storage:** Sessions stored in RAM, not disk
- **Auto-Expiration:** 24-hour automatic cleanup
- **User Control:** Users can clear conversations anytime
- **Per-Patient Sessions:** Each patient has separate conversation
- **No Cross-Patient Data:** Sessions isolated by patient ID

## 🚀 Future Enhancements

### Potential Upgrades:

1. **Redis Storage:**
   ```python
   # Replace in-memory dict with Redis
   redis_client = redis.Redis(host='localhost', port=6379)
   ```

2. **Database Persistence:**
   - Store conversations in PostgreSQL
   - Enable long-term history
   - Support conversation export

3. **Enhanced Summarization:**
   - Use LLM to generate better summaries
   - Extract key medical findings
   - Preserve critical information

4. **Multi-Session Support:**
   - Multiple concurrent conversations
   - Session switching
   - Session comparison

5. **Export Conversations:**
   - PDF export
   - Medical record integration
   - Audit trail

## 📝 Usage Examples

### Example 1: Follow-up Questions

**User:** "What's the patient's diagnosis?"
**AI:** "Based on the CT scan, the patient shows signs of pneumonia..."

**User:** "What treatment do you recommend?"
**AI:** "For the pneumonia I mentioned earlier, I recommend..." ✅ **Remembers!**

### Example 2: Page Refresh

```
1. User asks 5 questions
2. User refreshes page
3. All 5 Q&A pairs are restored
4. User continues conversation
5. AI remembers all context ✅
```

### Example 3: Clear and Start Fresh

```
1. User has long conversation about Patient A
2. User clicks "Clear Conversation"
3. Confirmation dialog appears
4. History deleted from backend
5. Chat resets with new greeting
6. Fresh conversation begins ✅
```

## 🧪 Testing

### Test Conversation Memory:

1. **Start a conversation:**
   ```
   "What is the patient's age?"
   "Tell me about their conditions"
   ```

2. **Refresh the page:**
   - All messages should reappear
   - Session ID should be preserved

3. **Continue conversation:**
   ```
   "What did you say about their conditions earlier?"
   ```
   - AI should reference previous response

4. **Clear conversation:**
   - Click "Clear Conversation"
   - Confirm dialog
   - Chat resets to greeting

### Check Backend Logs:

```bash
tail -f /tmp/engine.log | grep -i "conversation\|session"
```

Expected output:
```
[INFO] Generated new session_id: abc-123-def
[INFO] Using 5 messages from conversation history for LLM context
[INFO] Added assistant message to session abc-123-def (total: 6 messages)
[INFO] Conversation stats: {'total_sessions': 3, 'total_messages': 18, ...}
```

## 🐛 Troubleshooting

### Conversation Not Restoring?

**Check:**
1. localStorage has session ID: `localStorage.getItem('chat_session_Patient_123')`
2. Backend has history: `GET /api/v0/chat/history/{session_id}`
3. Session hasn't expired (24 hours)
4. No browser privacy mode blocking localStorage

### Clear Button Not Working?

**Check:**
1. Session ID exists: `sessionId` state is set
2. Messages > 1: Button should be enabled
3. Backend reachable: Check `/api/v0/chat/history/{session_id}` endpoint
4. No CORS errors in browser console

### Context Too Large?

**Adjust token limit:**
```python
# In chat.py, line ~60
conversation_history = conversation_manager.get_context_for_llm(
    session_id=request.session_id,
    max_tokens=1500  # Reduce if hitting limits
)
```

## ✅ What's Working Now

✅ **Session persistence** - Conversations saved per patient  
✅ **Automatic restoration** - History restored on page refresh  
✅ **Context management** - Smart token limit handling  
✅ **Clear conversation** - User control to start fresh  
✅ **Session expiration** - Auto-cleanup after 24 hours  
✅ **Memory across questions** - AI remembers previous context  
✅ **Per-patient isolation** - Each patient has separate history  

## 🎉 Impact

**Before:**
- ❌ AI forgets previous questions
- ❌ Users repeat context every time
- ❌ Page refresh loses everything
- ❌ No conversation continuity

**After:**
- ✅ AI remembers entire conversation
- ✅ Natural follow-up questions work
- ✅ Conversations survive page refresh
- ✅ Smooth, continuous dialogue
- ✅ Better clinical decision support

---

**All services running with conversation memory enabled! 🚀**

Try it out:
1. Ask a question about a patient
2. Ask a follow-up referencing the previous answer
3. Refresh the page - your conversation is still there!
4. Use "Clear Conversation" to start fresh anytime
