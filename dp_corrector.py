"""
FixFlow: Smart Text Correction Powered by Dynamic Programming & NLP
Module: dp_corrector.py

This module implements core Dynamic Programming algorithms:
1. Space-Optimized Levenshtein Distance (O(min(m, n)) space).
2. Vocabulary-based Top-K Candidate Suggestion Engine.
3. Longest Common Subsequence (LCS) Diff Generator with operation tags.
4. Viterbi Algorithm for context-aware word sequence correction using Bigram probabilities.
"""

from typing import List, Tuple, Dict, Optional, Set
import re
import math
from collections import Counter


# ---------------------------------------------------------------------------
# Default English Vocabulary & Word Frequency Data (Top Common English Words)
# ---------------------------------------------------------------------------
DEFAULT_VOCABULARY: Dict[str, int] = {
    "the": 2313585, "of": 1315194, "and": 1299767, "to": 1213693, "a": 1159277,
    "in": 846944, "for": 593330, "is": 470505, "on": 467744, "that": 460022,
    "by": 418633, "this": 403083, "with": 387413, "i": 384417, "you": 356280,
    "it": 352221, "not": 351766, "or": 340770, "be": 337774, "are": 328479,
    "from": 314020, "at": 310161, "as": 306521, "your": 279910, "all": 275164,
    "have": 271587, "new": 263300, "more": 262454, "an": 251827, "was": 246162,
    "we": 242655, "will": 237934, "home": 234084, "can": 230485, "us": 224928,
    "about": 220743, "if": 219736, "page": 212153, "my": 204694, "has": 203950,
    "search": 201605, "free": 201527, "but": 199899, "our": 198202, "one": 197289,
    "other": 192801, "do": 190906, "no": 190055, "information": 189686, "time": 183549,
    "they": 182470, "site": 179902, "he": 177964, "up": 177498, "may": 174850,
    "what": 173170, "which": 172565, "their": 172288, "news": 169080, "out": 167962,
    "use": 161937, "any": 159979, "there": 157759, "see": 156544, "only": 153744,
    "so": 151521, "his": 151329, "when": 150377, "contact": 149303, "here": 146114,
    "business": 145892, "who": 145197, "web": 144306, "also": 144306, "now": 143769,
    "help": 141991, "get": 140982, "pm": 139044, "view": 138962, "online": 137673,
    "first": 136126, "am": 135805, "been": 134599, "would": 134599, "how": 131522,
    "were": 130701, "me": 130107, "services": 128260, "some": 128031, "these": 127670,
    "click": 126340, "its": 125890, "like": 125845, "service": 124538, "than": 122094,
    "find": 121004, "price": 120531, "date": 119565, "back": 118408, "top": 117852,
    "people": 117786, "had": 116491, "list": 115160, "name": 114970, "just": 114887,
    "over": 114809, "state": 114705, "year": 114254, "day": 112806, "into": 112527,
    "email": 111750, "two": 111180, "health": 110753, "world": 110629, "next": 109311,
    "used": 108523, "go": 107693, "work": 106923, "last": 106708, "most": 106394,
    "products": 105638, "music": 104719, "buy": 102839, "data": 102511, "make": 101966,
    "them": 101435, "should": 100902, "product": 100860, "system": 100796, "post": 100584,
    "her": 100346, "city": 100234, "add": 97893, "policy": 97421, "number": 97347,
    "such": 97088, "please": 96940, "available": 96602, "copyright": 95654, "support": 95088,
    "message": 93998, "after": 93684, "best": 93582, "software": 92830, "then": 92608,
    "good": 92267, "video": 92147, "well": 90919, "where": 90760, "info": 89849,
    "rights": 89569, "public": 88722, "books": 88390, "high": 88064, "school": 87471,
    "through": 87314, "each": 86968, "links": 86616, "she": 86524, "review": 86121,
    "years": 85702, "order": 85501, "very": 85223, "privacy": 85078, "book": 84438,
    "items": 84149, "company": 83944, "read": 83905, "group": 83871, "sex": 83770,
    "need": 83529, "many": 83461, "user": 83269, "said": 83124, "de": 83076,
    "does": 82898, "set": 82839, "under": 82729, "general": 82436, "research": 82064,
    "university": 81373, "january": 81145, "mail": 81093, "full": 80721, "map": 80456,
    "reviews": 80092, "program": 79848, "life": 79496, "know": 78779, "games": 78680,
    "way": 78652, "days": 78563, "management": 78377, "part": 78245, "could": 78156,
    "great": 77805, "united": 77484, "hotel": 77413, "real": 77271, "item": 76953,
    "international": 76878, "center": 76594, "ebay": 76545, "must": 76449, "store": 76356,
    "travel": 76092, "comments": 76066, "made": 75718, "development": 75525, "report": 75151,
    "off": 75143, "member": 74768, "details": 74534, "line": 74360, "terms": 74149,
    "before": 74015, "hotels": 73844, "did": 73708, "send": 73678, "right": 73602,
    "type": 73491, "because": 73356, "local": 73264, "those": 73067, "using": 72911,
    "results": 72895, "office": 72810, "education": 72659, "national": 72545, "car": 72265,
    "design": 72084, "take": 72036, "posted": 71830, "internet": 71676, "address": 71441,
    "community": 71439, "within": 71360, "states": 71277, "area": 71167, "want": 71109,
    "phone": 71097, "shipping": 70966, "reserved": 70889, "subject": 70806, "between": 70732,
    "forum": 70624, "family": 70588, "long": 70587, "based": 70440, "code": 70355,
    "show": 70271, "even": 70139, "black": 70005, "check": 69949, "special": 69805,
    "prices": 69651, "website": 69637, "index": 69408, "being": 69324, "women": 69273,
    "much": 69212, "sign": 69174, "file": 69145, "link": 69131, "open": 69115,
    "today": 69094, "technology": 68984, "south": 68910, "case": 68670, "project": 68658,
    "same": 68508, "pages": 68352, "version": 68146, "section": 68132, "own": 67990,
    "found": 67912, "sports": 67784, "house": 67683, "related": 67520, "security": 67451,
    "both": 67406, "county": 67364, "american": 67240, "photo": 67202, "game": 67117,
    "members": 66827, "power": 66750, "while": 66735, "care": 66687, "network": 66504,
    "down": 66456, "computer": 66367, "systems": 66345, "three": 66342, "total": 66297,
    "place": 66108, "end": 65997, "following": 65913, "download": 65787, "him": 65697,
    "without": 65681, "per": 65487, "access": 65452, "think": 65377, "north": 65126,
    "resources": 65047, "current": 64875, "posts": 64796, "big": 64773, "media": 64757,
    "law": 64670, "control": 64639, "water": 64619, "history": 64593, "pictures": 64491,
    "size": 64332, "art": 64278, "personal": 64264, "since": 64210, "including": 64156,
    "guide": 64070, "shop": 63989, "directory": 63884, "board": 63782, "location": 63630,
    "change": 63442, "white": 63385, "text": 63375, "small": 63261, "rating": 63148,
    "rate": 63137, "government": 63098, "children": 62969, "during": 62892, "usa": 62886,
    "return": 62796, "students": 62719, "shopping": 62711, "dynamic": 45000, "programming": 52000,
    "algorithm": 48000, "sentence": 41000, "correction": 39000, "correct": 58000, "spelling": 42000,
    "grammar": 46000, "language": 55000, "processing": 51000, "artificial": 38000, "intelligence": 49000,
    "machine": 53000, "learning": 54000, "developer": 47000, "application": 56000, "interface": 50000,
    "hello": 61000, "world": 85000, "test": 67000, "example": 68000, "sample": 59000, "simple": 62000,
    "beautiful": 45000, "awesome": 43000, "amazing": 44000, "quick": 51000, "brown": 49000,
    "fox": 42000, "jumps": 39000, "lazy": 41000, "dog": 64000, "piece": 53000, "peace": 52000,
    "cake": 47000, "weather": 53000, "whether": 52000, "receive": 56000, "definitely": 46000,
    "separate": 48000, "necessary": 47000, "accommodate": 35000, "occurrence": 34000,
    "tomorrow": 52000, "yesterday": 51000, "writing": 58000, "reading": 59000, "python": 62000,
    "don't": 250000, "doesn't": 180000, "didn't": 190000, "can't": 210000, "won't": 160000,
    "isn't": 140000, "aren't": 120000, "wasn't": 110000, "weren't": 95000, "hasn't": 90000,
    "haven't": 95000, "hadn't": 80000, "couldn't": 90000, "shouldn't": 85000, "wouldn't": 95000,
    "it's": 320000, "that's": 220000, "what's": 150000, "there's": 160000, "here's": 130000,
    "let's": 120000, "who's": 90000, "i'm": 290000, "you're": 260000, "we're": 190000,
    "they're": 180000, "i've": 170000, "you've": 130000, "we've": 140000, "they've": 110000,
    "i'll": 160000, "you'll": 120000, "he'll": 80000, "she'll": 75000, "we'll": 130000,
    "they'll": 100000, "i'd": 120000, "you'd": 90000, "he'd": 70000, "she'd": 65000,
    "we'd": 85000, "they'd": 80000, "asap": 85000, "milestone": 75000, "milestones": 70000,
    "prompt": 65000, "prompts": 60000, "slide": 60000, "slides": 65000,
    "presentation": 70000, "presentations": 65000, "document": 75000, "documents": 72000,
    "optimizer": 55000, "optimization": 60000, "structured": 62000, "guidelines": 58000,
    "persona": 50000, "effective": 78000, "acquire": 65000, "objective": 70000,
}

