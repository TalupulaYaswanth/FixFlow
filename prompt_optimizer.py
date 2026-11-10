"""
FixFlow: Smart Text Correction Powered by Dynamic Programming & NLP
Module: prompt_optimizer.py

Specialized optimizers for different text and prompt types:
- AI System & Chat Prompts (Gemini, Claude, ChatGPT)
- Business & Professional Emails
- Presentation Slide Deck (PPT) Bullet Points
- Academic & Research Papers
- Technical Documentation & Code Notes
"""

import re
from typing import Dict, Tuple, List
from dp_corrector import DPCorrector
from nlp_corrector import NLPCorrector


class PromptOptimizer:
    """
    Tailors linguistic corrections and transformations based on Prompt Type / Context.
    """

    def __init__(self, dp_engine: DPCorrector, nlp_engine: NLPCorrector):
        self.dp = dp_engine
        self.nlp = nlp_engine

    def optimize_ai_prompt(self, raw_prompt: str, target_model: str = "Universal LLM") -> Tuple[str, List[Dict]]:
        """
        Enhances raw, vague prompts into high-performance, structured AI prompts
        with explicit Role, Objective, Constraints, and Expected Output.
        """
        # Step 1: Fix spelling typos using DP
        spell_fixed, changes = self.dp.correct_text(raw_prompt)

        # Step 2: Fix grammar and syntax using NLP
        grammar_fixed, nlp_changes = self.nlp.fix_grammar(spell_fixed)
        changes.extend(nlp_changes)

        # Generate structured prompt template
        structured_prompt = (
            f"# Role & Persona\n"
            f"You are an expert specialist operating as an advanced AI assistant ({target_model}).\n\n"
            f"# Task Objective\n"
            f"{grammar_fixed}\n\n"
            f"# Execution Guidelines & Constraints\n"
            f"- Prioritize accuracy, clarity, and well-reasoned explanations.\n"
            f"- Avoid generic boilerplate; provide actionable, concrete solutions.\n"
            f"- Maintain a professional, structured tone with clean formatting.\n\n"
            f"# Output Format\n"
            f"- Deliver the final response in clean markdown with clear headings and bullet points."
        )

        changes.append({
            "rule": "AI Prompt Optimization",
            "original": raw_prompt[:40] + "...",
            "replacement": "Structured AI Prompt Architecture",
            "explanation": "Applied Prompt Engineering best practices (Role, Objective, Constraints, Output Format)."
        })

        return structured_prompt, changes

    def optimize_email(
        self,
        subject: str,
        body: str,
        salutation: str = "Hi Team,",
        signoff: str = "Best regards,",
        email_tone: str = "professional"
    ) -> Tuple[Dict[str, str], List[Dict]]:
        """
        Processes an email draft: corrects and polishes Subject, Salutation, Body, and Sign-off.
        """
        changes = []

        # 1. Polish Subject
        clean_subject = subject.strip()
        if clean_subject:
            fixed_sub, sub_changes = self.dp.correct_text(clean_subject)
            fixed_sub, g_changes = self.nlp.fix_grammar(fixed_sub)
            # Ensure title case for subject
            fixed_sub = fixed_sub.rstrip(".")
            if not fixed_sub.istitle():
                fixed_sub = " ".join(w.capitalize() if w.lower() not in {"a", "an", "the", "in", "on", "for", "and", "or"} else w for w in fixed_sub.split())
            changes.extend(sub_changes)
            changes.extend(g_changes)
        else:
            fixed_sub = "Update Regarding Project Milestone"

        # 2. Polish Body
        fixed_body, body_changes = self.dp.correct_text(body)
        fixed_body, g_body_changes = self.nlp.fix_grammar(fixed_body)
        fixed_body, tone_changes = self.nlp.polish_tone(fixed_body, target_tone=email_tone)

        changes.extend(body_changes)
        changes.extend(g_body_changes)
        changes.extend(tone_changes)

        # 3. Assemble formatted email
        full_email = f"Subject: {fixed_sub}\n\n{salutation}\n\n{fixed_body}\n\n{signoff}"

        result_dict = {
            "subject": fixed_sub,
            "salutation": salutation,
            "body": fixed_body,
            "signoff": signoff,
            "full_email": full_email
        }

        return result_dict, changes

    def optimize_presentation_slides(self, text: str) -> Tuple[str, List[Dict]]:
        """
        Polishes presentation slide text into punchy, high-impact parallel bullet points.
        """
        changes = []
        lines = text.split("\n")
        polished_lines = []

        for line in lines:
            line_str = line.strip()
            if not line_str:
                polished_lines.append("")
                continue

            # If slide header, keep intact
            if line_str.startswith("===") or line_str.startswith("#"):
                fixed_header, h_changes = self.dp.correct_text(line_str)
                polished_lines.append(fixed_header)
                changes.extend(h_changes)
                continue

            # Strip existing bullet symbols
            content = re.sub(r'^[•\-\*\d+\.\s]+', '', line_str).strip()
            if not content:
                continue

            # Run DP spelling & NLP grammar
            fixed, dp_c = self.dp.correct_text(content)
            fixed, nlp_c = self.nlp.fix_grammar(fixed)
            fixed, tone_c = self.nlp.polish_tone(fixed, target_tone="concise")

            # Remove trailing periods on slide bullets for modern executive style
            fixed = fixed.rstrip(".")
            # Ensure capitalized first letter
            if fixed:
                fixed = fixed[0].upper() + fixed[1:]

            polished_lines.append(f"• {fixed}")
            changes.extend(dp_c)
            changes.extend(nlp_c)
            changes.extend(tone_c)

        return "\n".join(polished_lines), changes
