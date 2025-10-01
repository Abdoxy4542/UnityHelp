"""
JSON schemas for MCP server request/response validation
Defines standardized data structures for UnityAid humanitarian data
"""

# Base response schema
BASE_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["success", "error"]
        },
        "timestamp": {
            "type": "string",
            "format": "date-time"
        },
        "data": {
            "type": ["object", "array", "null"]
        },
        "error": {
            "type": ["string", "null"]
        },
        "metadata": {
            "type": ["object", "null"],
            "properties": {
                "current_page": {"type": "integer"},
                "total_pages": {"type": "integer"},
                "per_page": {"type": "integer"},
                "total_count": {"type": "integer"},
                "has_next": {"type": "boolean"},
                "has_previous": {"type": "boolean"}
            }
        },
        "spatial": {
            "type": ["object", "null"],
            "properties": {
                "bounds": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4
                },
                "center": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 2,
                    "maxItems": 2
                }
            }
        }
    },
    "required": ["status", "timestamp"]
}

# Common parameter schemas
PAGINATION_PARAMS_SCHEMA = {
    "type": "object",
    "properties": {
        "page": {
            "type": "integer",
            "minimum": 1,
            "default": 1
        },
        "per_page": {
            "type": "integer",
            "minimum": 1,
            "maximum": 500,
            "default": 50
        }
    }
}

SPATIAL_FILTER_PARAMS_SCHEMA = {
    "type": "object",
    "properties": {
        "bounds": {
            "type": "array",
            "items": {"type": "number"},
            "minItems": 4,
            "maxItems": 4,
            "description": "[west, south, east, north]"
        },
        "center": {
            "type": "array",
            "items": {"type": "number"},
            "minItems": 2,
            "maxItems": 2,
            "description": "[longitude, latitude]"
        },
        "radius": {
            "type": "number",
            "minimum": 0,
            "description": "Radius in kilometers"
        }
    }
}

DATE_RANGE_PARAMS_SCHEMA = {
    "type": "object",
    "properties": {
        "from_date": {
            "type": "string",
            "format": "date",
            "description": "Start date (YYYY-MM-DD)"
        },
        "to_date": {
            "type": "string",
            "format": "date",
            "description": "End date (YYYY-MM-DD)"
        }
    }
}

# Sites MCP Server Schemas
SITES_GET_ALL_SCHEMA = {
    "type": "object",
    "properties": {
        **PAGINATION_PARAMS_SCHEMA["properties"],
        **SPATIAL_FILTER_PARAMS_SCHEMA["properties"],
        **DATE_RANGE_PARAMS_SCHEMA["properties"],
        "status": {
            "type": "string",
            "enum": ["active", "inactive", "planned", "closed"]
        },
        "site_type": {
            "type": "string",
            "enum": ["camp", "settlement", "host_community", "transit_center"]
        },
        "search": {
            "type": "string",
            "description": "Search in site name or description"
        }
    }
}

SITES_GET_BY_ID_SCHEMA = {
    "type": "object",
    "properties": {
        "site_id": {
            "type": "integer",
            "minimum": 1
        },
        "include_services": {
            "type": "boolean",
            "default": True
        },
        "include_demographics": {
            "type": "boolean",
            "default": True
        }
    },
    "required": ["site_id"]
}

# Reports MCP Server Schemas
REPORTS_GET_ALL_SCHEMA = {
    "type": "object",
    "properties": {
        **PAGINATION_PARAMS_SCHEMA["properties"],
        **SPATIAL_FILTER_PARAMS_SCHEMA["properties"],
        **DATE_RANGE_PARAMS_SCHEMA["properties"],
        "site_id": {
            "type": "integer",
            "minimum": 1
        },
        "gso_id": {
            "type": "integer",
            "minimum": 1
        },
        "urgency_level": {
            "type": "string",
            "enum": ["low", "medium", "high", "critical"]
        },
        "has_media": {
            "type": "boolean"
        },
        "search": {
            "type": "string",
            "description": "Search in report content (Arabic and English)"
        }
    }
}

REPORTS_GET_BY_ID_SCHEMA = {
    "type": "object",
    "properties": {
        "report_id": {
            "type": "integer",
            "minimum": 1
        },
        "include_media": {
            "type": "boolean",
            "default": True
        }
    },
    "required": ["report_id"]
}

