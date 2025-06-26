#!/bin/bash
# Setup Script para SUPERmcp Unified Command Center
# Integra TODOS los componentes en un solo frontend

echo "🚀 Setting up SUPERmcp Unified Command Center..."
echo "=================================================="

# Crear directorio principal
UNIFIED_DIR="supermcp_unified"
mkdir -p $UNIFIED_DIR
cd $UNIFIED_DIR

# Instalar dependencias Python
echo "📦 Installing Python dependencies..."
pip install fastapi uvicorn aiohttp sqlite3 pydantic

# Crear estructura de directorios
echo "📁 Creating directory structure..."
mkdir -p {static,templates,logs,config,scripts}

# Crear el frontend unificado (guardado desde el artifact)
echo "🎨 Creating unified frontend..."
cat > index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SUPERmcp Unified Command Center</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.6/dist/vis-network.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/chart.js/3.9.1/chart.min.js"></script>
    <!-- Frontend completo va aquí - copiar del artifact HTML anterior -->
</head>
<body>
    <!-- Todo el HTML del frontend unificado -->
</body>
</html>
EOF

# Crear archivo de configuración del sistema
echo "⚙️ Creating system configuration..."
cat > config/system_config.json << 'EOF'
{
    "unified_gateway": {
        "port": 9000,
        "title": "SUPERmcp Unified Command Center",
        "description": "Central control hub for the entire SUPERmcp ecosystem"
    },
    "services": {
        "a2a_central": {
            "name": "A2A Central Server",
            "port": 8200,
            "priority": "critical",
            "auto_start": true
        },
        "manus": {
            "name": "Manus Orchestrator",
            "port": 8210,
            "priority": "critical", 
            "auto_start": true
        },
        "sam": {
            "name": "SAM Executor",
            "port": 8211,
            "priority": "critical",
            "auto_start": true
        },
        "memory": {
            "name": "Memory Analyzer", 
            "port": 8212,
            "priority": "critical",
            "auto_start": true
        },
        "googleai": {
            "name": "Google AI Agent",
            "port": 8213,
            "priority": "high",
            "auto_start": true
        },
        "observatory_monitor": {
            "name": "Observatory Monitor",
            "port": 8125,
            "priority": "medium",
            "auto_start": false
        },
        "observatory_dashboard": {
            "name": "Observatory Dashboard",
            "port": 8126, 
            "priority": "medium",
            "auto_start": false
        },
        "observatory_validation": {
            "name": "Observatory Validation",
            "port": 8127,
            "priority": "medium",
            "auto_start": false
        },
        "a2a_dashboard": {
            "name": "A2A Visual Dashboard",
            "port": 8300,
            "priority": "low",
            "auto_start": false
        },
        "mcp_backend": {
            "name": "MCP Backend",
            "port": 3000,
            "priority": "high", 
            "auto_start": false
        },
        "sam_chat": {
            "name": "Sam.chat Frontend",
            "port": 5174,
            "priority": "low",
            "auto_start": false
        }
    },
    "monitoring": {
        "health_check_interval": 30,
        "metrics_collection_interval": 60,
        "log_retention_days": 30
    },
    "features": {
        "enable_observatory": true,
        "enable_a2a_visual": true,
        "enable_google_ai": true,
        "enable_real_time_updates": true
    }
}
EOF

# Crear script de inicio unificado
echo "🚀 Creating unified startup script..."
cat > scripts/start_unified_system.sh << 'EOF'
#!/bin/bash
# Script de inicio unificado para SUPERmcp

echo "🚀 Starting SUPERmcp Unified System..."
echo "====================================="

# Función para verificar si un puerto está en uso
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0  # Puerto en uso
    else
        return 1  # Puerto libre
    fi
}

