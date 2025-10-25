"""
Helper functions for data ingestion and processing.
Contains CSV parsing utilities and common helper functions.
"""

import ast
import json
import pandas as pd
from typing import Any, Optional, List


def parse_json_maybe(raw: Any) -> Optional[Any]:
    """
    Return dict/list from a cell that might be JSON, a Python-literal string, or NaN.
    
    Args:
        raw: Raw data from CSV cell
        
    Returns:
        Parsed dictionary/list or None
    """
    # pandas NaN?
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None

    # already a dict/list?
    if isinstance(raw, (dict, list)):
        return raw

    s = str(raw).strip()
    if not s:
        return None

    # Try JSON first (handles proper JSON strings)
    if s[0] in "{[":
        try:
            return json.loads(s)
        except Exception:
            # Fall back to Python literal (handles single-quoted dicts/lists)
            try:
                return ast.literal_eval(s)
            except Exception:
                return None

    # If it doesn't start with { or [, still try literal_eval (sometimes quoted)
    try:
        return ast.literal_eval(s)
    except Exception:
        return None


def get_slot_formula(slot_map: Optional[dict], slot: int = 4) -> Optional[str]:
    """
    Return the formula for a specific slot level (fallback to closest lower, then lowest).
    
    Args:
        slot_map: Dictionary mapping slot levels to formulas
        slot: Target slot level
        
    Returns:
        Formula string or None
    """
    if not isinstance(slot_map, dict):
        return None
    pairs = sorted((int(k), v) for k, v in slot_map.items() if str(k).isdigit())
    if not pairs:
        return None
    for k, v in pairs:
        if k == slot:
            return v
    lowers = [v for k, v in pairs if k < slot]
    return lowers[-1] if lowers else pairs[0][1]


def extract_damage_at_slot(row: pd.Series, slot: int) -> Optional[str]:
    """
    Extract damage formula at specific slot level from CSV row.
    
    Args:
        row: Pandas Series representing a CSV row
        slot: Spell slot level
        
    Returns:
        Damage formula string or None
    """
    d = parse_json_maybe(row.get("damage"))
    if isinstance(d, dict):
        return get_slot_formula(d.get("damage_at_slot_level"), slot)
    return None


def extract_heal_at_slot(row: pd.Series, slot: int) -> Optional[str]:
    """
    Extract healing formula at specific slot level from CSV row.
    
    Args:
        row: Pandas Series representing a CSV row
        slot: Spell slot level
        
    Returns:
        Healing formula string or None
    """
    h = parse_json_maybe(row.get("heal_at_slot_level"))
    if isinstance(h, dict):
        return get_slot_formula(h, slot)
    return None


def extract_cast_class(row: pd.Series) -> List[str]:
    """
    Extract casting classes from CSV row data.
    
    Args:
        row: Pandas Series representing a CSV row
        
    Returns:
        List of class names (lowercase)
    """
    data = parse_json_maybe(row.get("classes"))
    if not isinstance(data, list):
        return []

    names = []
    seen = set()
    for item in data:
        if isinstance(item, dict):
            n = (item.get("name") or "").strip()
        elif isinstance(item, str):
            n = item.strip()
        else:
            n = ""
        if n and n.lower() not in seen:
            names.append(n.lower())
            seen.add(n.lower())
    return names


def flatten_desc(desc_raw: Any) -> str:
    """
    Flatten description data into a single string.
    
    Args:
        desc_raw: Raw description data (can be string, list, or JSON)
        
    Returns:
        Flattened description string
    """
    if desc_raw is None:
        return ""

    if isinstance(desc_raw, list):
        return "\n\n".join(str(x).strip() for x in desc_raw if str(x).strip())

    s = str(desc_raw).strip()
    if not s:
        return ""

    if s[0] in "[{":
        try:
            obj = json.loads(s)
            if isinstance(obj, list):
                return "\n\n".join(str(x).strip() for x in obj if str(x).strip())
            elif isinstance(obj, str):
                s = obj.strip()
        except Exception:
            pass

    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1].strip().strip("'\"")
        s = s.replace("', '", "\n\n").replace('", "', "\n\n")

    s = s.strip("[]'\" \n\r\t")
    return s


def read_spells_csv(csv_path: str) -> pd.DataFrame:
    """
    Read spells CSV file and return processed DataFrame.
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        Pandas DataFrame with spell data
    """
    # Read CSV file
    df = pd.read_csv(csv_path)
    
    # Keep only needed columns
    keep_cols = ["name", "classes", "desc", "damage", "heal_at_slot_level"]
    df = df[keep_cols]
    
    return df


def process_spell_row(row: pd.Series, slot_level: int = 5) -> Optional[dict]:
    """
    Process a single spell row from CSV into a standardized dictionary.
    
    Args:
        row: Pandas Series representing a CSV row
        slot_level: Spell slot level for damage/heal calculations
        
    Returns:
        Dictionary with processed spell data or None if invalid
    """
    name = str(row["name"]).strip()
    if not name:
        return None

    desc = flatten_desc(row["desc"])
    dmg = extract_damage_at_slot(row, slot_level)
    heal = extract_heal_at_slot(row, slot_level)
    cast_class_list = extract_cast_class(row)
    cast_class = ", ".join(cast_class_list) if cast_class_list else ""
    
    # Determine effect kind
    effect_kind = "none"
    if dmg:
        effect_kind = "damage"
    elif heal:
        effect_kind = "heal"

    return {
        "name": name,
        "cast_class": cast_class,
        "description": desc,
        "effect_kind": effect_kind,
        "damage": dmg or "",
        "heal": heal or ""
    }


def read_classes_csv(csv_path: str) -> pd.DataFrame:
    """
    Read classes CSV file and return processed DataFrame.
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        Pandas DataFrame with class data
    """
    # Read CSV file
    df = pd.read_csv(csv_path)
    
    # Keep only needed columns
    keep_cols = ["name", "index", "hit_die"]
    df = df[keep_cols]
    
    return df


def process_class_row(row: pd.Series) -> Optional[dict]:
    """
    Process a single class row from CSV into a standardized dictionary.
    
    Args:
        row: Pandas Series representing a CSV row
        
    Returns:
        Dictionary with processed class data or None if invalid
    """
    name = str(row["name"]).strip()
    index = str(row["index"]).strip()
    
    if not name or not index:
        return None
    
    # Get hit_die and calculate health
    try:
        hit_die = int(row["hit_die"])
        health = hit_die * 10
    except (ValueError, TypeError):
        return None
    
    return {
        "name": name,
        "index": index,
        "health": health
    }


def print_separator(title: str = "", char: str = "=", width: int = 70):
    """
    Print a visual separator line.
    
    Args:
        title: Optional title to center in the separator
        char: Character to use for the separator
        width: Width of the separator line
    """
    if title:
        print(f"\n{char * width}")
        print(f"{title:^{width}}")
        print(f"{char * width}\n")
    else:
        print(f"{char * width}\n")

