import frappe
import torch
import argparse
import re
from ai4bharat.transliteration import XlitEngine

# Add argparse.Namespace to safe globals
torch.serialization.add_safe_globals([argparse.Namespace])

# Initialize engines with different configurations for more phonetic variations
_engine_basic = XlitEngine("ml", beam_width=15, rescore=False)
_engine_advanced = None  # Will be initialized on demand with rescore=True

def preprocess_name(name: str) -> str:
    """Clean name for phonetic transliteration"""
    name = name.lower().strip()
    # Remove special characters except spaces and hyphens
    name = re.sub(r'[^a-zA-Z\s\-]', '', name)
    return name

def generate_phonetic_variations(word: str) -> list:
    """Generate phonetic variations of the input word for transliteration"""
    variations = [word]
    
    # Common phonetic variations in pronunciation
    phonetic_maps = [
        # Vowel variations
        {'a': 'aa', 'i': 'ee', 'u': 'oo', 'e': 'ae', 'o': 'au'},
        {'aa': 'a', 'ee': 'i', 'oo': 'u', 'ae': 'e', 'au': 'o'},
        
        # Consonant variations
        {'ph': 'f', 'gh': 'g', 'ch': 'sh', 'th': 'dh'},
        {'ck': 'k', 'qu': 'kw', 'x': 'ks'},
        
        # Double consonants
        {'ll': 'l', 'nn': 'n', 'mm': 'm', 'ss': 's', 'tt': 't'},
        {'l': 'll', 'n': 'nn', 'm': 'mm', 's': 'ss', 't': 'tt'},
        
        # Soft/hard consonant variations
        {'b': 'p', 'p': 'b', 'd': 't', 't': 'd', 'g': 'k', 'k': 'g'},
        {'v': 'w', 'w': 'v', 'j': 'y', 'y': 'j'},
        
        # Aspirated variations
        {'k': 'kh', 'g': 'gh', 't': 'th', 'd': 'dh', 'p': 'ph', 'b': 'bh'},
        
        # Ending variations
        {'y': 'i', 'i': 'y', 'ie': 'y', 'y': 'ie'}
    ]
    
    for phone_map in phonetic_maps:
        for original, replacement in phone_map.items():
            if original in word:
                variant = word.replace(original, replacement)
                if variant != word and variant not in variations:
                    variations.append(variant)
    
    return variations

def transliterate_single_word(word: str, engine, target_count: int = 5):
    """Get exactly target_count phonetic transliterations"""
    processed_word = preprocess_name(word)
    candidates = []
    
    try:
        # Get primary transliteration with high beam width
        out = engine.translit_word(processed_word, topk=target_count * 2)
        primary_candidates = out.get("ml", [])
        
        # Add primary candidates
        for candidate in primary_candidates:
            if candidate and candidate not in candidates:
                candidates.append(candidate)
        
        # If we need more candidates, try phonetic variations
        if len(candidates) < target_count:
            phonetic_vars = generate_phonetic_variations(processed_word)
            
            for variant in phonetic_vars:
                if len(candidates) >= target_count:
                    break
                    
                try:
                    var_out = engine.translit_word(variant, topk=3)
                    var_candidates = var_out.get("ml", [])
                    
                    for candidate in var_candidates:
                        if candidate and candidate not in candidates:
                            candidates.append(candidate)
                            if len(candidates) >= target_count:
                                break
                except:
                    continue
        
        # If still need more, try with different engine parameters
        if len(candidates) < target_count:
            # Try with different beam widths
            for beam_width in [20, 25, 30]:
                if len(candidates) >= target_count:
                    break
                    
                try:
                    temp_engine = XlitEngine("ml", beam_width=beam_width, rescore=False)
                    out = temp_engine.translit_word(processed_word, topk=target_count)
                    temp_candidates = out.get("ml", [])
                    
                    for candidate in temp_candidates:
                        if candidate and candidate not in candidates:
                            candidates.append(candidate)
                            if len(candidates) >= target_count:
                                break
                except:
                    continue
        
        # Ensure we have exactly target_count candidates
        if len(candidates) < target_count:
            # Try rescoring engine as last resort
            try:
                if not hasattr(transliterate_single_word, '_rescore_engine'):
                    transliterate_single_word._rescore_engine = XlitEngine("ml", beam_width=20, rescore=True)
                
                rescore_out = transliterate_single_word._rescore_engine.translit_word(processed_word, topk=target_count * 2)
                rescore_candidates = rescore_out.get("ml", [])
                
                for candidate in rescore_candidates:
                    if candidate and candidate not in candidates:
                        candidates.append(candidate)
                        if len(candidates) >= target_count:
                            break
            except:
                pass
        
        # If we still don't have enough, pad with the best available
        while len(candidates) < target_count:
            if candidates:
                # Add slight variations by trying different phonetic spellings
                base = candidates[0]
                candidates.append(base)
            else:
                # Absolute fallback - just add the original word
                candidates.append(processed_word)
        
        return candidates[:target_count]
        
    except Exception as e:
        frappe.log_error(f"Transliteration error for '{word}': {str(e)}")
        # Return the original word repeated if all else fails
        return [processed_word] * target_count

