"""LLM processing helper for document categorization using Ollama models."""

import json
from typing import Dict, List, Any, Tuple, Optional

from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from database.db_models import create_connection


# ----------------------------------------------------------------------
# 1. Helper functions
# ----------------------------------------------------------------------

def safe_json_loads(value, default=None):
    """Safely parse JSON, return default on failure."""
    if default is None:
        default = []
    if not value:
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        print(f"Warning: Invalid JSON in keywords: {value!r} → using {default}")
        return default

# ----------------------------------------------------------------------
# 1. Database helpers (unchanged)
# ----------------------------------------------------------------------
def get_available_llm_models() -> List[Dict[str, Any]]:
    """Get all active LLM models from the database."""
    conn = create_connection()
    cursor = conn.cursor()

    query = """
        SELECT llm_model_uuid, system, name, is_vision_capable, default_timeout
        FROM llm_models
        WHERE is_active = 1
        ORDER BY system, name
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "llm_model_uuid": row[0],
            "system": row[1],
            "name": row[2],
            "is_vision_capable": row[3],
            "default_timeout": row[4],
        }
        for row in rows
    ]


def get_level_1_categories(organization_uuid: bytes) -> List[Dict[str, Any]]:
    conn = create_connection()
    cursor = conn.cursor()

    query = """
        SELECT category_uuid, name, description, keywords,
               use_keywords, high_min_threshold, medium_min_threshold
        FROM category
        WHERE organization_uuid = ?
          AND hierarchy_level = 1
          AND use_llm = 1
          AND is_active = 1
        ORDER BY name
    """
    cursor.execute(query, (organization_uuid,))
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "category_uuid": row[0],
            "name": row[1],
            "description": row[2],
            "keywords": safe_json_loads(row[3], []),
            "use_keywords": row[4],
            "high_min_threshold": row[5],
            "medium_min_threshold": row[6],
        }
        for row in rows
    ]


def get_level_2_categories(
    organization_uuid: bytes, parent_category_uuid: bytes
) -> List[Dict[str, Any]]:
    conn = create_connection()
    cursor = conn.cursor()

    query = """
        SELECT category_uuid, name, description, keywords,
               use_keywords, high_min_threshold, medium_min_threshold
        FROM category
        WHERE organization_uuid = ?
          AND parent_category_uuid = ?
          AND hierarchy_level = 2
          AND use_llm = 1
          AND is_active = 1
        ORDER BY name
    """
    cursor.execute(query, (organization_uuid, parent_category_uuid))
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "category_uuid": row[0],
            "name": row[1],
            "description": row[2],
            "keywords": safe_json_loads(row[3], []),
            "use_keywords": row[4],
            "high_min_threshold": row[5],
            "medium_min_threshold": row[6],
        }
        for row in rows
    ]


# ----------------------------------------------------------------------
# 2. Prompt builder 
# ----------------------------------------------------------------------
def build_categorization_prompt(
    categories: List[Dict[str, Any]],
    level: int,
    parent_category_name: Optional[str] = None,
) -> str:
    """Build the prompt for LLM categorization."""
    base_context = (
        "I'm working at a collections law firm and need to categorize the following physical piece of mail "
        "which was scanned into a PDF file. The quality of these PDFs vary between files. "
    )

    if level == 2 and parent_category_name:
        base_context += (
            f"This document has already been categorized as '{parent_category_name}' "
            "and I need more specific categorization. "
        )

    # Category list
    category_text = f"Available Level {level} Categories:\n\n"
    for cat in categories:
        category_text += f"Category: {cat['name']}\n"
        category_text += f"Description: {cat['description']}\n"
        if cat.get("keywords") and cat.get("use_keywords"):
            category_text += f"Keywords: {', '.join(cat['keywords'])}\n"
        category_text += "\n"

    json_format = (
        "I need you return ONLY the following information as a JSON object:\n"
        "- the category selected (key name: category)\n"
        "- the confidence level as a decimal/float (key name: confidence)\n"
        "- a short description for your reasoning for choosing the category (key name: reasoning)\n\n"
        "I need this JSON object to fit perfectly to the format I described because I will be ingesting "
        "this into a database and expect the exact keys to be present.\n\n"
        "Document content:\n{document_text}"
    )

    return base_context + category_text + json_format


# ----------------------------------------------------------------------
# 3. Core LLM call
# ----------------------------------------------------------------------
def categorize_with_llm(
    model_name: str,
    document_text: str,
    categories: List[Dict[str, Any]],
    level: int,
    parent_category_name: Optional[str] = None,
    timeout: int = 60,
) -> Dict[str, Any]:
    """
    Categorize a document using an Ollama LLM model.

    Returns:
        {
            "success": bool,
            "category": str | None,
            "confidence": float,
            "reasoning": str | None,
            "model_used": str,
            "error": str | None,
        }
    """
    try:
        # 1. Initialise the Ollama LLM
        llm = OllamaLLM(model=model_name, timeout=timeout)

        # 2. Build the prompt template (only one variable)
        prompt_str = build_categorization_prompt(
            categories, level, parent_category_name
        )
        prompt = PromptTemplate.from_template(prompt_str)

        # 3. **Modern chain** – no LLMChain, just pipe
        chain = prompt | llm

        # 4. Run the chain
        raw_response: str = chain.invoke({"document_text": document_text})

        # ------------------------------------------------------------------
        # 5. Extract JSON (models sometimes wrap it in markdown)
        # ------------------------------------------------------------------
        response_text = raw_response.strip()

        # Strip possible markdown fences
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()

        result = json.loads(response_text)

        # Validate required keys
        required = {"category", "confidence", "reasoning"}
        if not required.issubset(result):
            raise ValueError(f"Missing keys; got {set(result.keys())}")

        result.update(
            {
                "model_used": model_name,
                "success": True,
                "error": None,
            }
        )
        return result

    except Exception as exc:  # pragma: no cover
        return {
            "success": False,
            "category": None,
            "confidence": 0.0,
            "reasoning": None,
            "model_used": model_name,
            "error": str(exc),
        }


# ----------------------------------------------------------------------
# 4. Document-content helpers (unchanged)
# ----------------------------------------------------------------------
def get_document_content(
    document_uuid: bytes, is_vision_capable: bool
) -> Tuple[Optional[str], Optional[bytes]]:
    """Return OCR text **or** PDF bytes depending on model capability."""
    conn = create_connection()
    cursor = conn.cursor()

    if is_vision_capable:
        query = "SELECT pdf FROM document WHERE document_uuid = ?"
        cursor.execute(query, (document_uuid,))
        row = cursor.fetchone()
        conn.close()
        return None, row[0] if row else None

    query = "SELECT ocr_text FROM document_category WHERE document_uuid = ?"
    cursor.execute(query, (document_uuid,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None, None


# ----------------------------------------------------------------------
# 5. Confidence-level helper (unchanged)
# ----------------------------------------------------------------------
def calculate_confidence_level(
    confidence: float, high_threshold: float, medium_threshold: float
) -> str:
    """Return 'high', 'medium' or 'low'."""
    if confidence >= high_threshold:
        return "high"
    if confidence >= medium_threshold:
        return "medium"
    return "low"


# ----------------------------------------------------------------------
# 6. Full pipeline (unchanged except using the new categorize_with_llm)
# ----------------------------------------------------------------------
def process_document_categorization(
    document_uuid: bytes, organization_uuid: bytes, ocr_text: str
) -> Dict[str, Any]:
    """Run level-1 then level-2 categorisation."""
    results = {
        "document_uuid": document_uuid,
        "level_1": {},
        "level_2": {},
    }

    # ---- LLM models ---------------------------------------------------
    llm_models = get_available_llm_models()
    if not llm_models:
        results["error"] = "No active LLM models available"
        return results

    # ---- Level 1 ------------------------------------------------------
    level_1_categories = get_level_1_categories(organization_uuid)
    if not level_1_categories:
        results["error"] = "No level 1 categories available"
        return results

    level_1_results = [
        categorize_with_llm(
            model_name=m["name"],
            document_text=ocr_text,
            categories=level_1_categories,
            level=1,
            timeout=m["default_timeout"],
        )
        for m in llm_models
    ]

    successful_l1 = [r for r in level_1_results if r.get("success")]
    if not successful_l1:
        results["error"] = "All level 1 attempts failed"
        return results

    best_l1 = max(successful_l1, key=lambda x: x.get("confidence", 0))
    results["level_1"] = {
        "category": best_l1["category"],
        "confidence": best_l1["confidence"],
        "reasoning": best_l1["reasoning"],
        "all_results": level_1_results,
    }

    # ---- Find parent for level 2 ---------------------------------------
    parent_cat = next(
        (c for c in level_1_categories if c["name"] == best_l1["category"]), None
    )
    if not parent_cat:
        results["error"] = "Selected level-1 category not found"
        return results

    # ---- Level 2 ------------------------------------------------------
    level_2_categories = get_level_2_categories(
        organization_uuid, parent_cat["category_uuid"]
    )
    if not level_2_categories:
        results["level_2"]["message"] = "No level-2 categories for this parent"
        return results

    level_2_results = [
        categorize_with_llm(
            model_name=m["name"],
            document_text=ocr_text,
            categories=level_2_categories,
            level=2,
            parent_category_name=best_l1["category"],
            timeout=m["default_timeout"],
        )
        for m in llm_models
    ]

    successful_l2 = [r for r in level_2_results if r.get("success")]
    if successful_l2:
        best_l2 = max(successful_l2, key=lambda x: x.get("confidence", 0))
        results["level_2"] = {
            "category": best_l2["category"],
            "confidence": best_l2["confidence"],
            "reasoning": best_l2["reasoning"],
            "all_results": level_2_results,
        }
    else:
        results["level_2"]["error"] = "All level-2 attempts failed"

    return results