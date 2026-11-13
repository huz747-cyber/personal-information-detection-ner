"""
Malaysian Recognizers and Gazetteers Package.
"""

from .mykad_recognizer import find_mykad_entities, mask_mykad, validate_mykad_parts
from .phone_recognizer import find_phone_entities
from .org_gazetteer import find_malaysian_org_entities
from .title_recognizer import find_malaysian_titles, purge_title_false_positives
from .location_recognizer import find_malaysian_postcodes, find_malaysian_locations
from .conflict_resolver import resolve_entity_conflicts

__all__ = [
    "find_mykad_entities",
    "mask_mykad",
    "validate_mykad_parts",
    "find_phone_entities",
    "find_malaysian_org_entities",
    "find_malaysian_titles",
    "purge_title_false_positives",
    "find_malaysian_postcodes",
    "find_malaysian_locations",
    "resolve_entity_conflicts",
]