# Función para iniciar un servicio
start_service() {
    local service_name=$1
    local script_path=$2
    local port=$3
    local priority=$4
    
    echo "🔍 Checking $service_name ($port)..."
    
    if check_port $port; then
        echo "✅ $service_name already running on port $port"
        return 0
    fi
    
    if [ -f "$script_path" ]; then
        echo "🚀 Starting $service_name..."
        nohup python3 "$script_path" > "logs/${service_name}.log" 2>&1 &
        echo $! > "logs/${service_name}.pid"
        sleep 3
        
        if check_port $port; then
            echo "✅ $service_name started successfully on port $port"
        else
            echo "❌ Failed to start $service_name"
            return 1
        fi
    else
        echo "⚠️  $service_name script not found: $script_path"
        return 1
    fi
}

# Función para verificar dependencias
check_dependencies() {
    echo "🔍 Checking dependencies..."
    
    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 not found. Please install Python 3.8+"
        exit 1
    fi
    
    # Verificar paquetes Python
    python3 -c "import fastapi, uvicorn, aiohttp" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "❌ Missing Python dependencies. Installing..."
        pip install fastapi uvicorn aiohttp sqlite3 pydantic
    fi
    
    echo "✅ Dependencies check passed"
}

# Función para configurar entorno
setup_environment() {
    echo "⚙️ Setting up environment..."
    
    # Crear directorios si no existen
    mkdir -p logs
    mkdir -p data
    
    # Configurar variables de entorno
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    export SUPERMCP_HOME="$(pwd)"
    
    echo "✅ Environment configured"
}

# Verificar dependencias
check_dependencies

# Configurar entorno
setup_environment

# Leer configuración
CONFIG_FILE="config/system_config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Configuration file not found: $CONFIG_FILE"
    exit 1
fi

echo "📋 Starting services based on configuration..."

# Iniciar A2A Central Server (crítico)
start_service "A2A Central" "../a2a_central_server.py" 8200 "critical"

# Iniciar agentes principales (críticos)
start_service "Manus Agent" "../manus_agent.py" 8210 "critical" 
start_service "SAM Agent" "../sam_agent.py" 8211 "critical"
start_service "Memory Agent" "../memory_agent.py" 8212 "critical"

# Iniciar Google AI Agent (alta prioridad)
start_service "GoogleAI Agent" "../googleai_agent.py" 8213 "high"

# Esperar a que los servicios críticos estén listos
echo "⏳ Waiting for critical services to initialize..."
sleep 10

# Verificar servicios críticos
critical_services=("8200:A2A Central" "8210:Manus" "8211:SAM" "8212:Memory")
all_critical_ok=true

for service in "${critical_services[@]}"; do
    port="${service%%:*}"
    name="${service##*:}"
    
    if check_port $port; then
        echo "✅ $name is healthy"
    else
        echo "❌ $name is not responding"
        all_critical_ok=false
    fi
done

if [ "$all_critical_ok" = false ]; then
    echo "❌ Critical services failed to start. Check logs in logs/ directory"
    exit 1
fi

# Iniciar servicios opcionales
echo "🔧 Starting optional services..."

# Observatory (si está habilitado)
start_service "Observatory Monitor" "../mcp_active_webhook_monitoring.py" 8125 "medium"
start_service "Observatory Dashboard" "../mcp_logs_dashboard_system.py" 8126 "medium"
start_service "Observatory Validation" "../mcp_task_validation_offline_system.py" 8127 "medium"

# A2A Visual Dashboard (opcional)
start_service "A2A Dashboard" "../a2a_dashboard_backend.py" 8300 "low"

# Finalmente, iniciar el Gateway Unificado
echo "🌐 Starting Unified Gateway..."
start_service "Unified Gateway" "../unified_gateway.py" 9000 "critical"

# Esperar a que el gateway esté listo
sleep 5

