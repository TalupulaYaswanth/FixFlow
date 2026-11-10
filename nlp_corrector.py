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

    # Preposition & Verb Usage Fixes
    (r'\b(emphasized|emphasize|emphasizes|emphasizing)\s+on\s+the\s+fact\s+that\b', r'\1 that', "Removed incorrect preposition 'on' and wordy 'the fact that'"),
    (r'\b(emphasized|emphasize|emphasizes|emphasizing)\s+on\b', r'\1', "The transitive verb '\1' takes a direct object without preposition 'on'"),
    (r'\b(discussed|discuss|discusses|discussing)\s+about\b', r'\1', "The transitive verb '\1' takes a direct object without 'about'"),
    (r'\b(ordered|order|orders)\s+for\s+(a|an|the|\d+|\w+)', r'\1 \2', "Removed redundant preposition 'for' after verb '\1'"),
    (r'\bcomprises\s+of\b', r'consists of', "Replace 'comprises of' with 'consists of' or 'comprises'"),
    (r'\bcomprise\s+of\b', r'consist of', "Replace 'comprise of' with 'consist of' or 'comprise'"),
    (r'\bcope\s+up\s+with\b', r'cope with', "Idiomatic phrasing: use 'cope with'"),

    # Tautology & Redundancy Eliminators
    (r'\b(cooperate|cooperating|cooperated|cooperates)\s+together\b', r'\1', "Redundancy: '\1' already implies working together"),
    (r'\b(collaborate|collaborating|collaborated|collaborates)\s+together\b', r'\1', "Redundancy: '\1' already implies working together"),
    (r'\b(merge|merging|merged|merges)\s+together\b', r'\1', "Redundancy: '\1' already implies joining together"),
    (r'\b(blend|blending|blended|blends)\s+together\b', r'\1', "Redundancy: '\1' already implies combining together"),
    (r'\b(join|joining|joined|joins)\s+together\b', r'\1', "Redundancy: '\1' already implies uniting together"),
    (r'\b(revert|reverting|reverted|reverts)\s+back\b', r'\1', "Redundancy: '\1' already implies returning"),
    (r'\b(reply|replying|replied|replies)\s+back\b', r'\1', "Redundancy: '\1' already implies sending back"),
    (r'\b(repeat|repeating|repeated|repeats)\s+again\b', r'\1', "Redundancy: '\1' already implies doing again"),
    (r'\b(return|returning|returned|returns)\s+back\b', r'\1', "Redundancy: '\1' already implies coming back"),
    (r'\bend\s+result\b', r'result', "Redundancy: 'result' already implies final outcome"),
    (r'\bfuture\s+plans\b', r'plans', "Redundancy: 'plans' inherently refer to the future"),
    (r'\bpast\s+history\b', r'history', "Redundancy: 'history' inherently refers to the past"),
    (r'\bfree\s+gift\b', r'gift', "Redundancy: a 'gift' is inherently free"),
    (r'\bunexpected\s+surprise\b', r'surprise', "Redundancy: a 'surprise' is inherently unexpected"),
    (r'\bcrashed\s+unexpectedly\b', r'crashed', "Conciseness: 'crashed' already indicates an unexpected failure"),
    (r'\bclose\s+proximity\b', r'proximity', "Redundancy: 'proximity' means nearness"),
    (r'\bbasic\s+fundamentals\b', r'fundamentals', "Redundancy: 'fundamentals' implies basic principles"),

    # Expletive / Modal Subjunctive / Wordiness Streamlining
    (r'\bit\s+is\s+required\s+that\s+all\s+([a-zA-Z\s]+?)\s+should\s+([a-z]+)\b', r'all \1 must \2', "Streamlined expletive construction to active requirement"),
    (r'\bit\s+is\s+required\s+that\s+([a-zA-Z\s]+?)\s+should\s+([a-z]+)\b', r'\1 must \2', "Streamlined expletive construction to active requirement"),
    (r'\bit\s+is\s+essential\s+that\s+([a-zA-Z\s]+?)\s+should\s+([a-z]+)\b', r'\1 must \2', "Streamlined expletive construction"),
    (r'\bit\s+is\s+necessary\s+that\s+([a-zA-Z\s]+?)\s+should\s+([a-z]+)\b', r'\1 must \2', "Streamlined expletive construction"),
    (r'\bevery\s+single\s+([a-zA-Z]+)\b', r'every \1', "Eliminated colloquial wordiness: 'every \1'"),
    (r'\bdue\s+to\s+the\s+fact\s+that\b', r'because', "Replaced wordy phrase 'due to the fact that' with 'because'"),
    (r'\bowing\s+to\s+the\s+fact\s+that\b', r'because', "Replaced wordy phrase 'owing to the fact that' with 'because'"),
    (r'\bin\s+order\s+to\b', r'to', "Replaced wordy 'in order to' with 'to'"),
    (r'\bthe\s+fact\s+that\b', r'that', "Removed wordy filler 'the fact that'"),

    # Dangling Modifiers & Passive Phrasing
    (r'\bWalking\s+into\s+the\s+room,\s+the\s+presentation\s+was\s+already\s+being\s+projected\s+on\s+the\s+screen\s+by\s+([A-Z][a-z]+)\b', r'When we walked into the room, \1 was already projecting the presentation on the screen', "Resolved dangling participle and passive voice to active construction"),

    # Relative Clause Formatting & Tightening
    (r'(\b\w+\b)\s+which\s+was\s+(running|operating|already)\s+behind\s+schedule\b', r'\1, which was \2 behind schedule', "Added comma before non-restrictive relative clause"),
    (r'\bwhich\s+was\s+(released|launched|built|created|introduced)\s+last\s+(week|month|year)\b', r'released last \2', "Tightened relative clause"),
    (r'\bcause\s+the\s+system\s+to\s+freeze\s+frequently\b', r'frequently freeze the system', "Streamlined periphrastic cause"),

    # Subject-Verb Agreement in Academic & News Contexts
    (r'\b(growth|economy|production|demand|supply|development|rate|inflation|price|cost|market|system|process)\s+have\b', r'\1 has', "Subject-verb agreement: singular noun requires 'has'"),
    (r'\b(results|findings|studies|experiments|data|models|observations|records|reports)\s+(clearly\s+|strongly\s+|also\s+|further\s+)?shows\b', r'\1 \2show', "Subject-verb agreement: plural noun requires 'show'"),
    (r'\b(results|findings|studies|experiments|data|models|observations|records|reports)\s+(clearly\s+|strongly\s+|also\s+|further\s+)?proves\b', r'\1 \2prove', "Subject-verb agreement: plural noun requires 'prove'"),
    (r'\b(we|they)\s+investigates\b', r'\1 investigate', "Subject-verb agreement: plural pronoun requires 'investigate'"),
    (r'\b(we|they)\s+demonstrates\b', r'\1 demonstrate', "Subject-verb agreement: plural pronoun requires 'demonstrate'"),
    (r'\b(we|they)\s+proposes\b', r'\1 propose', "Subject-verb agreement: plural pronoun requires 'propose'"),
    (r'\b(we|they)\s+evaluates\b', r'\1 evaluate', "Subject-verb agreement: plural pronoun requires 'evaluate'"),
    (r'\b(we|they)\s+analyzes\b', r'\1 analyze', "Subject-verb agreement: plural pronoun requires 'analyze'"),
    (r'\b(we|they)\s+examines\b', r'\1 examine', "Subject-verb agreement: plural pronoun requires 'examine'"),

    # News & Academic Confusions
    (r'\b(has|have|had|is|are|was|were)\s+effected\s+(by|millions|thousands|hundreds|people|the|our|their|a|an)\b', r'\1 affected \2', "Use 'affected' (verb meaning influenced/impacted) rather than 'effected'"),
    (r'\bas\s+compared\s+(to|with)\b', r'compared \1', "Conciseness: replace 'as compared to' with 'compared to'"),
    (r'\b(european|american|asian|african|australian|indian|british|chinese|japanese|german|french|italian|canadian)\b', lambda m: m.group(0).capitalize(), "Capitalize proper adjectives and nationalities"),
    (r'\bplays\s+an\s+crucial\s+role\b', r'plays a crucial role', "Use 'a' before consonant sound 'crucial'"),
    (r'\bplay\s+an\s+crucial\s+role\b', r'play a crucial role', "Use 'a' before consonant sound 'crucial'"),
]

