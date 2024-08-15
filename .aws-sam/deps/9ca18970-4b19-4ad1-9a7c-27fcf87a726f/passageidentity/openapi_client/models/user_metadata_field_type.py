# coding: utf-8

"""
    Passage Management API

    Passage's management API to manage your Passage apps and users.

    The version of the OpenAPI document: 1
    Contact: support@passage.id
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


from __future__ import annotations
import json
import pprint
import re  # noqa: F401
from enum import Enum



try:
    from typing import Self
except ImportError:
    from typing_extensions import Self


class UserMetadataFieldType(str, Enum):
    """
    UserMetadataFieldType
    """

    """
    allowed enum values
    """
    STRING = 'string'
    BOOLEAN = 'boolean'
    INTEGER = 'integer'
    DATE = 'date'
    PHONE = 'phone'
    EMAIL = 'email'

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Create an instance of UserMetadataFieldType from a JSON string"""
        return cls(json.loads(json_str))


