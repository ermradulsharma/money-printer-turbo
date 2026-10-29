import os


def resolve_path_within_directory(
    base_dir: str,
    unsafe_path: str,
    *,
    require_file: bool = True,
) -> str:
    if not unsafe_path:
        raise ValueError("empty path is not allowed")

    base_dir_real = os.path.realpath(base_dir)
    if os.path.isabs(unsafe_path):
        candidate_path = unsafe_path
    else:
        candidate_path = os.path.join(base_dir_real, unsafe_path)
    resolved_path = os.path.realpath(candidate_path)

    allowed_prefix = (
        base_dir_real if base_dir_real.endswith(os.sep) else base_dir_real + os.sep
    )
    if not (resolved_path == base_dir_real or resolved_path.startswith(allowed_prefix)):
        raise ValueError("path is outside the allowed directory")

    try:
        common_path = os.path.commonpath([base_dir_real, resolved_path])
    except ValueError as exc:
        raise ValueError("path is outside the allowed directory") from exc

    if common_path != base_dir_real:
        raise ValueError("path is outside the allowed directory")

    if require_file and not os.path.isfile(resolved_path):
        raise ValueError("file does not exist")

    return resolved_path
