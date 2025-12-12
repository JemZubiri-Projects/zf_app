import re

def extract_model_suffix(model_name: str) -> str:
    """
    Extracts suffix letters from model name.
    Example:
      "ZF 5000 A" -> "A"
      "ZF 5000 W" -> "W"
    """
    if not model_name:
        return None

    match = re.search(r"\b([A-Z])\b$", model_name.strip())
    return match.group(1) if match else None


def normalize_flag(flag: str) -> set[str]:
    """
    Converts a flag column name into logical tokens.

    Examples:
      "20xx / 21xx" -> {"20xx", "21xx"}
      "22xx / 23xx / W23xx" -> {"22xx", "23xx", "W23xx"}
      "A" -> {"A"}
    """
    return {f.strip() for f in flag.replace(" ", "").split("/")}


def model_matches_flag(selected_model: str, flag: str, selected_series: int) -> bool:
    """
    Determines if a given model belongs to a flag column.
    """
    suffix = extract_model_suffix(selected_model)

    for f in normalize_flag(flag):
        # Direct suffix match (A, B, W)
        if suffix and f == suffix:
            return True

        # Series group match (20xx / 21xx)
        if f.endswith("xx"):
            try:
                base = int(f[:2]) * 100
                if base <= selected_series < base + 200:
                    return True
            except ValueError:
                pass

        # W23xx → special case
        if f.startswith("W") and f[1:3].isdigit():
            base = int(f[1:3]) * 100
            if base <= selected_series < base + 100:
                return True

    return False
