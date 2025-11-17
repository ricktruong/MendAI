# 🧪 Conversation Memory - Quick Test Guide

## Quick Test (2 minutes)

### Test 1: Basic Memory ✅

1. **Open patient dashboard:**
   ```
   http://localhost:3000
   → Click any patient
   → Go to "Chat" tab
   ```

2. **Ask first question:**
   ```
   "What is this patient's age?"
   ```
   Expected: AI responds with patient's age

3. **Ask follow-up (testing memory):**
   ```
   "Based on their age, what health concerns should we watch for?"
   ```
   Expected: AI references the age from previous answer ✨

4. **Verify memory working:**
   - AI should mention specific age number
   - AI should not ask "which patient?" or "what age?"
   - Response should be contextually aware

### Test 2: Page Refresh Persistence ✅

1. **Have a conversation (3-4 messages)**

2. **Refresh the page:**
   ```
   Press Cmd+R (Mac) or F5 (Windows)
   ```

3. **Check results:**
   - ✅ All previous messages should reappear
   - ✅ Chat should scroll to bottom
   - ✅ You should be able to continue the conversation

4. **Send another message:**
   ```
   "What did we discuss earlier?"
   ```
   Expected: AI references previous conversation ✨

### Test 3: Clear Conversation ✅

1. **Look for the red button:**
   ```
   Top-right of chat: "🗑️ Clear Conversation"
   ```

2. **Click it:**
   - Should show confirmation dialog
   - Click "OK" to confirm

3. **Verify:**
   - ✅ Chat resets to greeting message
   - ✅ Only 1 message visible (greeting)
   - ✅ Previous conversation gone

4. **Start new conversation:**
   ```
   "Hello, what can you help me with?"
   ```
   Expected: Fresh conversation starts ✨

## Advanced Tests

### Test 4: Long Conversation Context

1. **Ask 10 questions in a row**

2. **On question 11, reference answer #1:**
   ```
   "You mentioned earlier that [something from answer 1]. Can you explain more?"
   ```

3. **Expected:**
   - AI should remember early context
   - Context management should handle it smoothly

### Test 5: Multi-Patient Sessions

1. **Talk to Patient A:**
   ```
   Ask 3 questions about Patient A
   ```

2. **Switch to Patient B:**
   ```
   Go back to patient list
   Open Patient B
   Go to Chat tab
   ```

3. **Expected:**
   - ✅ Patient B has fresh conversation (no Patient A context)
   - ✅ Each patient has isolated session

4. **Return to Patient A:**
   ```
   Go back to patient list
   Open Patient A again
   Go to Chat tab
   ```

5. **Expected:**
   - ✅ Patient A conversation restored
   - ✅ All 3 original messages visible

## Backend Verification

### Check Logs:

```bash
# Watch conversation activity
tail -f /tmp/engine.log | grep -i "conversation\|session"
```

**Expected output when sending message:**
```
[INFO] Generated new session_id: abc-123-def-456
[INFO] Added user message to session abc-123-def-456 (total: 2 messages)
[INFO] Using 2 messages from conversation history for LLM context
[INFO] Added assistant message to session abc-123-def-456 (total: 3 messages)
[INFO] Conversation stats: {'total_sessions': 1, 'total_messages': 3, 'avg_messages_per_session': 3.0}
```

### Check Session Storage:

```bash
# Get conversation stats
curl -s http://localhost:8000/api/v0/chat/stats | python3 -m json.tool
```

**Expected:**
```json
{
  "success": true,
  "stats": {
    "total_sessions": 2,
    "total_messages": 15,
    "avg_messages_per_session": 7.5
  }
}
```

### Check Specific Session:

```bash
# Replace {session_id} with actual ID from localStorage or logs
curl -s http://localhost:8000/api/v0/chat/history/{session_id} | python3 -m json.tool
```

