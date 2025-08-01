# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime

import pytest


class MockDocument:
    @classmethod
    def vocabulary(cls, base_url="http://spam.eggs/"):
        return {
            "spam": {"@id": f"{base_url}spam"},
            "ham": {"@id": f"{base_url}ham", "@type": "@id"},
            "eggs": {"@id": f"{base_url}eggs", "@container": "@list"},
            "use_until": {"@id": f"{base_url}use_until", "@type": "http://schema.org/DateTime"},

            "Egg": {"@id": f"{base_url}Egg"},
        }

    @classmethod
    def compact(cls, base_url="http://spam.eggs/"):
        return {
            "@context": cls.vocabulary(base_url),

            "spam": "bacon",
            "ham": f"{base_url}identifier",
            "eggs": [
                {"@type": "Egg", "use_until": datetime(2024, 4, 20, 16, 20).isoformat()},
                {"@type": "Egg", "use_until": datetime(2026, 12, 31, 23, 59, 59).isoformat()},
            ]
        }

    @classmethod
    def expanded(cls, base_url="http://spam.eggs/"):
        return [{
            f"{base_url}spam": [{"@value": "bacon"}],
            f"{base_url}ham": [{"@id": f"{base_url}identifier"}],
            f"{base_url}eggs": [{"@list": [
                {
                    "@type": [f"{base_url}Egg"],
                    f"{base_url}use_until": [
                        {"@type": "http://schema.org/DateTime", "@value": "2024-04-20T16:20:00"}
                    ],
                },
                {
                    "@type": [f"{base_url}Egg"],
                    f"{base_url}use_until": [
                        {"@type": "http://schema.org/DateTime", "@value": "2026-12-31T23:59:59"}
                    ],
                }
            ]}]
        }]


@pytest.fixture
def mock_context():
    return MockDocument.vocabulary()


@pytest.fixture
def mock_document():
    return MockDocument
