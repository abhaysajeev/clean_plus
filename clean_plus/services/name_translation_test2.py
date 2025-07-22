import frappe
import torch
import argparse
import re
import traceback
from functools import lru_cache
from ai4bharat.transliteration import XlitEngine

# Patch PyTorch safe deserialization (for >= 2.6)
torch.serialization.add_safe_globals([argparse.Namespace])

# Lazy-load and cache engine
@lru_cache(maxsize=1)
def get_engine():
    try:
        return XlitEngine("ml", beam_width=5, rescore=False)
    except Exception as e:
        frappe.log_error(
            title="XlitEngine Initialization Failed",
            message=traceback.format_exc()
        )
        raise e

def preprocess_name(name: str) -> str:
    """Clean the name string for transliteration"""
    name = name.lower().strip()
    return re.sub(r'[^a-zA-Z\s\-]', '', name)

def generate_phonetic_variations(word: str) -> list:
    """Simple phonetic alternates for better coverage"""
    variations = [word]
    basic_subs = [
        ('a', 'aa'), ('i', 'ee'), ('u', 'oo'),
        ('ph', 'f'), ('ch', 'sh'), ('b', 'p'),
        ('d', 't'), ('g', 'k'), ('v', 'w'),
    ]
    for old, new in basic_subs:
        if old in word:
            var = word.replace(old, new)
            if var != word and var not in variations:
                variations.append(var)
    return variations

def transliterate_single_word(word: str, engine, topk=5):
    word = preprocess_name(word)
    candidates = []

    try:
        out = engine.translit_word(word, topk=topk * 2)
        base = out.get("ml", [])
        candidates.extend([c for c in base if c and c not in candidates])

        if len(candidates) < topk:
            for var in generate_phonetic_variations(word):
                if len(candidates) >= topk:
                    break
                try:
                    var_out = engine.translit_word(var, topk=3)
                    for cand in var_out.get("ml", []):
                        if cand not in candidates:
                            candidates.append(cand)
                            if len(candidates) >= topk:
                                break
                except Exception:
                    continue

    except Exception:
        frappe.log_error(
            title=f"Transliteration Error for '{word}'",
            message=traceback.format_exc()
        )

    while len(candidates) < topk:
        candidates.append(word)

    return candidates[:topk]

@frappe.whitelist(allow_guest=True)
def transliterate_name(name: str, topk: int = 5):
    """
    Lightweight Phonetic Transliteration API: English to Malayalam
    """
    if not name or not name.strip():
        return {"original": name, "transliterated": "", "candidates": []}

    try:
        engine = get_engine()
        parts = name.strip().split()

        if len(parts) == 1:
            cands = transliterate_single_word(parts[0], engine, topk)
            return {
                "original": name,
                "transliterated": cands[0],
                "candidates": cands,
                "method": "basic"
            }

        # Multi-word: combine top-1 of each part
        combined = []
        for part in parts:
            sub = transliterate_single_word(part, engine, 1)
            combined.append(sub[0] if sub else part)

        return {
            "original": name,
            "transliterated": " ".join(combined),
            "candidates": [" ".join(combined)],
            "method": "basic"
        }

    except Exception:
        frappe.log_error(
            title="Transliteration Failed",
            message=traceback.format_exc()
        )
        return {
            "original": name,
            "transliterated": name,
            "candidates": [name] * topk,
            "error": "Internal transliteration error"
        }