# Assessments MCP Server Schemas
ASSESSMENTS_GET_ALL_SCHEMA = {
    "type": "object",
    "properties": {
        **PAGINATION_PARAMS_SCHEMA["properties"],
        **DATE_RANGE_PARAMS_SCHEMA["properties"],
        "site_id": {
            "type": "integer",
            "minimum": 1
        },
        "assessment_type": {
            "type": "string"
        },
        "status": {
            "type": "string",
            "enum": ["draft", "active", "completed", "archived"]
        },
        "kobo_form_id": {
            "type": "string"
        }
    }
}

ASSESSMENTS_ANALYZE_SCHEMA = {
    "type": "object",
    "properties": {
        "assessment_id": {
            "type": "integer",
            "minimum": 1
        },
        "analysis_type": {
            "type": "string",
            "enum": ["trend", "comparison", "summary", "indicators"],
            "default": "summary"
        },
        "compare_with": {
            "type": "array",
            "items": {"type": "integer"},
            "description": "Assessment IDs to compare with"
        }
    },
    "required": ["assessment_id"]
}

# Integrations MCP Server Schemas
INTEGRATIONS_GET_EXTERNAL_DATA_SCHEMA = {
    "type": "object",
    "properties": {
        **PAGINATION_PARAMS_SCHEMA["properties"],
        **DATE_RANGE_PARAMS_SCHEMA["properties"],
        "source": {
            "type": "string",
            "enum": ["hdx", "dtm", "unhcr", "fts", "who", "kobo"]
        },
        "data_type": {
            "type": "string",
            "enum": ["displacement", "funding", "health", "food_security", "conflict", "needs"]
        },
        "admin_level": {
            "type": "integer",
            "minimum": 0,
            "maximum": 3,
            "default": 1
        },
        "location": {
            "type": "string",
            "description": "Location name or code"
        }
    }
}

INTEGRATIONS_CRISIS_TIMELINE_SCHEMA = {
    "type": "object",
    "properties": {
        **DATE_RANGE_PARAMS_SCHEMA["properties"],
        "granularity": {
            "type": "string",
            "enum": ["daily", "weekly", "monthly"],
            "default": "monthly"
        },
        "data_types": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ["displacement", "funding", "health", "food_security", "conflict", "needs"]
            }
        }
    }
}

INTEGRATIONS_SECTOR_DATA_SCHEMA = {
    "type": "object",
    "properties": {
        "sector": {
            "type": "string",
            "enum": ["wash", "health", "food_security", "nutrition", "protection",
                    "education", "shelter", "cccm", "early_recovery", "logistics", "etc"]
        },
        "admin_level": {
            "type": "integer",
            "minimum": 0,
            "maximum": 3,
            "default": 1
        },
        **DATE_RANGE_PARAMS_SCHEMA["properties"]
    },
    "required": ["sector"]
}

# Response data schemas
SITE_DATA_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "site_type": {"type": "string"},
        "status": {"type": "string"},
        "location": {"type": ["object", "null"]},  # GeoJSON
        "population": {"type": "integer"},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
        "services": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "service_type": {"type": "string"},
                    "capacity": {"type": "integer"},
                    "current_load": {"type": "integer"}
                }
            }
        }
    }
}

REPORT_DATA_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "title": {"type": "string"},
        "content": {"type": "string"},
        "urgency_level": {"type": "string"},
        "site": {"type": "object"},
        "gso": {"type": "object"},
        "created_at": {"type": "string", "format": "date-time"},
        "media": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file_type": {"type": "string"},
                    "file_url": {"type": "string"},
                    "description": {"type": "string"}
                }
            }
        }
    }
}

ASSESSMENT_DATA_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "title": {"type": "string"},
        "assessment_type": {"type": "string"},
        "status": {"type": "string"},
        "site": {"type": "object"},
        "kobo_form_id": {"type": "string"},
        "responses_count": {"type": "integer"},
        "created_at": {"type": "string", "format": "date-time"},
        "last_response_at": {"type": ["string", "null"], "format": "date-time"}
    }
}

EXTERNAL_DATA_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "source": {"type": "string"},
        "data_type": {"type": "string"},
        "title": {"type": "string"},
        "crisis_date": {"type": "string", "format": "date"},
        "report_date": {"type": "string", "format": "date"},
        "location_name": {"type": "string"},
        "admin_level": {"type": "string"},
        "raw_data": {"type": "object"},
        "processed_data": {"type": ["object", "null"]}
    }
}