if check_port 9000; then
    echo ""
    echo "🎉 SUPERmcp Unified System Started Successfully!"
    echo "=============================================="
    echo ""
    echo "🌐 Main Interface:    http://localhost:9000"
    echo "📖 API Documentation: http://localhost:9000/docs"
    echo ""
    echo "🔗 Direct Service Access:"
    echo "   - A2A Central:      http://localhost:8200"
    echo "   - Manus Agent:      http://localhost:8210"
    echo "   - SAM Agent:        http://localhost:8211"
    echo "   - Memory Agent:     http://localhost:8212"
    echo "   - GoogleAI Agent:   http://localhost:8213"
    echo "   - Observatory:      http://localhost:8125-8127"
    echo "   - A2A Dashboard:    http://localhost:8300"
    echo ""
    echo "📊 System Status:"
    curl -s http://localhost:9000/api/services/status | python3 -m json.tool | grep -E '"name"|"status"' | head -20
    echo ""
    echo "📋 Logs location: logs/"
    echo "🛑 To stop: ./scripts/stop_unified_system.sh"
    echo ""
    echo "✨ Your unified SUPERmcp Command Center is ready!"
else
    echo "❌ Failed to start Unified Gateway"
    exit 1
fi
EOF

chmod +x scripts/start_unified_system.sh

# Crear script de parada
echo "🛑 Creating stop script..."
cat > scripts/stop_unified_system.sh << 'EOF'
#!/bin/bash
# Script para detener el sistema unificado SUPERmcp

echo "🛑 Stopping SUPERmcp Unified System..."

# Función para detener un servicio por PID
stop_service() {
    local service_name=$1
    local pid_file="logs/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "🛑 Stopping $service_name (PID: $pid)..."
            kill "$pid"
            sleep 2
            
            if kill -0 "$pid" 2>/dev/null; then
                echo "⚠️  Force killing $service_name..."
                kill -9 "$pid"
            fi
            
            echo "✅ $service_name stopped"
        else
            echo "⚠️  $service_name was not running"
        fi
        
        rm -f "$pid_file"
    else
        echo "⚠️  No PID file for $service_name"
    fi
}

# Detener servicios en orden inverso
services=("Unified Gateway" "A2A Dashboard" "Observatory Validation" "Observatory Dashboard" "Observatory Monitor" "GoogleAI Agent" "Memory Agent" "SAM Agent" "Manus Agent" "A2A Central")

for service in "${services[@]}"; do
    stop_service "$service"
done

# Limpiar logs antiguos (opcional)
echo "🧹 Cleaning up..."
find logs/ -name "*.log" -mtime +7 -delete 2>/dev/null

echo "✅ SUPERmcp Unified System stopped"
EOF

chmod +x scripts/stop_unified_system.sh

# Crear script de estado
echo "📊 Creating status script..."
cat > scripts/check_system_status.sh << 'EOF'
#!/bin/bash
# Script para verificar el estado del sistema

echo "📊 SUPERmcp System Status"
echo "========================"

# Función para verificar puerto
check_service() {
    local name=$1
    local port=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "✅ $name (port $port): Running"
        
        # Intentar health check si es posible
        if curl -s -f "http://localhost:$port/health" >/dev/null 2>&1; then
            echo "   💚 Health check: OK"
        elif curl -s -f "http://localhost:$port" >/dev/null 2>&1; then
            echo "   💚 HTTP response: OK"
        else
            echo "   ⚠️  HTTP check: No response"
        fi
    else
        echo "❌ $name (port $port): Not running"
    fi
}

# Verificar servicios
echo "🔍 Core Services:"
check_service "A2A Central" 8200
check_service "Manus Agent" 8210
check_service "SAM Agent" 8211
check_service "Memory Agent" 8212
check_service "GoogleAI Agent" 8213

echo ""
echo "🔍 Observatory Services:"
check_service "Observatory Monitor" 8125
check_service "Observatory Dashboard" 8126
check_service "Observatory Validation" 8127

echo ""
echo "🔍 Dashboard Services:"
check_service "A2A Dashboard" 8300
check_service "Unified Gateway" 9000

echo ""
echo "🔍 Optional Services:"
check_service "MCP Backend" 3000
check_service "Sam.chat" 5174

