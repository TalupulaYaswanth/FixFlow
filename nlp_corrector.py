"""
FixFlow: Smart Text Correction Powered by Dynamic Programming & NLP
Module: nlp_corrector.py

This module provides:
1. Rule-based & heuristic Grammar and Syntax correction engine (zero external dependencies).
2. Tone Polishing engine (Formal, Casual, Professional, Concise).
3. Optional Google GenAI SDK (Gemini) / LLM Transformer pipeline integration.
"""

import os
import re
from typing import List, Dict, Tuple, Optional


# ===========================================================================
# 1. Grammar & Syntax Rules (Heuristics & Pattern Transformations)
# ===========================================================================

# Common homophone and confusion context patterns: (regex_pattern, replacement, reason)
GRAMMAR_PATTERNS: List[Tuple[str, str, str]] = [
    # Indefinite article 'a' vs 'an'
    (r'\b[aA]\s+([aeiouAEIOU]\w+)', r'an \1', "Use 'an' before vowel sounds"),
    (r'\b[aA]n\s+([^aeiouAEIOU\s\W]\w*)', r'a \1', "Use 'a' before consonant sounds"),
    (r'\b[aA]\s+(hour|honest|honor)\b', r'an \1', "Use 'an' before silent 'h'"),
    (r'\b[aA]n\s+(university|uniform|unique|user)\b', r'a \1', "Use 'a' before 'yu' vowel sounds"),

    # Subject-verb agreement (singular/plural)
    (r'\b(he|she|it|this|that|everyone|everybody|someone)\s+do\b', r'\1 does', "Subject-verb agreement: singular subject requires 'does'"),
    (r'\b(he|she|it|this|that)\s+have\b', r'\1 has', "Subject-verb agreement: singular subject requires 'has'"),
    (r'\b(he|she|it|this|that)\s+dont\b', r"\1 doesn't", "Subject-verb agreement: use 'doesn\'t' with singular subjects"),
    (r'\b(he|she|it|this|that)\s+don\'t\b', r"\1 doesn't", "Subject-verb agreement: use 'doesn\'t' with singular subjects"),
    (r'\b(they|we|you)\s+does\b', r'\1 do', "Subject-verb agreement: plural subject requires 'do'"),
    (r'\b(they|we|you)\s+has\b', r'\1 have', "Subject-verb agreement: plural subject requires 'have'"),
    (r'\b(they|we|you)\s+is\b', r'\1 are', "Subject-verb agreement: plural subject requires 'are'"),
    (r'\b(they|we|you)\s+was\b', r'\1 were', "Subject-verb agreement: plural subject requires 'were'"),
    (r'\b[iI]\s+is\b', r'I am', "Subject-verb agreement: 'I' pairs with 'am'"),
    (r'\b[iI]\s+are\b', r'I am', "Subject-verb agreement: 'I' pairs with 'am'"),

    # Contractions & missing apostrophes
    (r'\bdont\b', r"don't", "Missing apostrophe in contraction"),
    (r'\bdoesnt\b', r"doesn't", "Missing apostrophe in contraction"),
    (r'\bcant\b', r"can't", "Missing apostrophe in contraction"),
    (r'\bwont\b', r"won't", "Missing apostrophe in contraction"),
    (r'\bwouldnt\b', r"wouldn't", "Missing apostrophe in contraction"),
    (r'\bshouldnt\b', r"shouldn't", "Missing apostrophe in contraction"),
    (r'\bcouldnt\b', r"couldn't", "Missing apostrophe in contraction"),
    (r'\bisnt\b', r"isn't", "Missing apostrophe in contraction"),
    (r'\barent\b', r"aren't", "Missing apostrophe in contraction"),
    (r'\bwasnt\b', r"wasn't", "Missing apostrophe in contraction"),
    (r'\bwerent\b', r"weren't", "Missing apostrophe in contraction"),
    (r'\bhasnt\b', r"hasn't", "Missing apostrophe in contraction"),
    (r'\bhavent\b', r"haven't", "Missing apostrophe in contraction"),
    (r'\bdidnt\b', r"didn't", "Missing apostrophe in contraction"),
    (r'\bim\b', r"I'm", "Capitalization and missing apostrophe"),
    (r'\bive\b', r"I've", "Capitalization and missing apostrophe"),
    (r'\bill\b(?=\s+\w+)', r"I'll", "Contraction fix"),

    # Common confusions
    (r'\btheir\s+(going|doing|coming|making|eating|working)\b', r"they're \1", "Use 'they\'re' (they are) before present participles"),
    (r'\bthere\s+(house|car|decision|system|code|work)\b', r"their \1", "Use possessive 'their' before nouns"),
    (r'\byour\s+(welcome|right|wrong|correct|great)\b', r"you're \1", "Use contraction 'you\'re' (you are)"),
    (r'\bits\s+(a|an|the|very|important|obvious)\b', r"it's \1", "Use contraction 'it\'s' (it is)"),
    (r'\bto\s+(much|many|late|early|fast|slow)\b', r"too \1", "Use 'too' indicating excessive degree"),
    (r'\bbetter\s+then\b', r"better than", "Use 'than' for comparative degree"),
    (r'\bmore\s+then\b', r"more than", "Use 'than' for comparisons"),
    (r'\bless\s+then\b', r"less than", "Use 'than' for comparisons"),
    (r'\bpeace\s+of\s+cake\b', r"piece of cake", "Idiom correction: 'piece of cake'"),
    (r'\bcould\s+of\b', r"could have", "Informal error: replace 'could of' with 'could have'"),
    (r'\bshould\s+of\b', r"should have", "Informal error: replace 'should of' with 'should have'"),
    (r'\bwould\s+of\b', r"would have", "Informal error: replace 'would of' with 'would have'"),

    # Repeated duplicated words ("the the", "in in")
    (r'\b(\w+)\s+\1\b', r'\1', "Removed consecutive duplicated word"),
]

