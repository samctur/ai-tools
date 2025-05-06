import pika
import json
import time
from datetime import datetime
from app.utils.rabbitmq import wait_for_rabbitmq

QUEUE_NAME = "logger"
ROUTING_KEY_PREFIX = "ai-tools"
EXCHANGE_NAME = "ai-tools"

def callback(ch, method, properties, body):
    msg = json.loads(body)
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "routing_key": method.routing_key,
        "body": msg
    }
    print(f"🔍 Logged: {log_entry}")
    with open("./output/logs/message_log.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def main():
    # Wait for RabbitMQ to be ready
    connection = wait_for_rabbitmq()
    channel = connection.channel()
    # Declare exchange and queue
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="topic", durable=True)
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    # Bind the queue to the exchange with the routing key
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key=f"{ROUTING_KEY_PREFIX}.#")

    print("🔎 Logger attached to all ai-tools events.")
    # Start consuming messages from the queue
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == "__main__":
    main()