# Method schemas by server
SITES_SERVER_METHODS = {
    "get_all_sites": {
        "description": "Get all displacement sites with filtering",
        "parameters": SITES_GET_ALL_SCHEMA,
        "response": {
            "type": "object",
            "properties": {
                **BASE_RESPONSE_SCHEMA["properties"],
                "data": {
                    "type": "array",
                    "items": SITE_DATA_SCHEMA
                }
            }
        }
    },
    "get_site_by_id": {
        "description": "Get detailed information for specific site",
        "parameters": SITES_GET_BY_ID_SCHEMA,
        "response": {
            "type": "object",
            "properties": {
                **BASE_RESPONSE_SCHEMA["properties"],
                "data": SITE_DATA_SCHEMA
            }
        }
    },
    "get_sites_geojson": {
        "description": "Get sites as GeoJSON FeatureCollection",
        "parameters": SITES_GET_ALL_SCHEMA,
        "response": {
            "type": "object",
            "properties": {
                **BASE_RESPONSE_SCHEMA["properties"],
                "data": {
                    "type": "object",
                    "description": "GeoJSON FeatureCollection"
                }
            }
        }
    }
}

REPORTS_SERVER_METHODS = {
    "get_all_reports": {
        "description": "Get all GSO field reports with filtering",
        "parameters": REPORTS_GET_ALL_SCHEMA,
        "response": {
            "type": "object",
            "properties": {
                **BASE_RESPONSE_SCHEMA["properties"],
                "data": {
                    "type": "array",
                    "items": REPORT_DATA_SCHEMA
                }
            }
        }
    },
    "get_report_by_id": {
        "description": "Get detailed information for specific report",
        "parameters": REPORTS_GET_BY_ID_SCHEMA,
        "response": {
            "type": "object",
            "properties": {
                **BASE_RESPONSE_SCHEMA["properties"],
                "data": REPORT_DATA_SCHEMA
            }
        }
    },
    "search_reports": {
        "description": "Full-text search in reports (Arabic/English)",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                **PAGINATION_PARAMS_SCHEMA["properties"]
            },
            "required": ["query"]
        }
    }
}

ASSESSMENTS_SERVER_METHODS = {
    "get_all_assessments": {
        "description": "Get all assessments with filtering",
        "parameters": ASSESSMENTS_GET_ALL_SCHEMA
    },
    "get_assessment_by_id": {
        "description": "Get detailed assessment information",
        "parameters": {
            "type": "object",
            "properties": {
                "assessment_id": {"type": "integer", "minimum": 1}
            },
            "required": ["assessment_id"]
        }
    },
    "analyze_assessment": {
        "description": "Analyze assessment data and trends",
        "parameters": ASSESSMENTS_ANALYZE_SCHEMA
    }
}

INTEGRATIONS_SERVER_METHODS = {
    "get_external_data": {
        "description": "Get external humanitarian data",
        "parameters": INTEGRATIONS_GET_EXTERNAL_DATA_SCHEMA
    },
    "get_crisis_timeline": {
        "description": "Get Sudan crisis timeline data",
        "parameters": INTEGRATIONS_CRISIS_TIMELINE_SCHEMA
    },
    "get_sector_data": {
        "description": "Get sector-specific data across all sources",
        "parameters": INTEGRATIONS_SECTOR_DATA_SCHEMA
    },
    "sync_external_data": {
        "description": "Trigger synchronization with external sources",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "enum": ["hdx", "dtm", "unhcr", "fts", "all"]
                },
                "force": {"type": "boolean", "default": False}
            }
        }
    }
}

# Complete server schemas
MCP_SERVER_SCHEMAS = {
    "sites": {
        "name": "UnityAid Sites MCP Server",
        "description": "Access to displacement sites, demographics and services data",
        "methods": SITES_SERVER_METHODS
    },
    "reports": {
        "name": "UnityAid Reports MCP Server",
        "description": "Access to GSO field reports and media attachments",
        "methods": REPORTS_SERVER_METHODS
    },
    "assessments": {
        "name": "UnityAid Assessments MCP Server",
        "description": "Access to KoboToolbox assessments and survey data",
        "methods": ASSESSMENTS_SERVER_METHODS
    },
    "integrations": {
        "name": "UnityAid Integrations MCP Server",
        "description": "Unified access to external humanitarian data sources",
        "methods": INTEGRATIONS_SERVER_METHODS
    }
}