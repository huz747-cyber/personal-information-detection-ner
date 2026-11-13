"""
Personal Information Detection using Named Entity Recognition (NER).
"""

from .entity_extractor import PersonalInformationDetector
from .patronymic_stitcher import stitch_patronymic_entities
from .recognizers import (
    find_mykad_entities,
    find_phone_entities,
    find_malaysian_org_entities,
    find_malaysian_titles,
    find_malaysian_postcodes,
    find_malaysian_locations,
    resolve_entity_conflicts,
    mask_mykad,
)

__all__ = [
    "PersonalInformationDetector",
    "stitch_patronymic_entities",
    "find_mykad_entities",
    "find_phone_entities",
    "find_malaysian_org_entities",
    "find_malaysian_titles",
    "find_malaysian_postcodes",
    "find_malaysian_locations",
    "resolve_entity_conflicts",
    "mask_mykad",
]
