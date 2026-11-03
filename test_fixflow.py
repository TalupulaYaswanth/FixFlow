"""
Unit and Integration Tests for FixFlow (Updated with Documents, Emails, Prompts)
Module: test_fixflow.py
"""

import unittest
import io
from dp_corrector import (
    levenshtein_distance,
    levenshtein_matrix,
    lcs_diff,
    DPCorrector,
    viterbi_context_corrector
)
from nlp_corrector import NLPCorrector
from prompt_optimizer import PromptOptimizer
from document_parser import parse_uploaded_file
from fastapi.testclient import TestClient
from main import app


class TestDynamicProgrammingModule(unittest.TestCase):
    def test_levenshtein_distance(self):
        self.assertEqual(levenshtein_distance("", ""), 0)
        self.assertEqual(levenshtein_distance("kitten", "sitting"), 3)
        self.assertEqual(levenshtein_distance("flaw", "lawn"), 2)
        self.assertEqual(levenshtein_distance("intention", "execution"), 5)
        self.assertEqual(levenshtein_distance("same", "same"), 0)

    def test_levenshtein_matrix(self):
        mat = levenshtein_matrix("cat", "hat")
        self.assertEqual(len(mat), 4)
        self.assertEqual(len(mat[0]), 4)
        self.assertEqual(mat[3][3], 1)

    def test_lcs_diff(self):
        diff = lcs_diff("the quik brown fox", "the quick brown fox", mode="word")
        ops = [op for op, val in diff]
        self.assertIn("delete", ops)
        self.assertIn("insert", ops)
        self.assertIn("equal", ops)

    def test_dp_corrector_suggestions(self):
        corrector = DPCorrector()
        suggs = corrector.get_suggestions("progranning", k=3)
        self.assertTrue(len(suggs) > 0)
        self.assertEqual(suggs[0][0].lower(), "programming")


class TestNLPModule(unittest.TestCase):
    def setUp(self):
        self.nlp = NLPCorrector()

    def test_grammar_corrections(self):
        text = "he dont have a apple and they is here"
        corrected, changes = self.nlp.fix_grammar(text)
        self.assertIn("doesn't", corrected)
        self.assertIn("an apple", corrected)
        self.assertIn("they are", corrected)


class TestPromptOptimizer(unittest.TestCase):
    def setUp(self):
        self.dp = DPCorrector()
        self.nlp = NLPCorrector()
        self.opt = PromptOptimizer(self.dp, self.nlp)

    def test_email_optimizer(self):
        email_res, changes = self.opt.optimize_email(
            subject="project milestone and dynmic programing",
            body="he dont have time to review this asap in order to get good results",
            salutation="Hi Team,",
            signoff="Best regards,",
            email_tone="professional"
        )
        self.assertIn("Milestone", email_res["subject"])
        self.assertIn("doesn't", email_res["body"])
        self.assertIn("acquire", email_res["body"].lower())

    def test_ai_prompt_optimizer(self):
        raw = "write a python script with dynmic programing"
        structured, changes = self.opt.optimize_ai_prompt(raw, target_model="Gemini 2.5")
        self.assertIn("# Role & Persona", structured)
        self.assertIn("# Task Objective", structured)
        self.assertIn("programming", structured.lower())

    def test_presentation_slides_optimizer(self):
        slides = "• quik brown fox\n• he dont have any errors"
        polished, changes = self.opt.optimize_presentation_slides(slides)
        self.assertIn("Quick", polished)
        self.assertIn("doesn't", polished)


class TestDocumentParser(unittest.TestCase):
    def test_text_file_parsing(self):
        sample_bytes = b"Hello world! This is a test file for FixFlow."
        text, ftype, meta = parse_uploaded_file("sample.txt", sample_bytes)
        self.assertEqual(ftype, "text")
        self.assertIn("Hello world", text)

    def test_pptx_generation_and_parsing(self):
        from pptx import Presentation
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        slide.shapes.title.text = "FixFlow Presentation"
        slide.placeholders[1].text = "Testing automated slide extraction."

        stream = io.BytesIO()
        prs.save(stream)
        pptx_bytes = stream.getvalue()

        text, ftype, meta = parse_uploaded_file("test_deck.pptx", pptx_bytes)
        self.assertEqual(ftype, "pptx")
        self.assertEqual(meta["total_slides"], 1)
        self.assertIn("FixFlow Presentation", text)


class TestFastAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(".pptx", resp.json()["supported_file_types"])

    def test_optimize_email_endpoint(self):
        payload = {
            "subject": "project update",
            "body": "he dont have an issue with this",
            "salutation": "Hi Team,",
            "signoff": "Best regards,",
            "tone": "professional"
        }
        resp = self.client.post("/optimize/email", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("optimized_email", data)


if __name__ == "__main__":
    unittest.main()