**Expected:**
```json
{
  "session_id": "abc-123-def-456",
  "messages": [
    {
      "role": "user",
      "content": "What is the patient's age?",
      "timestamp": "2025-11-16T10:30:00"
    },
    {
      "role": "assistant",
      "content": "The patient is 62 years old...",
      "timestamp": "2025-11-16T10:30:05"
    }
  ],
  "count": 2
}
```

## Browser Dev Tools Verification

### Check localStorage:

1. **Open browser console:**
   ```
   Press F12
   → Go to "Console" tab
   ```

2. **Check session IDs:**
   ```javascript
   // Check all stored sessions
   Object.keys(localStorage).filter(k => k.startsWith('chat_session_'))
   
   // Output: ["chat_session_Patient_123", "chat_session_Patient_456"]
   ```

3. **View specific session:**
   ```javascript
   localStorage.getItem('chat_session_Patient_123')
   // Output: "abc-123-def-456-789"
   ```

4. **Clear all sessions (for testing):**
   ```javascript
   Object.keys(localStorage)
     .filter(k => k.startsWith('chat_session_'))
     .forEach(k => localStorage.removeItem(k))
   ```

## Expected Behaviors ✅

### ✅ Memory Working:
- AI references previous answers
- Follow-up questions understood
- Context maintained across messages
- No repeated questions needed

### ✅ Persistence Working:
- Refresh preserves conversation
- Messages restored in order
- Session ID consistent
- Can continue after refresh

### ✅ Clear Working:
- Confirmation dialog appears
- All messages removed
- Fresh greeting shown
- New session created

### ✅ Isolation Working:
- Each patient has separate session
- No cross-patient context bleeding
- Sessions don't interfere

## Common Issues & Solutions

### ❌ Memory Not Working

**Symptoms:**
- AI forgets previous questions
- Asks "which patient?" repeatedly
- No context awareness

**Check:**
```bash
# 1. Verify conversation manager loaded
grep -i "ConversationManager initialized" /tmp/engine.log

# 2. Check if messages being stored
grep -i "Added.*message to session" /tmp/engine.log

# 3. Verify LLM getting context
grep -i "Using.*messages from conversation history" /tmp/engine.log
```

**Fix:**
- Restart engine service if ConversationManager not initialized
- Check for errors in /tmp/engine.log

### ❌ Persistence Not Working

**Symptoms:**
- Refresh clears all messages
- sessionId not saved

**Check:**
```javascript
// In browser console
localStorage.getItem('chat_session_Patient_123')
// Should return session ID string
```

**Fix:**
- Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
- Check browser privacy settings (localStorage must be enabled)
- Verify network tab shows GET /chat/history/{session_id} request

### ❌ Clear Button Not Working

**Check:**
```bash
# Test endpoint directly
curl -X DELETE http://localhost:8000/api/v0/chat/history/{session_id}
```

**Fix:**
- Verify session ID exists
- Check browser network tab for errors
- Ensure backend endpoint is accessible

## Success Criteria

Your conversation memory is working if:

✅ AI remembers previous questions in same conversation  
✅ Page refresh restores full conversation history  
✅ Each patient has separate, isolated conversation  
✅ Clear button removes all history and starts fresh  
✅ Session survives browser close/reopen  
✅ Long conversations handled gracefully (10+ messages)  
✅ Backend logs show session management activity  
✅ localStorage contains session IDs  

## Performance Check

### Expected Response Times:

- **First message:** ~2-3 seconds (new session creation)
- **Follow-up messages:** ~1-2 seconds (context loaded)
- **History restoration:** < 1 second (local storage + API call)
- **Clear conversation:** < 500ms (instant UI update)

### Memory Usage:

```bash
# Check if memory growing excessively
ps aux | grep "uvicorn engine.main"
# RSS column should be stable (not continuously growing)
```

## 🎉 You're Done!

If all tests pass, your conversation memory feature is fully working! 

The AI will now:
- 🧠 Remember all previous questions
- 💬 Provide contextual responses
- 💾 Survive page refreshes
- 🔄 Allow fresh starts with clear button
- 👤 Keep patient sessions isolated

Enjoy your enhanced chat experience! 🚀
