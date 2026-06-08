ALLOWED_TYPES = [
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
]

MAX_FILE_SIZE = 1024 * 1024 * 500


def validate_file(file):

    if file.content_type not in ALLOWED_TYPES:
        raise Exception("Unsupported file type")

    return True