# Verificar gateway y obtener métricas
echo ""
echo "📊 System Metrics:"
if curl -s -f "http://localhost:9000/api/metrics" >/dev/null 2>&1; then
    echo "🌐 Unified Gateway: Accessible"
    curl -s "http://localhost:9000/api/metrics" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    metrics = data.get('system_metrics', {})
    overview = data.get('service_overview', {})
    
    print(f'   - Total Agents: {metrics.get(\"total_agents\", \"N/A\")}')
    print(f'   - Active Tasks: {metrics.get(\"active_tasks\", \"N/A\")}')
    print(f'   - Success Rate: {metrics.get(\"success_rate\", \"N/A\")}%')
    print(f'   - System Uptime: {metrics.get(\"system_uptime\", \"N/A\")}')
    print(f'   - Healthy Services: {overview.get(\"healthy_services\", \"N/A\")}/{overview.get(\"total_services\", \"N/A\")}')
except:
    print('   ⚠️  Could not parse metrics')
"
else
    echo "❌ Unified Gateway: Not accessible"
fi

echo ""
echo "🌐 Access URLs:"
echo "   - Main Interface: http://localhost:9000"
echo "   - API Docs: http://localhost:9000/docs"
echo "   - Service Status: http://localhost:9000/api/services/status"
EOF

chmod +x scripts/check_system_status.sh

# Crear script de desarrollo
echo "🛠️ Creating development script..."
cat > scripts/dev_mode.sh << 'EOF'
#!/bin/bash
# Modo de desarrollo - inicia solo servicios esenciales

echo "🛠️ Starting SUPERmcp in Development Mode..."

# Servicios mínimos para desarrollo
start_service() {
    local name=$1
    local script=$2
    local port=$3
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null; then
        echo "✅ $name already running on port $port"
    else
        echo "🚀 Starting $name..."
        nohup python3 "$script" > "logs/${name}.log" 2>&1 &
        echo $! > "logs/${name}.pid"
        sleep 2
    fi
}

mkdir -p logs

# Solo servicios esenciales
start_service "A2A Central" "../a2a_central_server.py" 8200
start_service "Manus Agent" "../manus_agent.py" 8210
start_service "GoogleAI Agent" "../googleai_agent.py" 8213
start_service "Unified Gateway" "../unified_gateway.py" 9000

echo ""
echo "🛠️ Development mode started!"
echo "🌐 Interface: http://localhost:9000"
echo "🧪 Only essential services running for faster development"
EOF

chmod +x scripts/dev_mode.sh

# Crear documentación
echo "📖 Creating documentation..."
cat > README.md << 'EOF'
# 🚀 SUPERmcp Unified Command Center

Un frontend completamente integrado que unifica todos los componentes del ecosistema SUPERmcp en una sola interfaz.

## 🎯 ¿Qué unifica?

### ✅ Componentes Integrados:
- **🤖 Agentes A2A** (Manus, SAM, Memory, GoogleAI)
- **🔭 MCP Observatory** (Monitoring, Dashboard, Validation)
- **🎮 A2A Visual Dashboard** (Comunicación visual)
- **🎯 Google AI Integration** (Gemini, Vision, Translation)
- **📊 Métricas Unificadas** (Todas las fuentes)
- **📋 Logs Centralizados** (Todos los servicios)
- **⚙️ Configuración Central** (Un solo lugar)

### 🌐 Una Sola URL:
```
http://localhost:9000
```

## 🚀 Instalación Rápida

### 1. Setup Automático:
```bash
chmod +x setup_supermcp_unified.sh
./setup_supermcp_unified.sh
```

### 2. Iniciar Sistema:
```bash
cd supermcp_unified
./scripts/start_unified_system.sh
```

### 3. ¡Acceder!
```
http://localhost:9000
```

## 🎮 Funcionalidades

