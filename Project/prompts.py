# Prompt templates for SOLO Taxonomy Question Generation

SYSTEM_PROMPT = """You are an expert in education and didactics, specialized in SOLO taxonomy.
Your task is to analyze educational material and generate questions in ENGLISH.

SOLO TAXONOMY - DETAILED LEVEL DEFINITIONS (Based on Biggs & Collis):

1. PRESTRUCTURAL: The task is not attacked appropriately; the student hasn't really understood the point and uses too simple a way of going about it. Students respond with irrelevant comments, exhibit lack of understanding, often missing the point entirely.
   - Questions test basic recognition of terms with minimal understanding
   - Simple identification without comprehension
   - "What is X?" (basic recall)

2. UNISTRUCTURAL: The student's response only focuses on one relevant aspect. Students give slightly relevant but vague answers that lack depth.
   - Focus on a single aspect or characteristic
   - Direct recognition or definition of a concept
   - "Define X" or "What does Y mean?"

3. MULTISTRUCTURAL: The student's response focuses on several relevant aspects but they are treated independently and additively. Assessment is primarily quantitative. Students may know the concept in bits but don't know how to connect or explain relationships.
   - Listing multiple characteristics or components
   - Enumeration without explaining connections between elements
   - "List the components of X" or "What are the characteristics of Y?"

4. RELATIONAL: The different aspects have become integrated into a coherent whole. This level represents adequate understanding of a topic. Students can identify various patterns and view a topic from distinct perspectives.
   - Explaining cause and effect relationships
   - Comparisons and contrasts
   - Analysis of relationships between concepts
   - "How does X affect Y?" or "Compare A and B"

5. EXTENDED ABSTRACT: The previous integrated whole may be conceptualized at a higher level of abstraction and generalized to a new topic or area. Students may apply classroom concepts in real life.
   - Application of knowledge in new situations
   - Hypotheses and predictions
   - Evaluation and creation of new approaches
   - "What would happen if..." or "How would you apply X in situation Y?"

Respond EXCLUSIVELY in JSON format without additional text."""

# 1. Concept extraction from material (First phase)
CONCEPT_EXTRACTION_PROMPT = """
Analyze the following educational text and extract key concepts suitable for creating SOLO questions.

For each identified concept, return:
- "name": brief concept name
- "definition": how it is defined in the text
- "context": sentence/section from text where it is mentioned
- "solo_levels": list of SOLO levels that can be tested for this concept
- "related_concepts": list of other concepts from text that are connected

Focus on:
- Key terms and their definitions
- Processes and procedures
- Cause-and-effect relationships
- System components
- Examples and cases
- Principles that can be applied

Text:
{text}
"""
ANALYSIS_PROMPT = """
Analyze the following text and identify elements suitable for SOLO taxonomy.
Return JSON with the following keys:
- "definitions": list of terms and their definitions (for Unistructural)
- "enumerations": list of concepts that have multiple parts/characteristics (for Multistructural)
- "relationships": list of concept pairs that are causally connected or can be compared (for Relational)
- "application_concepts": list of abstract principles that can be applied in new situations (for Extended Abstract)

Text:
{text}
"""

# 2. Question generation based on analysis
SOLO_GENERATION_PROMPTS = {
    "prestructural": """
    Using the following DEFINITIONS from text analysis: {analysis_data}
    
    Create 1 PRESTRUCTURAL/UNISTRUCTURAL level question.
    TECHNIQUE: Choose one definition and ask for basic recognition/recall.
    
    EXAMPLE 1:
    Input: "CPU is the central processing unit."
    Question: "What does the abbreviation CPU stand for?"
    
    EXAMPLE 2:
    Input: "Malware is malicious software."
    Question: "Which term is used for software designed to harm computers?"
    
    Return ONLY JSON:
    {{
        "question": "...",
        "options": ["A)...", "B)...", "C)..."],
        "correct_answer": "...",
        "explanation": "..."
    }}
    """,
    
    "multistructural": """
    Using the following ENUMERATIONS from text analysis: {analysis_data}
    
    Create 1 MULTISTRUCTURAL level question.
    TECHNIQUE: Choose a concept with multiple parts and ask to identify all components or which doesn't belong.
    
    EXAMPLE 1:
    Input: "Primary colors are red, blue, and yellow."
    Question: "Which of the following are primary colors?"
    
    EXAMPLE 2:
    Input: "Computer components include CPU, RAM, HDD."
    Question: "Which of the following is NOT a hardware component of a computer?"
    
    Return ONLY JSON:
    {{
        "question": "...",
        "options": ["A)...", "B)...", "C)..."],
        "correct_answer": "...",
        "explanation": "..."
    }}
    """,
    
    "relational": """
    Using the following RELATIONSHIPS from text analysis: {analysis_data}
    
    Create 1 RELATIONAL level question.
    TECHNIQUE: Choose two connected concepts and ask to explain their relationship.
    
    EXAMPLE 1:
    Input: "More RAM allows faster operation of multiple applications simultaneously."
    Question: "How does increasing RAM memory affect multitasking performance?"
    
    EXAMPLE 2:
    Input: "Viruses spread by copying themselves, while Trojans require user activation."
    Question: "What is the key difference in spreading methods between viruses and Trojans?"
    
    Return ONLY JSON:
    {{
        "question": "...",
        "options": ["A)...", "B)...", "C)..."],
        "correct_answer": "...",
        "explanation": "..."
    }}
    """,
    
    "extended_abstract": """
    Using the following APPLICATION CONCEPTS from text analysis: {analysis_data}
    
    Create 1 EXTENDED ABSTRACT level question.
    TECHNIQUE: Present a hypothetical situation not in the text and ask for principle application.
    
    EXAMPLE 1:
    Input: "Encryption principle protects data from unauthorized access."
    Question: "A company wants to protect confidential employee emails who work from home. Which security measure would be best to implement and why?"
    
    Return ONLY JSON:
    {{
        "question": "...",
        "options": ["A)...", "B)...", "C)..."],
        "correct_answer": "...",
        "explanation": "..."
    }}
    """
}

# 3. Validation and Classification (Self-Correction)
CLASSIFICATION_PROMPT = """
Analyze the following question and answer, and classify it according to SOLO taxonomy.
Question: {question}
Expected answer: {answer}

Determine the level (Prestructural, Unistructural, Multistructural, Relational, Extended Abstract) and provide brief reasoning.
"""
