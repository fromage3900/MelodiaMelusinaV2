#!/usr/bin/env python3
"""Adversarial and stress test harness for MelodiaOllamaValidation C++ token parsing logic.

Mirrors the exact parsing and tokenization behavior in:
Source/BS_GodFile/MelodiaIntegration/MelodiaOllamaValidation.cpp
"""
from __future__ import annotations

import unittest

DELIMITERS = set(" \t\r\n.,;:!?\'\"()[]{}")


def tokenize_unreal(text: str) -> list[str]:
    """Exact emulation of UE5 ParseIntoArray(Tokens, TEXT(" \\t\\r\\n.,;:!?\'\"()[]{}"), true) with ToLower."""
    tokens: list[str] = []
    current_token: list[str] = []
    for char in text.lower():
        if char in DELIMITERS:
            if current_token:
                tokens.append("".join(current_token))
                current_token = []
        else:
            current_token.append(char)
    if current_token:
        tokens.append("".join(current_token))
    return tokens


def evaluate_ollama_validation_reply(model_reply: str) -> bool:
    """Exact emulation of MelodiaOllamaValidation::ValidateMessageAsync response parser."""
    trimmed = model_reply.strip()
    tokens = tokenize_unreal(trimmed)

    b_found_valid = False
    b_found_invalid = False

    for idx, token in enumerate(tokens):
        if token in ("invalid", "false"):
            b_found_invalid = True
            break
        if token == "not" and (idx + 1 < len(tokens)) and tokens[idx + 1] == "valid":
            b_found_invalid = True
            break
        if token in ("valid", "true"):
            b_found_valid = True

    return b_found_valid and not b_found_invalid


class MelodiaOllamaValidationStressTests(unittest.TestCase):
    def test_authoritative_prompt_test_vectors(self):
        """Verify the exact vectors specified in the task assignment."""
        self.assertFalse(evaluate_ollama_validation_reply("invalid"), "invalid must evaluate to False")
        self.assertTrue(evaluate_ollama_validation_reply("VALID"), "VALID must evaluate to True")
        self.assertFalse(evaluate_ollama_validation_reply("not valid"), "not valid must evaluate to False")
        self.assertFalse(evaluate_ollama_validation_reply("validity"), "validity must evaluate to False (fail-closed)")
        self.assertFalse(evaluate_ollama_validation_reply("The intent is invalid."), "The intent is invalid. must evaluate to False")
        self.assertTrue(evaluate_ollama_validation_reply("valid: true"), "valid: true must evaluate to True")

    def test_affirmative_cases(self):
        self.assertTrue(evaluate_ollama_validation_reply("valid"))
        self.assertTrue(evaluate_ollama_validation_reply("Valid"))
        self.assertTrue(evaluate_ollama_validation_reply("true"))
        self.assertTrue(evaluate_ollama_validation_reply("TRUE"))
        self.assertTrue(evaluate_ollama_validation_reply("The intent is valid."))
        self.assertTrue(evaluate_ollama_validation_reply("This is a valid Melodia intent."))
        self.assertTrue(evaluate_ollama_validation_reply("Answer: VALID"))
        self.assertTrue(evaluate_ollama_validation_reply('{"valid": true}'))
        self.assertTrue(evaluate_ollama_validation_reply("[valid]"))
        self.assertTrue(evaluate_ollama_validation_reply("(VALID!)"))
        self.assertTrue(evaluate_ollama_validation_reply('"valid"'))

    def test_negative_cases(self):
        self.assertFalse(evaluate_ollama_validation_reply("invalid"))
        self.assertFalse(evaluate_ollama_validation_reply("Invalid"))
        self.assertFalse(evaluate_ollama_validation_reply("INVALID"))
        self.assertFalse(evaluate_ollama_validation_reply("false"))
        self.assertFalse(evaluate_ollama_validation_reply("FALSE"))
        self.assertFalse(evaluate_ollama_validation_reply("not valid"))
        self.assertFalse(evaluate_ollama_validation_reply("NOT VALID"))
        self.assertFalse(evaluate_ollama_validation_reply("The intent is not valid."))
        self.assertFalse(evaluate_ollama_validation_reply("This is definitely an invalid intent."))
        self.assertFalse(evaluate_ollama_validation_reply('{"valid": false}'))
        self.assertFalse(evaluate_ollama_validation_reply('{"status": "invalid"}'))
        self.assertFalse(evaluate_ollama_validation_reply("[INVALID]"))
        self.assertFalse(evaluate_ollama_validation_reply("(not valid!)"))

    def test_substring_trap_immunity(self):
        """Confirm immunity to substring false-positives that plagued the old .Contains(TEXT('valid'))."""
        self.assertFalse(evaluate_ollama_validation_reply("invalid"))
        self.assertFalse(evaluate_ollama_validation_reply("validity"))
        self.assertFalse(evaluate_ollama_validation_reply("validation"))
        self.assertFalse(evaluate_ollama_validation_reply("validating"))
        self.assertFalse(evaluate_ollama_validation_reply("unvalidated"))
        self.assertFalse(evaluate_ollama_validation_reply("validate"))
        self.assertFalse(evaluate_ollama_validation_reply("invalidation"))

    def test_fail_closed_on_unrecognized_or_empty(self):
        """Ensure non-standard, ambiguous, or empty outputs fail closed (evaluate to False)."""
        self.assertFalse(evaluate_ollama_validation_reply(""))
        self.assertFalse(evaluate_ollama_validation_reply("   \n\t  "))
        self.assertFalse(evaluate_ollama_validation_reply("I don't know."))
        self.assertFalse(evaluate_ollama_validation_reply("Error 500: Server Busy"))
        self.assertFalse(evaluate_ollama_validation_reply("Maybe?"))
        self.assertFalse(evaluate_ollama_validation_reply("Intent parsed: 42"))

    def test_contradictory_and_compound_phrasing(self):
        """Ensure invalid or false immediately overrides or prevents valid result."""
        self.assertFalse(evaluate_ollama_validation_reply("valid: false"))
        self.assertFalse(evaluate_ollama_validation_reply("valid, but actually invalid"))
        self.assertFalse(evaluate_ollama_validation_reply("invalid even though valid was considered"))
        self.assertFalse(evaluate_ollama_validation_reply("not valid, true is incorrect"))


if __name__ == "__main__":
    unittest.main()
