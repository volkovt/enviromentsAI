# TaskAI

Aplicação desktop em **PyQt5** com funcionalidades de IA (Stackspot), gerenciamento de tarefas, timeline, Kanban e gamificação.  
Notificações usam o módulo interno `notification_manager` e `toast_notification`, e toda a GUI é construída em PyQt5.

---

## Funcionalidades

- Interface responsiva construída com PyQt5  
- Widgets de performance e gamificação com gráficos em matplotlib  
- Componente de timeline para visualizar progresso de tarefas  
- Kanban para organização visual de tarefas  
- Sistema de notificações nativo (tray icon + toast)  
- Exportação de tarefas para Excel via openpyxl  
- Suporte a QSS para tema customizado  

---

## Pré-requisitos

- Python 3.8 ou superior  
- pip  
- pyinstaller (para gerar executáveis)

---

## Instalação em modo desenvolvimento

1. Clone o repositório:  
   ```bash
   git clone https://seu-repo.git
   cd TaskAI

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
- `TaskAI.spec`: Arquivo de especificação do PyInstaller para gerar um executável em um único arquivo.
- `TaskAI_onedir.spec`: Arquivo de especificação do PyInstaller para gerar um executável em uma única pasta.

## Estrutura de pastas:
```
    ./
    ├── main.py
    ├── build.sh
    ├── TaskAI.spec
    ├── requirements.txt
    ├── styles/
    │   └── app_styles.qss
    ├── notification_manager.py
    ├── local_session_service.py
    ├── timeline_component.py
    ├── performance_widget.py
    ├── kanban_widget.py
    ├── gamification_widget.py
    └── utilities.py
```

## Logs e tratamento de erros:

```python
import logging
logger = logging.getLogger("[NotificationManager]")

try:
    # lógica de notificação
    self.notification_manager.show_toast(...)
    logger.info("Notificação enviada com sucesso")
except Exception as e:
    logger.error(f"Falha ao enviar notificação: {e}")
```

## Contato
Para dúvidas ou contribuições, chame no Teams/Email: Diego Oliveira Melo (diego.oliveira-melo@itau-unibanco.com.br)