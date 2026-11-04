"""Application-wide constants."""

MAX_LIMIT = 100

# Listing create payload caps (DoS / junk-data protection).
MAX_LISTING_DESCRIPTION_LENGTH = 2000
# Short marketplace intent phrase (Substage 3C-1) — not description.
MAX_USER_INTENT_TEXT_LENGTH = 280
MAX_LISTING_FIELDS = 40
MAX_LISTING_FIELD_KEY_LENGTH = 64
MAX_LISTING_FIELD_VALUE_LENGTH = 500
LISTING_CREATE_MAX_REQUESTS = 10
LISTING_CREATE_WINDOW_SECONDS = 60.0
