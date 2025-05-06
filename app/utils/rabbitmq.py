import pika
import time

def wait_for_rabbitmq(host="rabbitmq", retry_delay=2):
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
            print("✅ Connected to RabbitMQ!")
            return connection
        except pika.exceptions.AMQPConnectionError:
            print(f"❌ RabbitMQ not ready, retrying in {retry_delay}s...")
            time.sleep(retry_delay)
