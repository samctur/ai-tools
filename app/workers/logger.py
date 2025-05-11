import json
from datetime import datetime
from app.utils.rabbitMQConsumer import RabbitMQConsumer


def log_callback(ch, method, properties, body):
    msg = json.loads(body)
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "routing_key": method.routing_key,
        "body": msg
    }
    print(f"🔍 Logged: {log_entry}")
    with open("./output/logs/message_log.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")


if __name__ == "__main__":
    consumer = RabbitMQConsumer(
        host="rabbitmq",
        queue_name="logger",
        exchange_name="ai-tools",
        routing_key="ai-tools.#",
    )
    consumer.connect()
    consumer.start_consuming(log_callback)