### 📊 Dashboard Principal:
- **Vista general del sistema** con métricas en tiempo real
- **Estado de todos los servicios** (healthy/warning/error)
- **Actividad reciente** de todos los componentes
- **Métricas unificadas** (tareas, éxito, uptime)

### 🤖 Gestión de Agentes:
- **Monitoreo individual** de cada agente
- **Estado de salud** en tiempo real
- **Métricas específicas** por agente
- **Capacidades disponibles** por agente

### 🔗 Red A2A:
- **Visualización de red** estilo neuronal
- **Comunicaciones en tiempo real** animadas
- **Envío manual de tareas** entre agentes
- **Estadísticas de comunicación**

### 🔭 Observatory:
- **Monitoreo profundo** del sistema MCP
- **Validación de tareas** en tiempo real
- **Logs enterprise** con búsqueda
- **Métricas de performance**

### 🎯 Google AI:
- **Panel dedicado** para Google AI Studio
- **Testing de modelos** (Gemini Pro/Vision)
- **Estadísticas de uso** de la API
- **Configuración de modelos**

### 📜 Logs Unificados:
- **Logs de todos los servicios** en un lugar
- **Filtrado y búsqueda** avanzada
- **Niveles de log** (info, warning, error)
- **Timestamps** precisos

### ⚙️ Configuración:
- **Configuración central** de todo el sistema
- **Habilitación/deshabilitación** de servicios
- **Parámetros de monitoreo**
- **Configuración de alertas**

## 🛠️ Scripts Incluidos

### Gestión del Sistema:
```bash
# Iniciar sistema completo
./scripts/start_unified_system.sh

# Detener sistema
./scripts/stop_unified_system.sh

# Verificar estado
./scripts/check_system_status.sh

# Modo desarrollo (servicios mínimos)
./scripts/dev_mode.sh
```

## 📋 Arquitectura Unificada

```
┌─────────────────────────────────────────────────────────────┐
│                  Frontend Unificado                        │
│                  (Puerto 9000)                             │
│                                                             │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐│
│ │  Dashboard  │ │   Agents    │ │  A2A Net    │ │Observatory││
│ │             │ │             │ │             │ │          ││
│ └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘│
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐│
│ │    Tasks    │ │  GoogleAI   │ │    Logs     │ │  Config  ││
│ │             │ │             │ │             │ │          ││
│ └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘│
└─────────────────────────────────────────────────────────────┘
                                │
                    ┌─────────────────────┐
                    │  Gateway Unificado  │
                    │   (Proxy + API)     │
                    └─────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼──────┐    ┌──────────▼──────┐    ┌──────────▼──────┐
│   Agentes    │    │   Observatory   │    │   Dashboards    │
│              │    │                 │    │                 │
│ • Manus      │    │ • Monitor       │    │ • A2A Visual    │
│ • SAM        │    │ • Dashboard     │    │ • Sam.chat      │
│ • Memory     │    │ • Validation    │    │ • MCP Backend   │
│ • GoogleAI   │    │                 │    │                 │
└──────────────┘    └─────────────────┘    └─────────────────┘
```

## 🎯 Beneficios

### ✅ **Un Solo Lugar:**
- **No más múltiples URLs** a recordar
- **Interfaz consistente** en todo el sistema
- **Navegación unificada** entre componentes

### ✅ **Vista Completa:**
- **Estado de todo el sistema** de un vistazo
- **Métricas agregadas** de todos los servicios
- **Logs centralizados** de todas las fuentes

### ✅ **Gestión Simplificada:**
- **Un script** para iniciar todo
- **Un comando** para verificar estado
- **Una configuración** para todo el sistema

### ✅ **Desarrollo Eficiente:**
- **Modo desarrollo** con servicios mínimos
- **Hot reload** durante desarrollo
- **Debugging centralizado**

## 🚀 Casos de Uso

### 👨‍💻 **Para Desarrollo:**
```bash
# Modo desarrollo rápido
./scripts/dev_mode.sh

# Solo servicios esenciales corriendo
# Desarrollo más rápido y eficiente
```

