# DockerAI

Aplicação desktop em PyQt5 para gerenciamento de containers Docker com foco em soluções de IA (LocalStack e Kafka).

---

## Funcionalidades

- Gerenciamento de LocalStack
  - Inicia e para o container LocalStack na porta configurada.
  - Seleção e gerenciamento de serviços: SQS, S3, Secrets Manager, DynamoDB, Lambda e API Gateway.
- Gerenciamento de Kafka
  - Interface dedicada para mon**itorar e configurar o container Kafka na porta especificada.
- Ícone na Bandeja do Sistema
  - Menu de contexto para abrir as telas de LocalStack e Kafka sem fechar as demais.
  - Notificações de erro e status via NotificationManager.
- Tema Customizado
  - Estilo da aplicação controlado por QSS (arquivo de estilo em utils/utilities.py).
- Logs Estruturados
  - Registro de eventos e erros utilizando o módulo `logging` para facilitar o diagnóstico e a manutenção.
- Arquitetura Modular
  - Padrão MVC leve: separação clara entre controllers, services e components.


---

## Pré-requisitos

- Python 3.8 ou superior  
- Docker (para executar LocalStack e Kafka)
- pip  
- pyinstaller (para gerar executáveis)

---

## Instalação em modo desenvolvimento

1. Clone o repositório:  
   ```bash
   git clone https://seu-repo.git
   cd DockerAI

2. Crie um ambiente virtual (opcional, mas recomendado):  
   ```bash
   python -m venv .venv
   source .venv/bin/activate     # Linux/macOS
   .venv\Scripts\activate        # Windows (PowerShell)
   
3. Instale as dependências:  
   ```bash
   pip install -r requirements.txt
   
4. Execute a aplicação:  
   ```bash
   python main.py

## Gerando o executável:

1 - Já incluímos dois scripts para simplificar o build com PyInstaller:
- `build.sh`: Script para Linux/macOS que executa o PyInstaller com as opções necessárias.
- `build.bat`: Script para Windows que executa o PyInstaller com as opções necessárias.
- `DockerAI.spec`: Arquivo de especificação do PyInstaller para gerar um executável em um único arquivo.
- `DockerAI_onedir.spec`: Arquivo de especificação do PyInstaller para gerar um executável em uma única pasta.

## Estrutura de pastas:
```
    ./
   ├── main.py                          # Ponto de entrada da aplicação
   ├── requirements.txt                 # Dependências Python
   ├── controller/                      # Lógica de controle para cada serviço
   │   ├── kafka/                       # Controllers do Kafka
   │   └── localstack/                  # Controllers do LocalStack
   ├── presentation/                    # Componentes de UI PyQt5
   │   └── components/
   │       ├── kafka/                   # Tela e componentes de Kafka
   │       └── localstack/              # Tela e componentes de LocalStack
   ├── services/                        # Serviços auxiliares (sessões, notificações)
   ├── utils/                           # Funções utilitárias (estilo, helpers)
   └── README.md                        # Documentação deste arquivo
```

## Logs e tratamento de erros:

```python
import logging
logger = logging.getLogger("[NotificationManager]")

try:
    # lógica de notificação
    self.notification_manager.show_toast(...)
    logger.info("[ApplicationManager] Notificação enviada com sucesso")
except Exception as e:
    logger.error(f"[ApplicationManager] Falha ao enviar notificação: {e}")
```

## Contato
Para dúvidas ou contribuições, chame no Teams/Email: Diego Oliveira Melo (diego.oliveira-melo@itau-unibanco.com.br)