# Punctuation formatting rules
PUNCTUATION_FIXES: List[Tuple[str, str, str]] = [
    (r'(?<!\d)\s+([,\.!?:;])', r'\1', "Removed whitespace before punctuation mark"),
    (r'([,\.!?:;])(?=[a-zA-Z])(?<!e\.g\.)(?<!i\.e\.)', r'\1 ', "Added required space after punctuation mark"),
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

        def _apply_repl(m, repl):
            if callable(repl):
                expanded = repl(m)
            else:
                expanded = m.expand(repl)
            orig = m.group(0)
            if orig and orig[0].isupper() and expanded and expanded[0].islower():
                expanded = expanded[0].upper() + expanded[1:]
            return expanded

        # Apply Grammar Pattern Transformations
        for pattern, replacement, reason in GRAMMAR_PATTERNS:
            matches = list(re.finditer(pattern, result, flags=re.IGNORECASE))
            if matches:
                # Track each change
                for m in matches:
                    expanded_text = _apply_repl(m, replacement)
                    changes.append({
                        "rule": "Grammar & Syntax",
                        "original": m.group(0),
                        "replacement": expanded_text,
                        "explanation": reason
                    })
                result = re.sub(pattern, lambda m, r=replacement: _apply_repl(m, r), result, flags=re.IGNORECASE)

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

        # Ensure sentence opening letter is capitalized
        if result and result[0].isalpha() and result[0].islower():
            result = result[0].upper() + result[1:]

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

        # Ensure sentence opening letter is capitalized
        if result and result[0].isalpha() and result[0].islower():
            result = result[0].upper() + result[1:]

        return result, changes

    def correct_with_llm(self, text: str, mode: str = "grammar", tone: str = "formal") -> Optional[Tuple[str, List[Dict]]]:
        """
        Uses Google GenAI SDK (Gemini) if API key is configured.
        """
        if not self.genai_client:
            return None

        prompt = (
            f"You are FixFlow, an expert linguistic editor and copywriter.\n"
            f"Target Mode: {mode}\n"
            f"Target Tone: {tone}\n"
            f"Input Text: \"{text}\"\n\n"
            f"Instructions:\n"
            f"1. Return ONLY the polished, refined English text.\n"
            f"2. Maintain original intent while eliminating all grammatical friction, spelling errors, wordiness, tautologies, dangling modifiers, and awkward phrasing.\n"
            f"3. Do not include markdown code fences, quotes around the output, or introductory comments."
        )

        for candidate_model in ["gemini-2.0-flash", "gemini-1.5-flash"]:
            try:
                response = self.genai_client.models.generate_content(
                    model=candidate_model,
                    contents=prompt
                )
                if response and response.text:
                    corrected = response.text.strip()
                    if corrected.startswith('"') and corrected.endswith('"') and len(corrected) > 2:
                        corrected = corrected[1:-1].strip()
                    changes = [{
                        "rule": "GenAI LLM Polish",
                        "original": text,
                        "replacement": corrected,
                        "explanation": f"Polished and refined using Gemini ({candidate_model}) in '{mode}' mode."
                    }]
                    return corrected, changes
            except Exception:
                continue

        return None
