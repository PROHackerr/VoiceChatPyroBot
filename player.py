import threading
import queue
from subprocess import Popen, PIPE
from helpers import State

q = queue.Queue()
q_list = []

process = None
STATE = State.NothingSpecial


def worker():
    global process, q_list, STATE
    while True:
        item = q.get()
        log = None

        if "stream_url" in item:
            STATE = State.Streaming
            if "log" in item:
                if item["log"]:
                    log = item["log"][0](
                        *item["log"][1]
                    )
            process = Popen(["mplayer", item["stream_url"]], stdin=PIPE)
            process.wait()
        else:
            STATE = State.Playing
            item["on_start"][0](
                *item["on_start"][1],
                quote=True
            )

            if "log" in item:
                if item["log"]:
                    args = item["log"][1]
                    args[1] = args[1].format(
                        item["url"],
                        item["title"],
                        item["sent_by_id"],
                        item["sent_by_name"],
                        item["dur"]
                    )
                    log = item["log"][0](
                        *args
                    )

            process = Popen(["mplayer", item["file"]], stdin=PIPE)
            process.wait()

            if STATE == State.Playing:
                item["on_end"][0](
                    *item["on_end"][1],
                    quote=True
                )
            elif STATE == State.Skipped:
                item["on_skip"][0](
                    *item["on_skip"][1],
                    quote=True
                )

            if q_list:
                if q_list[0] == item:
                    del q_list[0]
        if log:
            log.delete()

        STATE = State.NothingSpecial
        process = None
        if q:
            q.task_done()


threading.Thread(target=worker, daemon=True).start()


def play(file, on_start, on_end, title, url, sent_by_id, sent_by_name, log, dur, on_skip):
    args = {
        "file": file,
        "on_start": on_start,
        "on_end": on_end,
        "title": title,
        "url": url,
        "sent_by_id": sent_by_id,
        "sent_by_name": sent_by_name,
        "log": log,
        "dur": dur,
        "on_skip": on_skip
    }
    q.put(
        args
    )
    q_list.append(
        args
    )
    return q.qsize()


def stream(stream_url, log):
    q.put(
        {
            "stream_url": stream_url,
            "log": log
        }
    )
    return q.qsize()


def currently_playing():
    return q_list[0] if q_list else []


def abort():
    if process:
        process.terminate()
        del q_list[0]
        return True
    return False


def pause_resume():
    if process:
        process.stdin.write(b"p")
        process.stdin.flush()
        return True
    return False


def sf():
    if process:
        process.stdin.write(b"\x1B[D")
        process.stdin.flush()
        return True
    return False
