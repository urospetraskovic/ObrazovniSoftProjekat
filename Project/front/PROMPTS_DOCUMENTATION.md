# 📍 SOLO Taxonomy Prompts - Complete Documentation

## Where Are The Prompts?

### File Locations

**Backend Implementation:**
- **File**: `D:\GitHub\ObrazovniSoftProjekat\Project\front\backend\quiz_generator.py`
- **Function**: `_build_prompt(self, content: str, level: str, context: str) -> str`
- **Lines**: ~167-250

**Original Prompt Templates:**
- **File**: `D:\GitHub\ObrazovniSoftProjekat\Project\prompts.py`
- **Contains**: SOLO taxonomy definitions and prompt templates

---

## 📋 What's In The Prompts Now

### Complete SOLO Taxonomy Definitions

Each prompt now includes the **FULL SOLO taxonomy definition section** with all 5 levels:

```
SOLO TAXONOMY - DETAILED LEVEL DEFINITIONS (Based on Biggs & Collis):

1. PRESTRUCTURAL: The task is not attacked appropriately; the student hasn't really understood...
2. UNISTRUCTURAL: The student's response only focuses on one relevant aspect...
3. MULTISTRUCTURAL: The student's response focuses on several relevant aspects...
4. RELATIONAL: The different aspects have become integrated into a coherent whole...
5. EXTENDED ABSTRACT: The previous integrated whole may be conceptualized at a higher level...
```

### Each Level Includes

✅ **Detailed Description** - What students demonstrate at this level
✅ **Question Characteristics** - What makes questions appropriate for this level
✅ **Question Patterns** - Example question formats
✅ **Learning Examples** - How this level manifests in practice

---

## 🔍 Prompt Structure for Each SOLO Level

### 1️⃣ PRESTRUCTURAL Prompt

**Location**: `quiz_generator.py` - `prompts['prestructural']`

**Includes**:
- ✅ Full SOLO taxonomy definitions
- ✅ Specific requirements for prestructural questions
- ✅ Pattern to follow: "What is X?" or "What does Y mean?"
- ✅ Instruction to test basic recognition without deep comprehension
- ✅ JSON format requirements
- ✅ Content excerpt (500 chars)

**Example Requirement**:
```
Test basic recognition of terms with minimal understanding
Simple identification or recall without deep comprehension
Follow pattern: "What is X?" or "What does Y mean?"
```

---

### 2️⃣ MULTISTRUCTURAL Prompt

**Location**: `quiz_generator.py` - `prompts['multistructural']`

**Includes**:
- ✅ Full SOLO taxonomy definitions
- ✅ Specific requirements for multistructural questions
- ✅ Pattern: "List the components of X" or "Which of these are characteristics of Y?"
- ✅ Emphasis on independent aspects (NOT connections)
- ✅ Multiple items without relationships
- ✅ JSON format requirements

**Example Requirement**:
```
Focus on several relevant aspects that are treated independently
Ask student to list multiple components or characteristics
Do NOT ask about connections between elements
```

---

### 3️⃣ RELATIONAL Prompt

**Location**: `quiz_generator.py` - `prompts['relational']`

**Includes**:
- ✅ Full SOLO taxonomy definitions
- ✅ Specific requirements for relational questions
- ✅ Pattern: "How does X affect Y?" or "Compare A and B"
- ✅ Emphasis on integrated understanding
- ✅ Cause-effect and comparisons
- ✅ Showing connections between concepts
- ✅ JSON format requirements

**Example Requirement**:
```
Integrate multiple aspects into a coherent whole
Ask about cause-and-effect relationships
Ask for comparisons and contrasts
Ask how concepts are connected
```

---

### 4️⃣ EXTENDED ABSTRACT Prompt

**Location**: `quiz_generator.py` - `prompts['extended_abstract']`

**Includes**:
- ✅ Full SOLO taxonomy definitions
- ✅ Specific requirements for extended abstract questions
- ✅ Pattern: "What would happen if...?" or "How would you apply X in situation Y?"
- ✅ Real-world application beyond content
- ✅ Hypothetical scenarios
- ✅ Transfer of learning emphasis
- ✅ JSON format requirements

**Example Requirement**:
```
Ask student to apply concepts to new or hypothetical situations
Go beyond the content with real-world application
Ask for predictions, hypotheses, or creative solutions
Present a novel scenario not directly in the original content
```

---

## 🎯 What Each Prompt Contains

### 1. SOLO Taxonomy Definitions Section
```
Complete definitions for all 5 SOLO levels
- Detailed explanation of each level
- Characteristics of student responses at each level
- Question patterns for each level
```

### 2. Task Specification
```
Which SOLO level to generate for
Specific requirements for that level
What makes a good question at this level
```

### 3. Requirements Section
```
Specific characteristics for questions at this level
Question patterns to follow
What to test/measure
What NOT to include
```

### 4. Content
```
500 characters of actual lesson content
Ensures questions are grounded in the material
Provides context for question generation
```

### 5. Format Specification
```
Return ONLY valid JSON
Specific JSON fields required:
  - question: the question text
  - options: array of 4 options
  - correct_answer: the correct option
  - explanation: explanation of the answer
```

---

## ✅ Verification Checklist

Let me verify the prompts have everything needed:

### Prestructural Level ✅
- [x] Includes full SOLO taxonomy definitions
- [x] Specifies "basic recognition/recall" requirement
- [x] Mentions minimal understanding
- [x] Gives example patterns: "What is X?"
- [x] Requires JSON format
- [x] Includes content excerpt