# Common colloquial contractions missing apostrophes
COMMON_CONTRACTIONS: Dict[str, str] = {
    "dont": "don't",
    "cant": "can't",
    "wont": "won't",
    "didnt": "didn't",
    "doesnt": "doesn't",
    "isnt": "isn't",
    "arent": "aren't",
    "wasnt": "wasn't",
    "werent": "weren't",
    "hasnt": "hasn't",
    "havent": "haven't",
    "hadnt": "hadn't",
    "couldnt": "couldn't",
    "shouldnt": "shouldn't",
    "wouldnt": "wouldn't",
    "im": "I'm",
    "ive": "I've",
    "id": "I'd",
    "youre": "you're",
    "theyre": "they're",
    "weve": "we've",
    "youve": "you've",
    "theyve": "they've",
    "thats": "that's",
    "whats": "what's",
    "theres": "there's",
    "heres": "here's",
    "lets": "let's",
}



# ===========================================================================
# 1. Space-Optimized Levenshtein Distance (Dynamic Programming)
# ===========================================================================

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Computes the Levenshtein (Edit) Distance between two strings using
    space-optimized Dynamic Programming.

    The edit distance represents the minimum number of single-character operations
    (insertions, deletions, or substitutions) required to transform s1 into s2.

    DYNAMIC PROGRAMMING FORMULATION:
    Let DP[i][j] be the edit distance between prefix s1[0...i-1] and s2[0...j-1].

    Base Cases:
      - DP[0][j] = j  (inserting j characters to match empty s1)
      - DP[i][0] = i  (deleting i characters to match empty s2)

    State Transition:
      If s1[i-1] == s2[j-1]:
          DP[i][j] = DP[i-1][j-1]                      (no cost for match)
      Else:
          DP[i][j] = 1 + min(
              DP[i-1][j],     # Deletion from s1
              DP[i][j-1],     # Insertion into s1
              DP[i-1][j-1]    # Substitution
          )

    SPACE OPTIMIZATION:
    Notice that DP[i][j] only relies on the current row DP[i] and previous row DP[i-1].
    Therefore, we can reduce space complexity from O(m * n) to O(min(m, n)) by maintaining
    only two rows and ensuring the shorter string forms the columns.

    Complexity:
      - Time:  O(len(s1) * len(s2))
      - Space: O(min(len(s1), len(s2)))
    """
    # Ensure s2 is the shorter string to minimize row buffer memory
    if len(s1) < len(s2):
        s1, s2 = s2, s1

    m, n = len(s1), len(s2)
    if n == 0:
        return m

    # previous_row stores DP[i-1][0...n]
    # Initially for i=0: [0, 1, 2, ..., n]
    previous_row = list(range(n + 1))
    current_row = [0] * (n + 1)

    for i in range(1, m + 1):
        # Base case for current row: transforming prefix s1[0...i-1] to empty s2 requires i deletions
        current_row[0] = i
        char1 = s1[i - 1]

        for j in range(1, n + 1):
            char2 = s2[j - 1]
            if char1 == char2:
                # Characters match: cost is 0
                current_row[j] = previous_row[j - 1]
            else:
                # Characters differ: take minimum of deletion, insertion, or substitution + 1
                deletion = previous_row[j]       # DP[i-1][j]
                insertion = current_row[j - 1]   # DP[i][j-1]
                substitution = previous_row[j - 1] # DP[i-1][j-1]

                current_row[j] = 1 + min(deletion, insertion, substitution)

        # Slide window: current row becomes previous row for next iteration
        previous_row, current_row = current_row, previous_row

    return previous_row[n]


def levenshtein_matrix(s1: str, s2: str) -> List[List[int]]:
    """
    Computes the full (m+1) x (n+1) DP matrix for visualization, debugging,
    or backtracking alignment paths.
    """
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],      # deletion
                    dp[i][j - 1],      # insertion
                    dp[i - 1][j - 1]   # substitution
                )
    return dp


# ===========================================================================
# 2. Vocabulary-Based Candidate Suggestion Generator
# ===========================================================================

class DPCorrector:
    """
    Spell correction engine powered by Dynamic Programming and Lexical Statistics.
    """

    def __init__(self, vocabulary: Optional[Dict[str, int]] = None):
        """
        Initializes the corrector with a frequency dictionary {word: count}.
        """
        self.vocab = vocabulary if vocabulary is not None else DEFAULT_VOCABULARY
        # Compute maximum frequency for normalization
        self.max_freq = max(self.vocab.values()) if self.vocab else 1
        # Set of known lowercase words for fast O(1) membership check
        self.known_words = set(self.vocab.keys())

    def is_known(self, word: str) -> bool:
        """Returns True if the word is in the known vocabulary."""
        return word.lower() in self.known_words

    def get_suggestions(
        self,
        word: str,
        k: int = 3,
        max_distance: int = 3
    ) -> List[Tuple[str, int, float]]:
        """
        Finds the top-K closest matching words from the vocabulary for a misspelled word.

        Pruning Optimization:
          Skip words whose absolute length difference exceeds max_distance, because
          edit_distance(w1, w2) >= abs(len(w1) - len(w2)).

        Ranking Metric:
          Candidates are ranked by:
            1. Minimum Levenshtein Distance (ascending)
            2. Relative Word Frequency (descending, breaking distance ties)

        Returns:
          List of tuples: (suggested_word, edit_distance, confidence_score [0.0 - 1.0])
        """
        clean_word = word.lower().strip()
        if not clean_word:
            return []

        # If already known and exact match, return as 0-distance suggestion
        if clean_word in self.known_words:
            return [(clean_word, 0, 1.0)]

        candidates = []
        word_len = len(clean_word)

        for candidate, freq in self.vocab.items():
            # Length difference bounding prune
            if abs(len(candidate) - word_len) > max_distance:
                continue

            dist = levenshtein_distance(clean_word, candidate)
            if dist <= max_distance:
                # Frequency prior weight: normalized between 0.0 and 1.0
                freq_score = math.log(freq + 1) / math.log(self.max_freq + 1)
                # Composite score: higher is better
                # Heavy penalty for distance (each distance step cuts score significantly)
                composite_score = (1.0 / (1.0 + dist)) * (0.7 + 0.3 * freq_score)
                candidates.append((candidate, dist, freq, composite_score))

        # Sort primarily by lowest distance, secondarily by highest frequency
        candidates.sort(key=lambda item: (item[1], -item[2]))

        # Take top-K and format output
        top_k = []
        for cand, dist, freq, score in candidates[:k]:
            # Preserve capitalization style of original input
            formatted_cand = self._match_case(word, cand)
            top_k.append((formatted_cand, dist, round(score, 3)))

        return top_k

    def correct_word(self, word: str) -> Tuple[str, bool, List[str]]:
        """
        Corrects an individual word if misspelled.
        Returns: (best_word, was_changed, top_3_alternatives)
        """
        # Preserve non-alphabetic tokens (e.g., numbers, punctuation)
        if not word.isalpha() or len(word) <= 1:
            return word, False, []

        clean = word.lower()
        if clean in self.known_words:
            return word, False, []

        suggestions = self.get_suggestions(word, k=3, max_distance=3)
        if not suggestions:
            return word, False, []

        best_word, dist, _ = suggestions[0]
        alternatives = [s[0] for s in suggestions]
        return best_word, True, alternatives

    def correct_text(self, text: str) -> Tuple[str, List[Dict]]:
        """
        Tokenizes text, corrects misspelled words using DP Levenshtein,
        and reconstructs the sentence while preserving whitespace and punctuation.

        Returns:
          - corrected_text: str
          - changes: List of dicts describing changes made
        """
        # Split tokens while retaining delimiters, keeping words with internal apostrophes intact
        tokens = re.findall(r"[a-zA-Z]+(?:'[a-zA-Z]+)?|\s+|[^\w\s]", text)
        corrected_tokens = []
        changes = []

        for token in tokens:
            if re.match(r"^[a-zA-Z]+(?:'[a-zA-Z]+)?$", token):
                clean_lower = token.lower()

                # Check contraction map first (e.g. dont -> don't)
                if clean_lower in COMMON_CONTRACTIONS:
                    replacement = COMMON_CONTRACTIONS[clean_lower]
                    formatted_cand = self._match_case(token, replacement)
                    corrected_tokens.append(formatted_cand)
                    changes.append({
                        "original": token,
                        "replacement": formatted_cand,
                        "distance": 1,
                        "alternatives": [replacement],
                        "type": "contraction_fix"
                    })
                    continue

                if clean_lower not in self.known_words:
                    suggestions = self.get_suggestions(token, k=3, max_distance=3)
                    if suggestions:
                        best_match, best_dist, _ = suggestions[0]
                        # Pruning guard: for short words (len <= 4), prevent overly aggressive deletions
                        token_len = len(token)
                        cand_len = len(best_match)
                        is_valid_replacement = True

                        if token_len <= 3 and best_dist > 1:
                            is_valid_replacement = False
                        elif token_len <= 4 and (best_dist > 1 or cand_len < token_len - 1):
                            is_valid_replacement = False
                        elif best_dist > 2:
                            is_valid_replacement = False

                        if is_valid_replacement:
                            corrected_tokens.append(best_match)
                            changes.append({
                                "original": token,
                                "replacement": best_match,
                                "distance": best_dist,
                                "alternatives": [s[0] for s in suggestions],
                                "type": "spelling_correction"
                            })
                            continue
            corrected_tokens.append(token)

        corrected_text = "".join(corrected_tokens)
        return corrected_text, changes

    @staticmethod
    def _match_case(original: str, candidate: str) -> str:
        """Transfers capitalization pattern from original word to suggested candidate."""
        if original.isupper():
            return candidate.upper()
        if original.istitle():
            return candidate.capitalize()
        return candidate


# ===========================================================================
# 3. Longest Common Subsequence (LCS) Diff Generator
# ===========================================================================

def lcs_diff(original: str, corrected: str, mode: str = "word") -> List[Tuple[str, str]]:
    """
    Computes visual diff segments between original and corrected text using
    Dynamic Programming (Longest Common Subsequence).

    Args:
      original: The source string.
      corrected: The transformed/corrected string.
      mode: 'word' for token-level diffs (recommended for natural language)
            or 'char' for character-level diffs.

    DYNAMIC PROGRAMMING FORMULATION (LCS):
    Let A and B be token sequences of length m and n.
    DP[i][j] stores the length of LCS of A[0...i-1] and B[0...j-1].

    Recurrence:
      DP[i][j] = DP[i-1][j-1] + 1                     if A[i-1] == B[j-1]
      DP[i][j] = max(DP[i-1][j], DP[i][j-1])          if A[i-1] != B[j-1]

    BACKTRACKING:
    Starting at (m, n), traverse backward to (0, 0):
      - If A[i-1] == B[j-1]: Operation is 'equal'
      - Else if DP[i-1][j] >= DP[i][j-1]: Operation is 'delete' from A
      - Else: Operation is 'insert' from B

    Returns:
      List of tuples: (operation, token)
        where operation is one of:
          - 'equal': unchanged text
          - 'delete': present in original, removed in corrected
          - 'insert': added in corrected, absent in original
    """
    if mode == "word":
        # Split on whitespace/punctuation boundaries while capturing tokens
        tokens_a = re.findall(r'\S+|\s+', original)
        tokens_b = re.findall(r'\S+|\s+', corrected)
    else:
        tokens_a = list(original)
        tokens_b = list(corrected)

    m, n = len(tokens_a), len(tokens_b)

    # Build (m+1) x (n+1) DP matrix
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if tokens_a[i - 1] == tokens_b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = dp[i - 1][j] if dp[i - 1][j] >= dp[i][j - 1] else dp[i][j - 1]

    # Backtrack from (m, n) to construct the sequence of diff operations
    diff_ops = []
    i, j = m, n

    while i > 0 or j > 0:
        if i > 0 and j > 0 and tokens_a[i - 1] == tokens_b[j - 1]:
            diff_ops.append(("equal", tokens_a[i - 1]))
            i -= 1
            j -= 1
        elif j > 0 and (i == 0 or dp[i][j - 1] >= dp[i - 1][j]):
            diff_ops.append(("insert", tokens_b[j - 1]))
            j -= 1
        elif i > 0 and (j == 0 or dp[i - 1][j] > dp[i][j - 1]):
            diff_ops.append(("delete", tokens_a[i - 1]))
            i -= 1

    # Reverse because we backtracked from end to beginning
    diff_ops.reverse()

    # Consolidate adjacent identical operations for cleaner output
    consolidated = []
    for op, val in diff_ops:
        if consolidated and consolidated[-1][0] == op:
            consolidated[-1] = (op, consolidated[-1][1] + val)
        else:
            consolidated.append((op, val))

    return consolidated


# ===========================================================================
# 4. Bonus Context Engine: Viterbi Algorithm for Sequence Correction
# ===========================================================================

# Bigram transition table for common phrases / homophone disambiguation
BIGRAM_PROBABILITIES: Dict[Tuple[str, str], float] = {
    ("piece", "of"): 0.95, ("peace", "of"): 0.05,
    ("peace", "treaty"): 0.98, ("piece", "treaty"): 0.02,
    ("weather", "is"): 0.90, ("whether", "is"): 0.10,
    ("whether", "or"): 0.97, ("weather", "or"): 0.03,
    ("their", "house"): 0.96, ("there", "house"): 0.02, ("they're", "house"): 0.02,
    ("over", "there"): 0.98, ("over", "their"): 0.02,
    ("they", "are"): 0.95, ("they're", "going"): 0.92,
    ("dynamic", "programming"): 0.99,
    ("machine", "learning"): 0.99,
    ("natural", "language"): 0.99,
    ("artificial", "intelligence"): 0.99,
    ("smart", "text"): 0.95,
}

def viterbi_context_corrector(words: List[str], corrector: DPCorrector) -> List[str]:
    """
    Applies the Viterbi Dynamic Programming Algorithm over a hidden Markov model
    to select the sequence of word candidates that maximizes joint sequence likelihood.

    States at step t: Top candidates for word t
    Transitions: Bigram probabilities P(w_t | w_{t-1})
    Emission: P(observed | candidate) derived from Levenshtein distance
    """
    if not words:
        return []

    # Step 1: Generate candidate sets for each position
    candidate_lattice = []
    for w in words:
        if corrector.is_known(w):
            candidates = [w.lower()]
        else:
            suggestions = corrector.get_suggestions(w, k=3, max_distance=2)
            candidates = [s[0].lower() for s in suggestions] if suggestions else [w.lower()]
        candidate_lattice.append((w, candidates))

    # Viterbi DP table: viterbi[t][state] = (max_log_prob, backpointer)
    viterbi = []
    # Initialize t = 0
    init_col = {}
    orig_w0, cands0 = candidate_lattice[0]
    for c in cands0:
        dist = levenshtein_distance(orig_w0.lower(), c)
        emission_prob = math.exp(-dist * 1.5)
        prior_freq = corrector.vocab.get(c, 100) / corrector.max_freq
        init_col[c] = (math.log(emission_prob) + math.log(prior_freq + 1e-6), None)
    viterbi.append(init_col)

    # Forward recurrence for t = 1 ... N-1
    for t in range(1, len(candidate_lattice)):
        orig_w, cands = candidate_lattice[t]
        curr_col = {}

        for c_curr in cands:
            dist = levenshtein_distance(orig_w.lower(), c_curr)
            emission_prob = math.exp(-dist * 1.5)
            log_emission = math.log(emission_prob)

            best_prob = -float('inf')
            best_prev = None

            for c_prev, (prev_prob, _) in viterbi[t - 1].items():
                # Bigram probability or fallback unigram
                transition = BIGRAM_PROBABILITIES.get((c_prev, c_curr), 0.01)
                total_prob = prev_prob + math.log(transition) + log_emission

                if total_prob > best_prob:
                    best_prob = total_prob
                    best_prev = c_prev

            curr_col[c_curr] = (best_prob, best_prev)
        viterbi.append(curr_col)

    # Backtracking best path
    best_final_cand = max(viterbi[-1].keys(), key=lambda c: viterbi[-1][c][0])
    path = [best_final_cand]

    for t in range(len(words) - 1, 0, -1):
        prev = viterbi[t][path[-1]][1]
        path.append(prev)

    path.reverse()

    # Restore casing
    result = []
    for orig, chosen in zip(words, path):
        result.append(DPCorrector._match_case(orig, chosen))

    return result