@frappe.whitelist()
def transliterate_name(name: str, topk: int = 5, use_advanced: bool = False):
    """
    Pure phonetic transliteration: English → Malayalam
    Returns exactly 5 phonetic variations based on sound
    """
    if not name or not name.strip():
        return {"original": name, "transliterated": "", "candidates": []}
    
    # Always return exactly 5 candidates
    topk = 5
    
    # Choose engine
    if use_advanced:
        global _engine_advanced
        if _engine_advanced is None:
            _engine_advanced = XlitEngine("ml", beam_width=20, rescore=True)
        engine = _engine_advanced
    else:
        engine = _engine_basic
    
    try:
        name_parts = name.strip().split()
        
        if len(name_parts) == 1:
            # Single word - get 5 phonetic variations
            candidates = transliterate_single_word(name_parts[0], engine, topk)
            
            return {
                "original": name,
                "transliterated": candidates[0] if candidates else "",
                "candidates": candidates[:topk],
                "method": "phonetic_" + ("advanced" if use_advanced else "basic")
            }
        
        else:
            # Multiple words - combine phonetic variations
            part_candidates = []
            for part in name_parts:
                # Get fewer candidates per part to create combinations
                part_vars = transliterate_single_word(part, engine, 3)
                part_candidates.append(part_vars)
            
            # Generate combinations
            combinations = []
            
            # Method 1: Best of each part
            if part_candidates:
                for i in range(min(3, len(part_candidates[0]))):
                    combination_parts = []
                    for part_vars in part_candidates:
                        if i < len(part_vars):
                            combination_parts.append(part_vars[i])
                        else:
                            combination_parts.append(part_vars[0])
                    
                    combination = " ".join(combination_parts)
                    if combination not in combinations:
                        combinations.append(combination)
            
            # Method 2: Cross combinations for remaining slots
            from itertools import product
            if len(combinations) < topk and len(part_candidates) >= 2:
                # Limit to prevent explosion
                limited_parts = [part[:2] for part in part_candidates]
                
                for combo in product(*limited_parts):
                    full_combo = " ".join(combo)
                    if full_combo not in combinations:
                        combinations.append(full_combo)
                        if len(combinations) >= topk:
                            break
            
            # Ensure exactly topk combinations
            while len(combinations) < topk:
                if combinations:
                    combinations.append(combinations[0])
                else:
                    combinations.append(" ".join(name_parts))
            
            return {
                "original": name,
                "transliterated": combinations[0] if combinations else "",
                "candidates": combinations[:topk],
                "method": "phonetic_" + ("advanced" if use_advanced else "basic")
            }
            
    except Exception as e:
        frappe.log_error(f"Transliteration error for '{name}': {str(e)}")
        return {
            "original": name, 
            "transliterated": name,
            "candidates": [name] * topk,
            "error": str(e)
        }

@frappe.whitelist()
def transliterate_name_smart(name: str):
    """
    Smart phonetic transliteration - tries basic first, then advanced
    Returns exactly 5 phonetic sound-based candidates
    """
    # Try basic engine first
    basic_result = transliterate_name(name, topk=5, use_advanced=False)
    
    # Check if we have good diversity in basic results
    candidates = basic_result.get("candidates", [])
    unique_candidates = len(set(candidates))
    
    # If basic gives good diversity, use it
    if unique_candidates >= 3:
        return basic_result
    
    # Otherwise try advanced engine
    try:
        advanced_result = transliterate_name(name, topk=5, use_advanced=True)
        advanced_result["method"] = "phonetic_smart_hybrid"
        return advanced_result
    except Exception as e:
        # Fall back to basic if advanced fails
        basic_result["fallback_reason"] = str(e)
        return basic_result

@frappe.whitelist()
def batch_transliterate_names(names: list, use_advanced: bool = False):
    """
    Batch transliterate multiple names
    Returns exactly 5 phonetic candidates per name
    """
    results = []
    for name in names:
        result = transliterate_name(name, topk=5, use_advanced=use_advanced)
        results.append(result)
    
    return {"results": results, "total": len(names)}

@frappe.whitelist()
def test_phonetic_transliteration(test_names: list = None):
    """Test function to verify 5 phonetic candidates are returned"""
    if not test_names:
        test_names = ["John", "Mary", "Priya", "Ravi", "Abdul"]
    
    results = []
    for name in test_names:
        result = transliterate_name_smart(name)
        results.append({
            "name": name,
            "candidate_count": len(result.get("candidates", [])),
            "candidates": result.get("candidates", []),
            "unique_count": len(set(result.get("candidates", [])))
        })
    
    return results