# Enhanced Quiz Generator with Quality Validation & Multi-Pass Refinement
# Add this to quiz_generator.py after the _build_prompt method

from typing import Dict, List, Any
import json

def _validate_question_quality(self, question_data: Dict[str, Any], content: str, level: str) -> Dict[str, bool]:
    """
    Validate generated question for quality metrics
    Returns dict with validation results and score
    """
    quality_checks = {
        'has_structure': False,
        'has_realistic_distractors': False,
        'no_obvious_answer': False,
        'appropriate_difficulty': False,
        'good_explanation': False,
        'overall_pass': False
    }
    
    try:
        q = question_data.get('question', '')
        opts = question_data.get('options', [])
        corr = question_data.get('correct_answer', '')
        expl = question_data.get('explanation', '')
        
        # Check 1: Has proper structure
        if q and len(opts) == 4 and corr and expl:
            quality_checks['has_structure'] = True
        
        # Check 2: Distractors aren't obviously wrong
        distractor_words = set()
        for opt in opts:
            if opt != corr:
                words = opt.lower().split()
                distractor_words.update(words)
        
        # Bad patterns in distractors
        bad_patterns = ['fake', 'pretend', 'made up', 'nonsense', 'cheese', 'obviously', 'never', 'always']
        has_bad_pattern = any(pattern in ' '.join([o.lower() for o in opts]) for pattern in bad_patterns)
        
        if not has_bad_pattern and len(distractor_words) > 5:
            quality_checks['has_realistic_distractors'] = True
        
        # Check 3: Correct answer isn't obvious by elimination
        # If options are very different lengths or structure, answer is too obvious
        opt_lengths = [len(o) for o in opts]
        length_variance = max(opt_lengths) - min(opt_lengths)
        
        # Also check if correct answer contains too many keywords from question
        q_words = set(q.lower().split())
        corr_words = set(corr.lower().split())
        keyword_overlap = len(q_words & corr_words) / (len(q_words) + 1)
        
        if length_variance < 30 and keyword_overlap < 0.4:
            quality_checks['no_obvious_answer'] = True
        
        # Check 4: Difficulty appropriate for SOLO level
        if level == 'unistructural':
            # Should be shorter, simpler
            if len(q) < 200 and len(expl) < 150:
                quality_checks['appropriate_difficulty'] = True
        elif level == 'multistructural':
            # Medium complexity
            if len(q) < 250 and len(expl) < 200:
                quality_checks['appropriate_difficulty'] = True
        elif level in ['relational', 'extended_abstract']:
            # Can be longer, more complex
            if len(q) < 300 and len(expl) < 250:
                quality_checks['appropriate_difficulty'] = True
        
        # Check 5: Explanation is meaningful, not generic
        generic_phrases = ['this is correct', 'the answer is', 'because it is']
        is_generic = any(phrase in expl.lower() for phrase in generic_phrases)
        
        if not is_generic and len(expl) > 30 and len(expl.split()) > 5:
            quality_checks['good_explanation'] = True
        
        # Overall: pass if 4/5 checks pass
        passed_checks = sum(1 for v in list(quality_checks.values())[:-1] if v)
        quality_checks['overall_pass'] = passed_checks >= 4
        
    except Exception as e:
        print(f"[QUALITY CHECK] Error: {str(e)}")
        quality_checks['overall_pass'] = False
    
    return quality_checks


def _refine_question(self, question_data: Dict[str, Any], level: str, quality_issues: str) -> Dict[str, Any]:
    """
    Refine a question that didn't pass quality checks
    Asks AI to critique and improve the question
    """
    prompt = f"""You are an expert educational assessment designer. Review this SOLO Level {level.upper()} question and REFINE it.

CURRENT QUESTION:
{json.dumps(question_data, indent=2)}

QUALITY ISSUES TO FIX:
{quality_issues}

IMPROVEMENT TASKS:
1. Make distractors MORE PLAUSIBLE and LESS OBVIOUS
   - Ensure they relate to the topic but are factually wrong
   - Avoid generic wrong answers like "never", "always", "fake"
   - Make each distractor a realistic misconception or alternative answer
   
2. If answer is too obvious, vary the option lengths and structures more
   
3. Make explanation MORE DETAILED and EDUCATIONAL
   - Explain WHY correct answer is right
   - Explain WHY each distractor is wrong
   - Teach the concept, not just confirm the answer

4. Adjust question complexity to match {level.upper()} level:
   - UNISTRUCTURAL: Simple single fact, direct recall
   - MULTISTRUCTURAL: Multiple independent facts, no connections
   - RELATIONAL: Show how parts connect and relate
   - EXTENDED_ABSTRACT: Apply to new situations beyond the content

RETURN ONLY IMPROVED JSON: {{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "A) ...", "explanation": "..."}}"""
    
    try:
        refined = self._call_api(prompt)
        refined_data = self._parse_json_response(refined)
        if refined_data and all(k in refined_data for k in ['question', 'options', 'correct_answer', 'explanation']):
            return refined_data
    except Exception as e:
        print(f"[REFINE] Error refining question: {str(e)}")
    
    return question_data  # Return original if refinement fails