### Multistructural Level ✅
- [x] Includes full SOLO taxonomy definitions
- [x] Specifies multiple independent aspects
- [x] EXPLICITLY says "Do NOT ask about connections"
- [x] Gives patterns: "List the components of X"
- [x] Mentions enumeration without relationships
- [x] Requires JSON format

### Relational Level ✅
- [x] Includes full SOLO taxonomy definitions
- [x] Specifies integrated understanding
- [x] Asks for cause-effect relationships
- [x] Mentions comparisons and contrasts
- [x] Patterns: "How does X affect Y?"
- [x] Requires JSON format

### Extended Abstract Level ✅
- [x] Includes full SOLO taxonomy definitions
- [x] Specifies new/hypothetical situations
- [x] Goes beyond original content
- [x] Patterns: "What would happen if...?"
- [x] Emphasizes real-world application
- [x] Requires JSON format

---

## 📝 Example: How It Works

When you ask the quiz generator to create a quiz:

1. **File Upload** → Your .txt file
2. **Backend receives** → File content
3. **Generator analyzes** → Splits into chapters
4. **For each chapter**:
   - Calls `_build_prompt()` with `level='prestructural'`
   - Builds prompt with **FULL SOLO definitions + specific requirements**
   - Sends to OpenRouter API
   - Receives JSON response
   - Returns formatted question

5. **Final Quiz** → Multiple questions at each level

---

## 🔄 Current Prompt Flow

```
User uploads file
        ↓
Backend reads content
        ↓
Splits into chapters
        ↓
For each chapter:
        ├─→ PRESTRUCTURAL level
        │   └─→ _build_prompt() with FULL definitions
        │       └─→ API returns question
        │
        ├─→ MULTISTRUCTURAL level
        │   └─→ _build_prompt() with FULL definitions
        │       └─→ API returns question
        │
        ├─→ RELATIONAL level
        │   └─→ _build_prompt() with FULL definitions
        │       └─→ API returns question
        │
        └─→ EXTENDED ABSTRACT level
            └─→ _build_prompt() with FULL definitions
                └─→ API returns question
        ↓
Quiz compiled and returned to frontend
```

---

## 💡 Key Features of the Updated Prompts

### 1. Comprehensive Definition Context
Each prompt includes the full SOLO taxonomy framework so the AI understands the complete taxonomy hierarchy.

### 2. Specific Requirements per Level
Clear instructions about what makes a question appropriate for each level.

### 3. Pattern Examples
Concrete question patterns to guide question generation.

### 4. Content Grounding
500-character excerpt from actual lesson content ensures questions are relevant.

### 5. Format Clarity
Explicit JSON format requirements ensure consistent, parseable responses.

### 6. No Ambiguity
Clear statements about what to do and what NOT to do:
- "Do NOT ask about connections" (for multistructural)
- "Ask for comparisons and contrasts" (for relational)
- "Present a novel scenario" (for extended abstract)

---

## 🎓 How This Ensures Quality Questions

### Before Update
```
Prompts were vague:
"Create a PRESTRUCTURAL level question"
→ AI might guess what this means
→ Questions could miss SOLO level objectives
```

### After Update
```
Prompts are comprehensive:
"PRESTRUCTURAL: The task is not attacked appropriately...
Test basic recognition of terms with minimal understanding
Simple identification or recall without deep comprehension
Follow pattern: 'What is X?'"
→ AI fully understands the level
→ Questions accurately reflect SOLO objectives
```

---

## 📊 Prompt Statistics

| Aspect | Details |
|--------|---------|
| **Total Lines** | ~200+ lines of prompt specifications |
| **SOLO Definitions** | Included in EVERY prompt (5 levels × 4 prompts) |
| **Requirements** | Specific to each level |
| **Examples** | Question patterns provided |
| **Context** | 500 characters of content per prompt |
| **Format** | JSON specification included |

---

## 🔧 If You Want to Modify Prompts

### Edit Location
```
File: D:\GitHub\ObrazovniSoftProjekat\Project\front\backend\quiz_generator.py
Function: _build_prompt()
```

### How to Modify
1. Open the file
2. Find the `_build_prompt` method
3. Edit the prompt for the specific level you want to change
4. Restart the backend: `python app.py`
5. Test with a new file upload

### Example Modification
```python
'prestructural': f"""Updated prompt here...

{solo_definitions}

Your custom requirements...
"""
```

---

## ✨ Summary

### ✅ The Prompts Now Include:
- Complete SOLO taxonomy framework
- Detailed definitions of all 5 levels
- Level-specific requirements
- Question patterns and examples
- Content excerpt
- JSON format specifications
- Clear do's and don'ts

### ✅ This Ensures:
- AI understands full SOLO hierarchy
- Questions match intended cognitive level
- Consistent, high-quality output
- Proper JSON formatting
- Grounded in actual lesson content

### ✅ You Can:
- Generate quizzes with confidence
- Rely on proper SOLO level implementation
- Modify prompts easily if needed
- Understand exactly how questions are generated

---

## 📍 Quick Reference

**To View the Prompts:**
```
File: D:\GitHub\ObrazovniSoftProjekat\Project\front\backend\quiz_generator.py
Lines: ~167-250
Function: _build_prompt()
```

**To Modify the Prompts:**
1. Edit the `prompts` dictionary in `_build_prompt()`
2. Restart backend
3. Test with new file

**To Use the Prompts:**
1. Upload file via web interface
2. Click "Generate Quiz"
3. Prompts are used automatically
4. Questions generated according to specifications

---

**Status**: ✅ **PROMPTS FULLY UPDATED WITH COMPLETE SOLO DEFINITIONS**

All prompts now include comprehensive SOLO taxonomy explanations!
