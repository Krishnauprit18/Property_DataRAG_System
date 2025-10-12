# 🎬 Complete Video Demo Guide - Property RAG System

## 🚀 Quick Start Commands

### Terminal 1 - Backend Server
```bash
cd /home/krishna/Music/Property_DataRAG_System/backend
source venv/bin/activate
python main.py
```
**Expected Output:**
```
INFO: Starting Property RAG System...
INFO: ✅ Loaded vector database with 139,728 properties
INFO: ✅ Global analytics initialized
INFO: System ready!
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2 - Frontend App
```bash
cd /home/krishna/Music/Property_DataRAG_System
source backend/venv/bin/activate
streamlit run frontend/app.py
```
**Expected Output:**
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

---

## 📋 Video Demo Flow (15-20 minutes)

### **Part 1: Introduction (2 min)**

**What to Show:**
- Project overview
- Technology stack
- Key features

**Script:**
```
"Yeh ek Property RAG System hai jo 139,000+ properties ka data handle karta hai.
Technologies used:
- FastAPI backend
- ChromaDB vector database
- Sentence Transformers for embeddings
- Google Gemini LLM
- Streamlit frontend
- Conversational memory

Main features:
✅ Natural language queries
✅ Semantic search
✅ Smart filters
✅ Conversational AI with memory
✅ Real-time analytics
✅ Fast response times"
```

---

### **Part 2: Basic Search (3 min)**

#### **Test 1: Simple Property Search**
**Query:** "Show me properties in London"
**Filters:** None
**Show:**
- Query response
- Number of results
- Property cards with details
- Response time

#### **Test 2: Specific Requirements**
**Query:** "I need a 2 bedroom apartment"
**Filters:** None
**Show:**
- How LLM understands the requirement
- Relevant results
- Property details matching query

#### **Test 3: Budget Query**
**Query:** "Find affordable properties under £1000"
**Filters:** None
**Show:**
- Price-based filtering
- Results within budget

---

### **Part 3: Filter Functionality (4 min) - IMPORTANT!**

**Intro:**
"Pehle is project mein filter functionality mein errors aa rahe the. 
Jab price range ya multiple filters use karte the to error aata tha.
Maine yeh fix kar diya hai. Ab dekho kaise kaam kar raha hai:"

#### **Test 4: Price Range Filter (FIXED)**
**Query:** "Show me properties"
**Filters:**
- ☑️ Filter by Price
  - Min: £1000
  - Max: £2000

**Point Out:**
- "Yeh pehle broken tha - price range error deta tha"
- "Ab perfect kaam kar raha hai"
- Show results within range

#### **Test 5: Multiple Filters (FIXED)**
**Query:** "Find spacious 3 bedroom properties"
**Filters:**
- ☑️ Filter by Price: £1000-£3000
- ☑️ Filter by Bedrooms: 3
- ☑️ Filter by Bathrooms: 2

**Point Out:**
- "Multiple filters saath mein pehle error dete the"
- "Ab sab smooth kaam kar raha hai"
- Show all filters applied correctly

#### **Test 6: Studio Apartments**
**Query:** "Show me studio apartments"
**Filters:**
- ☑️ Filter by Bedrooms: 0
- ☑️ Filter by Price: Max £1200

**Show:**
- Studio apartments (0 bedrooms)
- Price filtering working

---

### **Part 4: Conversational AI (4 min)**

**Intro:**
"System conversational memory use karta hai. 
Previous queries yaad rakhta hai aur context maintain karta hai."

#### **Test 7: Multi-turn Conversation**
**Query 1:** "Show me 2 bedroom apartments in Manchester"
**Expected:** 2-bed properties

**Query 2:** "What about under £1500?"
**Expected:** System remembers "2 bedroom" + adds price filter

**Query 3:** "Which one has the lowest crime score?"
**Expected:** Analyzes previous results, finds safest area

**Show:**
- Active session indicator
- Message count
- Context awareness
- "View History" button
- Conversation history panel

#### **Test 8: Context Refinement**
**Query 1:** "Find properties with gym and parking"
**Query 2:** "What about cheaper ones?"
**Query 3:** "Show me those in South London"

**Show:**
- How context carries forward
- Refinement based on previous queries
- Natural conversation flow

---

### **Part 5: Analytics Dashboard (3 min)**

#### **Test 9: Database Statistics**
**Show in Sidebar:**
- Total properties: 139,728
- Collection name
- Active session info

#### **Test 10: Query Analytics**
**Navigate to:** `http://localhost:8000/analytics`
**Show:**
- Query statistics
- Response times
- Success rates
- Popular searches

**Browser Command:**
```bash
# Open in browser
curl http://localhost:8000/analytics | jq
```

---

### **Part 6: Advanced Queries (3 min)**

#### **Test 11: Comparative Analysis**
**Query:** "Compare properties in Birmingham vs Manchester"
**Show:**
- Comparative response
- Price differences
- Multiple location handling

#### **Test 12: Statistical Query**
**Query:** "What's the average price of 3 bedroom homes?"
**Show:**
- LLM generates statistical answer
- Global analytics integration
- Accurate calculations

#### **Test 13: Complex Requirements**
**Query:** "Show me 4 bedroom detached houses with garden in premium areas under 3000"
**Filters:**
- Bedrooms: 4
- Max Price: £3000

