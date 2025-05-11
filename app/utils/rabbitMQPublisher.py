import pika
import time
from app.utils.mcpUtils import MCPMessageWrapper


class RabbitMQPublisher:
    def __init__(
            self,
            host: str = "rabbitmq",
            exchange_name: str = "ai-tools",
            routing_key_prefix: str = "ai-tools",
            retry_delay: int = 2
    ):
        self.host = host
        self.exchange_name = exchange_name
        self.routing_key_prefix = routing_key_prefix
        self.connection = None
        self.channel = None
        self.retry_delay = retry_delay  # seconds

    def connect(self):
        """Attempt to connect to RabbitMQ with retry logic."""
        while True:
            try:
                self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
                self.channel = self.connection.channel()
                self.channel.exchange_declare(exchange=self.exchange_name, exchange_type="topic", durable=True)
                print("✅ Connected to RabbitMQ!")
                break
            except pika.exceptions.AMQPConnectionError:
                print(f"❌ RabbitMQ not ready, retrying in {self.retry_delay}s...")
                time.sleep(self.retry_delay)

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            self.channel = None

    def publish(self, prompt: str, model_type: str, task: str = "generate.image"):
        if not self.channel:
            raise RuntimeError("RabbitMQ channel not initialized. Call connect() first.")

        routing_key = f"{self.routing_key_prefix}.{model_type}"

        # Wrap the message in MCPMessage
        message = MCPMessageWrapper(
            context={"model_type": model_type},
            input={"prompt": prompt},
            input_type="text",
            output_type="image",
            task=task,
            output_format="json"
        )

        # Publish the message
        self.channel.basic_publish(
            exchange=self.exchange_name,
            routing_key=routing_key,
            body=message.json(),
            properties=pika.BasicProperties(delivery_mode=2)
        )