# Punctuation formatting rules
PUNCTUATION_FIXES: List[Tuple[str, str, str]] = [
    (r'\s+([,\.!?:;])', r'\1', "Removed whitespace before punctuation mark"),
    (r'([,\.!?:;])(?=[a-zA-Z])', r'\1 ', "Added required space after punctuation mark"),
    (r'([\.!?])\s+([a-z])', lambda m: f"{m.group(1)} {m.group(2).upper()}", "Capitalized sentence beginning"),
    (r'\b(i)\b', r'I', "Always capitalize the personal pronoun 'I'"),
]


# ===========================================================================
# 2. Tone Transformation Lexicons
# ===========================================================================

TONE_LEXICONS = {
    "formal": {
        "good": "exemplary",
        "bad": "suboptimal",
        "get": "acquire",
        "buy": "purchase",
        "help": "assist",
        "start": "commence",
        "end": "terminate",
        "make": "produce",
        "show": "demonstrate",
        "ask": "inquire",
        "tell": "inform",
        "big": "substantial",
        "a lot of": "a significant quantity of",
        "lots of": "numerous",
        "about": "approximately",
        "kids": "children",
        "boss": "supervisor",
        "smart": "astute",
        "fix": "rectify",
        "check": "verify",
        "look into": "investigate",
    },
    "professional": {
        "good": "effective",
        "bad": "inefficient",
        "get": "acquire",
        "fix": "resolve",
        "talk to": "consult with",
        "give": "provide",
        "get in touch": "connect",
        "let you know": "update you",
        "asap": "at your earliest convenience",
        "check out": "review",
        "job": "engagement",
        "meet": "convene",
        "deal with": "address",
    },
    "casual": {
        "acquire": "get",
        "purchase": "buy",
        "assist": "help",
        "commence": "start",
        "terminate": "wrap up",
        "demonstrate": "show",
        "inquire": "ask",
        "utilize": "use",
        "convene": "catch up",
        "furthermore": "also",
        "nevertheless": "still",
        "consequently": "so",
        "at your earliest convenience": "whenever you can",
    },
    "concise": {
        "in order to": "to",
        "due to the fact that": "because",
        "at this point in time": "now",
        "at the present time": "currently",
        "a large number of": "many",
        "in the event that": "if",
        "for the purpose of": "for",
        "with regard to": "regarding",
        "is able to": "can",
        "has the ability to": "can",
        "make a decision": "decide",
        "give consideration to": "consider",
    }
}


# ===========================================================================
# 3. NLP Corrector Engine
# ===========================================================================

