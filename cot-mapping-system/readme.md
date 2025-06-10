# CoT Mapping Email System

Sistema automatizado para procesar Class of Trades (CoTs) de Estados Unidos desde archivos Excel recibidos por email, con identificación inteligente de nuevos elementos y chat con IA.

## 🚀 Características

- **📧 Procesamiento automático de emails** con attachments Excel
- **🔍 Identificación inteligente** de New Channels y New COTs
- **💬 Chat con IA** para consultas en lenguaje natural
- **📊 Dashboard en tiempo real** con estadísticas
- **🔄 Automatización completa** con n8n workflows
- **📋 Auditoría completa** de todos los procesamientos

## 🛠️ Stack Tecnológico

- **Backend:** FastAPI + SQLite
- **IA:** Ollama (llama3.1:8b)
- **Automatización:** n8n
- **Frontend:** HTML/CSS/JavaScript
- **Datos:** Pandas + SQLAlchemy

## 📦 Instalación Rápida

### 1. Clonar y configurar
```bash
git clone <repository>
cd cot-mapping-system
chmod +x scripts/install.sh
./scripts/install.sh
```

### 2. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus credenciales de email
```

### 3. Instalar Ollama
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.1:8b
```

### 4. Ejecutar sistema
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

## 🔧 Configuración Manual

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar base de datos
```bash
python -c "from database import init_db; init_db()"
```

### 3. Ejecutar API
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Acceder al dashboard
```
http://localhost:8000/dashboard
```

## 📧 Configuración de Email

1. **Gmail/Google Workspace:**
   - Habilitar autenticación de 2 factores
   - Generar App Password
   - IMAP: `imap.gmail.com:993`
   - SMTP: `smtp.gmail.com:587`

2. **Outlook/Exchange:**
   - IMAP: `outlook.office365.com:993`
   - SMTP: `smtp-mail.outlook.com:587`

## 📋 Formato de Excel Requerido

El Excel debe contener las siguientes columnas:

| Columna | Descripción | Requerido |
|---------|-------------|-----------|
| `IC Channel` | Canal original | ✅ |
| `IC COT` | COT original | ✅ |
| `New Channel` | Canal nuevo | ✅ |
| `New COT` | COT nuevo | ✅ |
| `Notes` | Notas adicionales | ❌ |

## 🤖 Uso del Chat con IA

Ejemplos de preguntas que puedes hacer:

```
¿Cuántos registros nuevos llegaron hoy?
¿Cuáles son los nuevos channels identificados?
Muéstrame un resumen del último archivo procesado
¿Hay errores en los procesamientos recientes?
¿Cuántos COTs nuevos se encontraron esta semana?
```

## 🔄 Automatización con n8n

### Instalar n8n
```bash
npm install -g n8n
```

### Importar workflow
1. Ejecutar `n8n`
2. Ir a `http://localhost:5678`
3. Importar `n8n-workflows/cot-email-processor.json`
4. Configurar credenciales de email
5. Activar workflow

## 📊 API Endpoints

### Procesamiento
- `POST /upload-excel/` - Subir Excel manualmente
- `GET /mappings/` - Obtener mapeos
- `GET /mappings/new-items/` - Elementos nuevos
- `GET /processing-logs/` - Logs de procesamiento

### Chat con IA
- `POST /chat/` - Hacer pregunta a la IA
- `GET /chat/reload-context/` - Recargar contexto

### Configuración
- `GET /email-config/` - Obtener configuración email
- `PUT /email-config/` - Actualizar configuración
- `POST /email-monitoring/start/` - Iniciar monitoreo
- `POST /email-monitoring/stop/` - Detener monitoreo

### Analytics
- `GET /analytics/summary/` - Resumen estadístico

## 🐳 Docker (Opcional)

```bash
# Construir imagen
docker-compose build

# Ejecutar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f
```

## 📁 Estructura de Archivos

```
cot-mapping-system/
├── main.py              # API principal FastAPI
├── database.py          # Configuración de base de datos
├── models.py            # Modelos SQLAlchemy
├── email_processor.py   # Procesador de emails
├── chat_handler.py      # Manejador de chat IA
├── templates/
│   └── dashboard.html   # Dashboard principal
├── static/              # Archivos estáticos CSS/JS
├── uploads/             # Archivos Excel subidos
├── logs/                # Logs del sistema
└── backups/             # Backups de BD
```

## 🔍 Troubleshooting

### Error de conexión Ollama
```bash
# Verificar que Ollama esté ejecutándose
ollama list
ollama serve
```

### Error de email
```bash
# Verificar configuración en dashboard
# Probar conexión IMAP/SMTP manualmente
```

### Error de base de datos
```bash
# Recrear base de datos
rm cot_mappings.db
python -c "from database import init_db; init_db()"
```

## 📞 Soporte

Para problemas o preguntas:
1. Revisar logs en `logs/`
2. Verificar configuración en dashboard
3. Consultar documentación de API en `http://localhost:8000/docs`

## 📄 Licencia

MIT License - Ver archivo LICENSE para detalles.

## 🚀 Próximas Características

- [ ] Integración con Hugging Face para análisis avanzados
- [ ] Dashboard con gráficos interactivos
- [ ] Notificaciones push
- [ ] API REST completa
- [ ] Exportación a múltiples formatos
- [ ] Backup automático
- [ ] Clustering de datos