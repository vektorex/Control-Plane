"""
Configurable limits for Step 30: Multimodal AI and Unified Artifact Intelligence.
Enforces strict server-side limits preventing resource exhaustion and decompression bombs.
"""

# Maximum file upload size: 50MB
MULTIMODAL_MAX_FILE_SIZE: int = 50 * 1024 * 1024

# Maximum image file size: 15MB
MULTIMODAL_MAX_IMAGE_SIZE: int = 15 * 1024 * 1024

# Maximum image dimensions (prevent decompression bombs)
MULTIMODAL_MAX_IMAGE_WIDTH: int = 4096
MULTIMODAL_MAX_IMAGE_HEIGHT: int = 4096
MULTIMODAL_MAX_IMAGE_PIXELS: int = 16_000_000

# Maximum audio duration in seconds: 1 hour (3600s)
MULTIMODAL_MAX_AUDIO_DURATION: int = 3600

# Maximum video duration in seconds: 30 minutes (1800s)
MULTIMODAL_MAX_VIDEO_DURATION: int = 1800

# Maximum extracted key frames per video artifact
MULTIMODAL_MAX_VIDEO_FRAMES: int = 30

# Maximum artifact parts allowed per artifact
MULTIMODAL_MAX_ARTIFACT_PARTS: int = 100

# Maximum rows and columns extracted from a structured table
MULTIMODAL_MAX_TABLE_ROWS: int = 5000
MULTIMODAL_MAX_TABLE_COLS: int = 100

# Maximum tokens estimated per artifact part context injection
MULTIMODAL_MAX_PART_TOKENS: int = 3000

# Default retention policy in days
ARTIFACT_RETENTION_DAYS: int = 90
