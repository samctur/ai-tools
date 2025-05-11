import pika
import json
import time
from datetime import datetime
from typing import Callable


class RabbitMQConsumer:
    def __init__(
            self,
            queue_name: str,
            host: str = "rabbitmq",
            exchange_name: str = "ai-tools",
            routing_key: str = "ai-tools.#",
            retry_delay: int = 2
    ):
        self.host = host
        self.queue_name = queue_name
        self.exchange_name = exchange_name
        self.routing_key = routing_key
        self.retry_delay = retry_delay
        self.connection = None
        self.channel = None

    def connect(self):
        while True:
            try:
                self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
                self.channel = self.connection.channel()
                self.channel.exchange_declare(exchange=self.exchange_name, exchange_type="topic", durable=True)
                self.channel.queue_declare(queue=self.queue_name, durable=True)
                self.channel.queue_bind(
                    exchange=self.exchange_name,
                    queue=self.queue_name,
                    routing_key=self.routing_key
                )
                print("✅ Connected to RabbitMQ and queue bound.")
                break
            except pika.exceptions.AMQPConnectionError:
                print(f"❌ RabbitMQ not ready, retrying in {self.retry_delay}s...")
                time.sleep(self.retry_delay)

    def start_consuming(self, callback: Callable[[pika.adapters.blocking_connection.BlockingChannel, pika.spec.Basic.Deliver, pika.spec.BasicProperties, bytes], None]):
        if not self.channel:
            raise RuntimeError("RabbitMQ channel not initialized. Call connect() first.")

        print(f"🔎 Listening to events with routing key: {self.routing_key}")
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=callback, auto_ack=True)
        self.channel.start_consuming()

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            self.channel = None
