"""Queue backends for scheduled scan jobs."""
import json
import os
from contextlib import contextmanager


RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "scan_jobs")


@contextmanager
def _rabbit_channel():
    try:
        import pika
    except Exception:
        yield None
        return

    params = pika.URLParameters(RABBITMQ_URL)
    connection = None
    channel = None
    try:
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        yield channel
    except Exception:
        yield None
    finally:
        if connection and connection.is_open:
            connection.close()


def publish_scan_job(scan_id: int) -> bool:
    with _rabbit_channel() as channel:
        if channel is None:
            return False
        channel.basic_publish(
            exchange="",
            routing_key=RABBITMQ_QUEUE,
            body=json.dumps({"scan_id": scan_id}),
            properties=None,
        )
        return True


def consume_scan_job():
    with _rabbit_channel() as channel:
        if channel is None:
            return None
        method_frame, _, body = channel.basic_get(queue=RABBITMQ_QUEUE, auto_ack=False)
        if not method_frame:
            return None
        try:
            payload = json.loads(body.decode("utf-8"))
            scan_id = payload.get("scan_id")
            if not scan_id:
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                return None
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            return int(scan_id)
        except Exception:
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            return None