**Show:**
- Complex query understanding
- Multiple parameter handling
- Relevant results

---

### **Part 7: System Features (2 min)**

#### **Feature 1: New Chat**
**Action:** Click "🆕 New Chat"
**Show:**
- New session created
- Conversation history cleared
- Fresh start

#### **Feature 2: Clear Conversation**
**Action:** Click "🗑️ Clear"
**Show:**
- Session cleared
- History removed

#### **Feature 3: View History**
**Action:** Click "📜 View History"
**Show:**
- Full conversation log
- User and assistant messages
- Timestamps

#### **Feature 4: Number of Results Slider**
**Action:** Adjust slider (1-20)
**Show:**
- Dynamic result count
- Performance with different counts

---

## 🎯 Key Demo Points Checklist

### Technical Highlights:
- [ ] 139,728 properties in database
- [ ] Real-time semantic search
- [ ] < 2 second response times
- [ ] Conversational memory
- [ ] Multiple filter combinations
- [ ] Natural language understanding

### Fixed Issues:
- [ ] ✅ Price range filters (min + max together)
- [ ] ✅ Multiple filters combined
- [ ] ✅ ChromaDB query syntax
- [ ] ✅ All filter combinations working

### UI/UX Features:
- [ ] Clean, modern interface
- [ ] Real-time filtering
- [ ] Session management
- [ ] Conversation history
- [ ] Property cards with details
- [ ] Response indicators

---

## 🎥 Screen Recording Tips

### What to Show:
1. **Both terminals** running (split screen)
2. **Browser with frontend** (main focus)
3. **Query inputs** clearly visible
4. **Filter sidebar** when using filters
5. **Results section** with property cards
6. **Conversation history** expanding
7. **Session indicators**

### Camera Angles:
- Start with full screen overview
- Zoom into query input when typing
- Show filter sidebar when selecting
- Pan to results section
- Show terminal logs occasionally

### Voice Over Points:
- Explain what you're doing
- Highlight fixed features
- Point out response times
- Explain conversational context
- Demonstrate filter combinations

---

## 🐛 Troubleshooting During Demo

### If Backend Not Starting:
```bash
# Check port
lsof -i :8000
# Kill if needed
kill -9 <PID>
# Restart
cd backend && python main.py
```

### If Frontend Not Loading:
```bash
# Check port
lsof -i :8501
# Kill if needed
kill -9 <PID>
# Restart
streamlit run frontend/app.py
```

### If No Results Found:
- Check backend logs for errors
- Verify ChromaDB has data (1.7GB in backend/chroma_db)
- Restart backend from backend directory

### If Filters Not Working:
- Clear browser cache
- Restart frontend
- Check backend/vector_store.py has latest fix

---

## 📊 Expected Performance Metrics

| Metric | Value | Demo Point |
|--------|-------|------------|
| Total Properties | 139,728 | "Bahut bada database" |
| Response Time | 1-2 sec | "Fast response" |
| Query Success Rate | 100% | "No errors" |
| Filter Combinations | All working | "Sab fixed hai" |
| Conversation Memory | 10+ messages | "Context yaad rakhta hai" |

---

## 🎬 Closing Points

**Summary:**
```
"Toh yeh tha complete Property RAG System demo.

✅ Natural language search
✅ Smart filtering - sab fixed
✅ Conversational AI with memory
✅ Fast and accurate
✅ 139,000+ properties

Pehle jo filter errors the wo fix ho gaye hain.
Ab aap koi bhi combination use kar sakte ho.

Technologies:
- ChromaDB for vector storage
- Sentence Transformers for embeddings
- Google Gemini for LLM
- FastAPI backend
- Streamlit frontend

Thank you for watching!"
```

---

## 📝 Pre-Demo Checklist

- [ ] Backend virtual environment activated
- [ ] Frontend virtual environment activated
- [ ] Both servers running
- [ ] Browser opened to http://localhost:8501
- [ ] Screen recording software ready
- [ ] Audio check done
- [ ] Terminal fonts readable
- [ ] Browser zoom level comfortable
- [ ] Test query prepared
- [ ] Backup test cases ready

---

## 🚀 One-Command Demo Start

```bash
# Create a quick start script
./start_demo.sh
```

Or manually:
```bash
# Terminal 1
cd backend && source venv/bin/activate && python main.py

# Terminal 2
cd /home/krishna/Music/Property_DataRAG_System && \
source backend/venv/bin/activate && \
streamlit run frontend/app.py
```

---

## 📌 Important Files Reference

- **Backend:** `/home/krishna/Music/Property_DataRAG_System/backend/main.py`
- **Frontend:** `/home/krishna/Music/Property_DataRAG_System/frontend/app.py`
- **Vector Store:** `/home/krishna/Music/Property_DataRAG_System/backend/vector_store.py`
- **Data:** `/home/krishna/Music/Property_DataRAG_System/Property_data.csv`
- **ChromaDB:** `/home/krishna/Music/Property_DataRAG_System/backend/chroma_db/`

---

**Demo Duration:** 15-20 minutes  
**Difficulty Level:** Medium  
**Recommended Recording:** 1080p, 30fps  
**Audio:** Clear Hindi/English mix  

**Status:** ✅ Ready for Recording!

---

*Last Updated: 12 October 2025*  
*All errors fixed and tested!* 🎉
