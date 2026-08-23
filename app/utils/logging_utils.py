import os
import threading

from loguru import logger


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
)
LOG_RECORD_FORMAT = (
    "<green>{time:%Y-%m-%d %H:%M:%S}</> | "
    "<level>{level}</> | "
    '"{file.path}:{line}":<blue> {function}</> '
    "- <level>{message}</>\n"
)
_terminal_handler_id: int | None = 0
_terminal_handler_lock = threading.RLock()


def format_log_record(record):
    """
    统一格式化终端与 WebUI 日志。

    Loguru 会把同一条记录交给多个 sink。第一个 sink 可能已经将绝对路径转换
    为项目相对路径，因此这里同时兼容绝对路径和 ``./`` 开头的已格式化路径。
    WebUI sink 会关闭颜色，但时间、级别、调用位置和消息内容与终端保持一致。
    """
    file_path = record["file"].path
    if os.path.isabs(file_path):
        relative_path = os.path.relpath(file_path, PROJECT_ROOT)
        record["file"].path = f"./{relative_path}"

    record["message"] = record["message"].replace(PROJECT_ROOT, ".")
    return LOG_RECORD_FORMAT


def configure_terminal_logger(sink, level: str, colorize: bool = True) -> int:
    """
    安全替换进程级终端日志 handler，并保留任务专用 handler。

    Streamlit 在代码热重载或缓存失效时可能重新执行日志初始化。这里只按已记录
    的 handler ID 精确移除旧终端输出，因此不会中断后台任务正在写入的 WebUI
    日志。锁用于保护多个浏览器会话同时初始化时的 ID 更新。
    """
    global _terminal_handler_id

    with _terminal_handler_lock:
        if _terminal_handler_id is not None:
            try:
                logger.remove(_terminal_handler_id)
            except ValueError:
                pass

        _terminal_handler_id = logger.add(
            sink,
            level=level,
            format=format_log_record,
            colorize=colorize,
        )
        return _terminal_handler_id