def _generate_question_with_quality_check(self, content: str, level: str, context: str, content_summary: str = "", retry_count: int = 0) -> Dict[str, Any]:
    """
    Generate a question and validate quality. Retry/refine if needed.
    """
    max_retries = 2
    
    if retry_count > max_retries:
        print(f"[{level.upper()}] Max retries reached, returning best attempt")
        return None
    
    # Generate question
    prompt = self._build_prompt(content, level, context, content_summary)
    response = self._call_api(prompt)
    question_data = self._parse_json_response(response)
    
    if not question_data:
        print(f"[{level.upper()}] Failed to parse response, retrying...")
        return self._generate_question_with_quality_check(content, level, context, content_summary, retry_count + 1)
    
    # Validate quality
    quality_checks = self._validate_question_quality(question_data, content, level)
    
    if quality_checks['overall_pass']:
        print(f"[{level.upper()}] ✓ Question passed quality checks")
        return question_data
    else:
        # Identify issues
        failed_checks = [k for k, v in quality_checks.items() if not v and k != 'overall_pass']
        issues_desc = ", ".join(failed_checks)
        print(f"[{level.upper()}] ⚠ Quality issues: {issues_desc} - Refining...")
        
        # Try to refine
        refined = self._refine_question(question_data, level, issues_desc)
        
        # Check refined version
        refined_checks = self._validate_question_quality(refined, content, level)
        if refined_checks['overall_pass']:
            print(f"[{level.upper()}] ✓ Refined question passed quality checks")
            return refined
        elif retry_count < max_retries:
            print(f"[{level.upper()}] Refined question still has issues, retrying from scratch...")
            return self._generate_question_with_quality_check(content, level, context, content_summary, retry_count + 1)
        else:
            print(f"[{level.upper()}] Returning refined version despite issues")
            return refined


def _enhance_prompt_with_examples(self, level: str) -> str:
    """
    Get enhanced prompt with REAL WORLD EXAMPLES of good distractors
    """
    examples = {
        'unistructural': """
EXAMPLE OF GOOD UNISTRUCTURAL QUESTION:

Question: "In photosynthesis, what is the primary role of chlorophyll?"
A) To store glucose produced by the plant
B) To absorb light energy from the sun ← CORRECT
C) To convert water into oxygen molecules
D) To transport nutrients through the plant

Why this is GOOD:
- All distractors mention real photosynthesis components (glucose, water, oxygen, nutrients)
- Each distractor reflects a real misconception students have
- Not obvious by process of elimination
- Student MUST understand chlorophyll's actual role to get it right
""",
        'multistructural': """
EXAMPLE OF GOOD MULTISTRUCTURAL QUESTION:

Question: "Which of the following are characteristics of mammals? (Select all that apply)"
A) Have backbones, produce milk, regulate body temperature ← CORRECT
B) Have backbones, lay eggs, produce milk
C) Produce milk, lay eggs, breathe with lungs
D) Regulate body temperature, have backbones, breathe with gills

Why this is GOOD:
- Correct answer has all TRUE components (all mammals have these)
- Each distractor mixes 2-3 real components but includes 1 WRONG one
- Option B: correct + wrong (birds lay eggs, not mammals)
- Option C: correct + correct + wrong (yes to first two, but lungs not unique to mammals in this list)
- Student must verify EACH component, not just recognize keywords
""",
        'relational': """
EXAMPLE OF GOOD RELATIONAL QUESTION:

Question: "Why does increasing temperature cause an increase in reaction rate in most chemical reactions?"
A) Higher temperature increases molecular kinetic energy, leading to more frequent and energetic collisions ← CORRECT
B) Higher temperature causes molecules to expand in size, making collisions more likely
C) Higher temperature increases the amount of reactants available for the reaction
D) Higher temperature changes the chemical structure of the reactants

Why this is GOOD:
- Tests understanding of HOW temperature relates to reaction rate (mechanism)
- Correct answer explains the RELATIONSHIP and CAUSATION
- Option B: partially true but incomplete (size expansion not the real reason)
- Option C: confuses quantity with rate
- Option D: confuses structure change with speed change
- Student must understand the MECHANISM, not just know the fact
""",
        'extended_abstract': """
EXAMPLE OF GOOD EXTENDED_ABSTRACT QUESTION:

Question: "A new disease emerges that spreads rapidly through airborne transmission. Based on principles of epidemiology and vaccination, what would be the BEST immediate response?"
A) Develop vaccines quickly and prioritize healthcare workers and vulnerable populations ← CORRECT
B) Immediately quarantine all infected individuals regardless of disease severity
C) Distribute antimicrobial drugs to everyone prophylactically
D) Close all international borders completely until vaccine is available

Why this is GOOD:
- NOT directly from course material - requires applying learned principles
- Correct answer applies multiple learned concepts (herd immunity, risk stratification, vaccination priority)
- Option B: follows logic but ignores resource constraints and pragmatic epidemiology
- Option C: misapplies treatment vs prevention concepts
- Option D: extreme response that ignores other epidemiological strategies
- Student must THINK through principles, not recall facts
"""
    }
    
    return examples.get(level, "")
