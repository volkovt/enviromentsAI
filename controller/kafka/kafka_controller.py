from services.kafka.kafka_service import KafkaService

class KafkaController:
    def __init__(self, port_provider: callable):
        self.service = KafkaService(port_provider())

    def start(self):
        self.service.start()

    def stop(self):
        self.service.stop()

    def create_topic(self, name: str):
        self.service.create_topic(name)

    def list_topics(self) -> list[str]:
        return self.service.list_topics()

    def is_running(self) -> bool:
        return self.service.is_running()

    def register_schema(self, topic: str, avsc_str: str) -> dict:
        return self.service.register_schema(topic, avsc_str)

    def get_schema(self, topic: str) -> str | None:
        return self.service.get_latest_schema(topic)

    def produce_avro(self, topic: str, record: dict, avsc_str: str):
        self.service.produce_avro(topic, record, avsc_str)

    def consume_avro(self, topic: str, avsc_str: str) -> list[dict]:
        return self.service.consume_avro(topic, avsc_str)

    def produce(self, topic: str, message: str):
        self.service.produce_plain(topic, message)

    def consume(self, topic: str) -> str:
        return self.service.consume_plain(topic)