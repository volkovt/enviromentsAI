import logging
import subprocess
import time
from subprocess import CalledProcessError

from confluent_kafka import Producer, Consumer
from confluent_kafka.avro.serializer import SerializerError
import requests
from confluent_kafka.avro import AvroProducer, AvroConsumer, loads as avro_loads

logger = logging.getLogger(__name__)

class KafkaService:
    def __init__(self, port: int = 9092):
        self.port = port
        self.bootstrap = f"PLAINTEXT://localhost:{self.port}"
        self.schema_registry = "http://localhost:8081"
        self.network = "kafka-net"

    def start(self):
        logger.info(f"[KafkaService] Criando rede '{self.network}' (se não existir)...")
        subprocess.run(
            ["docker", "network", "create", self.network],
            check=False
        )

        for name in ("zookeeper", "kafka-broker", "schema-registry"):
            try:
                logger.info(f"[KafkaService] Removendo container existente '{name}' (se houver)...")
                subprocess.run(
                    ["docker", "rm", "-f", name],
                    check=False,
                )
            except Exception as e:
                logger.error(f"[KafkaService] Falha ao remover '{name}': {e}")

        try:
            logger.info("[KafkaService] Iniciando Zookeeper...")
            subprocess.run([
                "docker", "run", "-d", "--name", "zookeeper",
                "--network", self.network,
                "-p", "2181:2181",
                "-e", "ZOOKEEPER_CLIENT_PORT=2181",
                "confluentinc/cp-zookeeper:latest"
            ], check=True)
        except CalledProcessError as e:
            logger.error(f"[KafkaService] Erro ao iniciar Zookeeper: {e.stderr or e}")
            raise RuntimeError("Falha ao iniciar Zookeeper") from e

        try:
            logger.info("[KafkaService] Iniciando Kafka broker...")
            subprocess.run([
                "docker", "run", "-d", "--name", "kafka-broker",
                "--network", self.network,
                "-p", f"{self.port}:29092",
                "-e", "KAFKA_BROKER_ID=1",
                "-e", "KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181",
                "-e", "KAFKA_LISTENERS=INTERNAL://0.0.0.0:9092,EXTERNAL://0.0.0.0:29092",
                "-e", "KAFKA_ADVERTISED_LISTENERS=INTERNAL://kafka-broker:9092,EXTERNAL://localhost:9092",
                "-e", "KAFKA_INTER_BROKER_LISTENER_NAME=INTERNAL",
                "-e", "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=INTERNAL:PLAINTEXT,EXTERNAL:PLAINTEXT",
                "-e", "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1",
                "confluentinc/cp-kafka:latest"
            ], check=True)
        except CalledProcessError as e:
            logger.error(f"[KafkaService] Erro ao iniciar Kafka broker: {e.stderr or e}")
            raise RuntimeError("Falha ao iniciar Kafka broker") from e

        logger.info("[KafkaService] Aguardando Kafka broker ficar online...")
        time.sleep(10)

        try:
            logger.info("[KafkaService] Iniciando Schema Registry...")
            subprocess.run([
                "docker", "run", "-d", "--name", "schema-registry",
                "--network", self.network,
                "-p", "8081:8081",
                "-e", "SCHEMA_REGISTRY_HOST_NAME=localhost",
                "-e", "SCHEMA_REGISTRY_LISTENERS=http://0.0.0.0:8081",
                "-e", "SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS=PLAINTEXT://kafka-broker:9092",
                "confluentinc/cp-schema-registry:latest"
            ], check=True)
        except CalledProcessError as e:
            logger.error(f"[KafkaService] Erro ao iniciar Schema Registry: {e.stderr or e}")
            raise RuntimeError("Falha ao iniciar Schema Registry") from e

        logger.info("[KafkaService] Kafka completo iniciado com sucesso!")

    def stop(self):
        for name in ("schema-registry", "kafka-broker", "zookeeper"):
            subprocess.run(["docker", "rm", "-f", name], check=False)
        subprocess.run(["docker", "network", "rm", self.network], check=False)

    def list_topics(self) -> list[str]:
        # lista todos os tópicos, mas filtra os internos (__*)
        result = subprocess.run([
            "docker", "exec", "kafka-broker",
            "kafka-topics", "--list",
            "--bootstrap-server", f"localhost:{self.port}"
        ], capture_output=True)
        text = result.stdout.decode("utf-8", errors="replace")
        return [
            t for t in text.splitlines()
            if t and not t.startswith("__")
        ]

    def create_topic(self, topic: str):
        cmd = [
            "docker", "exec", "kafka-broker",
            "kafka-topics", "--create",
            "--topic", topic,
            "--bootstrap-server", f"localhost:{self.port}",
            "--replication-factor", "1",
            "--partitions", "1"
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True)
        except CalledProcessError as e:
            reason = e.stderr.decode("utf-8", errors="replace") if e.stderr else str(e)
            raise RuntimeError(f"Erro ao criar tópico '{topic}':\n{reason.strip()}")

    def produce_avro(self, topic: str, record: dict, avsc_str: str):
        # Converte o avsc_str em Schema com confluent_kafka.avro.loads
        schema = avro_loads(avsc_str)

        conf = {
            "bootstrap.servers": self.bootstrap.replace("PLAINTEXT://", ""),
            "schema.registry.url": self.schema_registry
        }
        producer = AvroProducer(conf, default_value_schema=schema)

        try:
            producer.produce(topic=topic, value=record)
            producer.flush()
        except SerializerError as e:
            raise RuntimeError(f"Erro serializando Avro: {e}")

    def consume_avro(self, topic: str, avsc_str: str, max_messages: int = 1) -> list[dict]:
        conf = {
            "bootstrap.servers": self.bootstrap.replace("PLAINTEXT://", ""),
            "schema.registry.url": self.schema_registry,
            "group.id": f"avro-consumer-{topic}",
            "auto.offset.reset": "earliest"
        }
        consumer = AvroConsumer(conf)
        consumer.subscribe([topic])

        records = []
        start = time.time()
        while len(records) < max_messages and time.time() - start < 10:
            msg = consumer.poll(1.0)
            if msg is None or msg.error():
                continue
            records.append(msg.value())

        consumer.close()
        return records

    def produce_plain(self, topic: str, message: str):
        p = Producer({"bootstrap.servers": self.bootstrap.replace("PLAINTEXT://", "")})
        p.produce(topic, message.encode("utf-8"))
        p.flush()

    def consume_plain(self, topic: str, max_messages: int = 1) -> str:
        c = Consumer({
            "bootstrap.servers": self.bootstrap.replace("PLAINTEXT://", ""),
            "group.id": f"plain-consumer-{topic}",
            "auto.offset.reset": "earliest"
        })
        c.subscribe([topic])

        records = []
        start = time.time()
        while len(records) < max_messages and time.time() - start < 10:
            msg = c.poll(1.0)
            if msg is None or msg.error():
                continue
            records.append(msg.value().decode("utf-8"))
        c.close()
        return "\n".join(records)

    def is_running(self) -> bool:
        res = subprocess.run([
            "docker", "ps",
            "--filter", "name=kafka-broker",
            "--filter", "status=running",
            "-q"
        ], capture_output=True)
        return bool(res.stdout.strip())

    def register_schema(self, topic: str, avsc_str: str) -> dict:
        url = f"{self.schema_registry}/subjects/{topic}-value/versions"
        resp = requests.post(url, json={"schema": avsc_str})
        resp.raise_for_status()
        return resp.json()

    def get_latest_schema(self, topic: str) -> str | None:
        """
        Retorna o schema registrado em Schema Registry para {topic}-value,
        ou None se não existir (HTTP 404).
        """
        url = f"{self.schema_registry}/subjects/{topic}-value/versions/latest"
        resp = requests.get(url)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json().get("schema")