class NLPCorrector:
    """
    Advanced text enhancement, grammar correction, and tone adjustment engine.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.genai_client = None

        if self.api_key:
            try:
                from google import genai
                self.genai_client = genai.Client(api_key=self.api_key)
            except Exception as e:
                # Graceful fallback to rule-based engine if client init fails
                self.genai_client = None

    def fix_grammar(self, text: str) -> Tuple[str, List[Dict]]:
        """
        Applies grammar, syntax, capitalization, and punctuation rules.
        Returns: (corrected_text, list_of_changes)
        """
        changes = []
        result = text

        # Capitalize first character of text if alphabetic
        if result and result[0].isalpha() and result[0].islower():
            result = result[0].upper() + result[1:]
            changes.append({
                "rule": "Capitalization",
                "original": text[0],
                "replacement": result[0],
                "explanation": "Capitalized opening letter of the sentence."
            })

        # Apply Grammar Pattern Transformations
        for pattern, replacement, reason in GRAMMAR_PATTERNS:
            matches = list(re.finditer(pattern, result, flags=re.IGNORECASE))
            if matches:
                # Track each change
                for m in matches:
                    changes.append({
                        "rule": "Grammar & Syntax",
                        "original": m.group(0),
                        "replacement": re.sub(pattern, replacement, m.group(0), flags=re.IGNORECASE),
                        "explanation": reason
                    })
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        # Apply Punctuation & Capitalization Fixes
        for pattern, replacement, reason in PUNCTUATION_FIXES:
            matches = list(re.finditer(pattern, result))
            if matches:
                for m in matches:
                    changes.append({
                        "rule": "Punctuation & Formatting",
                        "original": m.group(0),
                        "replacement": re.sub(pattern, replacement, m.group(0)) if isinstance(replacement, str) else replacement(m),
                        "explanation": reason
                    })
                result = re.sub(pattern, replacement, result)

        # Ensure sentence terminates with closing punctuation
        trimmed = result.strip()
        if trimmed and trimmed[-1] not in ".!?":
            trimmed += "."
            changes.append({
                "rule": "Terminal Punctuation",
                "original": "",
                "replacement": ".",
                "explanation": "Added terminal period."
            })
            result = trimmed

        return result, changes

    def polish_tone(self, text: str, target_tone: str = "formal") -> Tuple[str, List[Dict]]:
        """
        Transforms text vocabulary and style into target tone:
        'formal', 'professional', 'casual', 'concise'.
        """
        tone_key = target_tone.lower()
        lexicon = TONE_LEXICONS.get(tone_key, TONE_LEXICONS["formal"])
        changes = []
        result = text

        # Check multi-word phrases first, then single words
        sorted_phrases = sorted(lexicon.keys(), key=lambda k: len(k.split()), reverse=True)

        for phrase in sorted_phrases:
            replacement = lexicon[phrase]
            pattern = rf'\b{re.escape(phrase)}\b'
            matches = list(re.finditer(pattern, result, flags=re.IGNORECASE))
            if matches:
                for m in matches:
                    matched_text = m.group(0)
                    # Preserve title case if needed
                    rep = replacement.capitalize() if matched_text.istitle() else replacement
                    changes.append({
                        "rule": f"Tone Adjustment ({tone_key.capitalize()})",
                        "original": matched_text,
                        "replacement": rep,
                        "explanation": f"Substituted with '{rep}' for a {tone_key} tone."
                    })
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        # Run grammar cleanup pass on polished text
        result, grammar_changes = self.fix_grammar(result)
        changes.extend(grammar_changes)

        return result, changes

    def correct_with_llm(self, text: str, mode: str = "grammar", tone: str = "formal") -> Optional[Tuple[str, List[Dict]]]:
        """
        Uses Google GenAI SDK (Gemini) if API key is configured.
        """
        if not self.genai_client:
            return None

        prompt = (
            f"You are FixFlow, an expert linguistic editor.\n"
            f"Target Mode: {mode}\n"
            f"Target Tone: {tone}\n"
            f"Input Text: \"{text}\"\n\n"
            f"Instructions:\n"
            f"1. Return ONLY the polished, corrected text directly.\n"
            f"2. Maintain original intent while fixing all grammar, spelling, and tone issues.\n"
            f"3. Do not include markdown quotes, introductory pleasantries, or explanations."
        )

        try:
            response = self.genai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            corrected = response.text.strip()
            changes = [{
                "rule": "GenAI LLM Enhancement",
                "original": text,
                "replacement": corrected,
                "explanation": f"Enhanced using Gemini LLM in '{mode}' mode."
            }]
            return corrected, changes
        except Exception:
            return None