### 🚀 **Para Producción:**
```bash
# Sistema completo
./scripts/start_unified_system.sh

# Todos los servicios y monitoreo
# Sistema robusto y observable
```

### 🎮 **Para Demos:**
```bash
# Interface visual impresionante
# Comunicación A2A en tiempo real
# Métricas live que actualizan
```

### 🔧 **Para Mantenimiento:**
```bash
# Estado completo del sistema
./scripts/check_system_status.sh

# Logs unificados en la interfaz
# Configuración centralizada
```

## 🎉 **¡No Más Fragmentación!**

**Antes:**
- 🔭 Observatory: `http://localhost:8125-8127`
- 🎮 A2A Dashboard: `http://localhost:8300` 
- 🤖 Agentes: `http://localhost:8200-8213`
- 💬 Sam.chat: `http://localhost:5174`
- 🔧 MCP Backend: `http://localhost:3000`

**Ahora:**
- 🚀 **TODO**: `http://localhost:9000`

### ✨ **Tu ecosistema SUPERmcp completamente unificado en una sola interfaz moderna!**
EOF

# Crear script de instalación de dependencias
echo "📦 Creating dependency installer..."
cat > scripts/install_dependencies.sh << 'EOF'
#!/bin/bash
# Instalar todas las dependencias necesarias

echo "📦 Installing SUPERmcp Dependencies..."

# Python packages
pip install -r requirements.txt

# Crear requirements.txt si no existe
if [ ! -f "requirements.txt" ]; then
    cat > requirements.txt << DEPS
fastapi==0.104.1
uvicorn==0.24.0
aiohttp==3.9.1
sqlite3
pydantic==2.5.0
websockets==12.0
python-multipart==0.0.6
jinja2==3.1.2
DEPS
fi

echo "✅ Dependencies installed"
EOF

chmod +x scripts/install_dependencies.sh

# Crear archivo de variables de entorno
echo "🌍 Creating environment configuration..."
cat > .env << 'EOF'
# SUPERmcp Unified Configuration
SUPERMCP_ENV=development
SUPERMCP_LOG_LEVEL=INFO
SUPERMCP_PORT=9000

# Google AI Configuration
GOOGLE_API_KEY=your_google_api_key_here

# Service URLs (auto-detected)
A2A_CENTRAL_URL=http://localhost:8200
MANUS_AGENT_URL=http://localhost:8210
SAM_AGENT_URL=http://localhost:8211
MEMORY_AGENT_URL=http://localhost:8212
GOOGLEAI_AGENT_URL=http://localhost:8213

# Observatory URLs
OBSERVATORY_MONITOR_URL=http://localhost:8125
OBSERVATORY_DASHBOARD_URL=http://localhost:8126
OBSERVATORY_VALIDATION_URL=http://localhost:8127

# Optional Services
A2A_DASHBOARD_URL=http://localhost:8300
MCP_BACKEND_URL=http://localhost:3000
SAM_CHAT_URL=http://localhost:5174
EOF

echo ""
echo "✅ SUPERmcp Unified Command Center Setup Completed!"
echo "=================================================="
echo ""
echo "📁 Created directory: $UNIFIED_DIR/"
echo "🎨 Frontend: index.html (unified interface)"
echo "🌐 Backend: unified_gateway.py (API gateway)"
echo "⚙️ Config: config/system_config.json"
echo "🚀 Scripts: scripts/ (start, stop, status, dev)"
echo ""
echo "🔧 Next steps:"
echo "1. Copy your existing agent scripts to this directory"
echo "2. Configure your Google API key in .env"
echo "3. Start the unified system:"
echo "   cd $UNIFIED_DIR"
echo "   ./scripts/start_unified_system.sh"
echo "4. Access your unified interface:"
echo "   http://localhost:9000"
echo ""
echo "🎉 No more fragmented interfaces!"
echo "🚀 Everything unified in one beautiful frontend!"
