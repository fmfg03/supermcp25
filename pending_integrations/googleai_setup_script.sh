#!/bin/bash
# GoogleAI Agent Setup Script - Integración automática con SUPERmcp A2A
# Configura e instala el GoogleAI Agent en tu sistema existente

echo "🚀 GoogleAI Agent Setup - SUPERmcp A2A Integration"
echo "=================================================="
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "supermcp_a2a_server.py" ]; then
    echo "❌ Error: Ejecutar desde el directorio /root/supermcp"
    echo "   cd /root/supermcp && ./setup_googleai_agent.sh"
    exit 1
fi

# Verificar API Key de Google
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "⚠️  GOOGLE_API_KEY no configurada"
    echo "   Configúrala con: export GOOGLE_API_KEY='tu_api_key_aqui'"
    echo "   O agrégala al archivo .env"
    echo ""
    read -p "¿Quieres configurarla ahora? (y/N): " configure_key
    
    if [[ $configure_key =~ ^[Yy]$ ]]; then
        read -p "Ingresa tu Google AI Studio API Key: " api_key
        echo "GOOGLE_API_KEY='$api_key'" >> .env
        export GOOGLE_API_KEY="$api_key"
        echo "✅ API Key configurada"
    else
        echo "❌ API Key requerida para continuar"
        exit 1
    fi
fi

echo "📦 Instalando dependencias de Google AI..."

# Instalar Google Generative AI
pip install google-generativeai --quiet

# Verificar instalación
python3 -c "import google.generativeai; print('✅ Google AI SDK instalado correctamente')" 2>/dev/null || {
    echo "❌ Error instalando Google AI SDK"
    exit 1
}

echo "📁 Creando estructura de archivos..."

# Crear archivo de configuración para GoogleAI Agent
cat > configs/googleai_config.json << 'EOF'
{
  "models": {
    "gemini-pro": {
      "enabled": true,
      "max_tokens": 30720,
      "temperature": 0.7,
      "rate_limit": 60
    },
    "gemini-pro-vision": {
      "enabled": true,
      "max_tokens": 30720,
      "supports_images": true,
      "rate_limit": 60
    },
    "text-embedding-004": {
      "enabled": true,
      "dimensions": 768,
      "rate_limit": 1000
    }
  },
  "capabilities": [
    "text_generation",
    "text_analysis", 
    "image_analysis",
    "translation",
    "embedding_generation",
    "code_generation",
    "summarization"
  ],
  "a2a_integration": {
    "auto_register": true,
    "heartbeat_interval": 30,
    "max_concurrent_tasks": 10
  }
}
EOF

echo "🔧 Creando script de inicio..."

# Crear script de inicio para GoogleAI Agent
cat > start_googleai_agent.sh << 'EOF'
#!/bin/bash
echo "🤖 Starting GoogleAI A2A Agent..."

# Verificar API Key
if [ -z "$GOOGLE_API_KEY" ]; then
    if [ -f ".env" ]; then
        source .env
    fi
    
    if [ -z "$GOOGLE_API_KEY" ]; then
        echo "❌ GOOGLE_API_KEY not found"
        exit 1
    fi
fi

# Crear directorio de logs si no existe
mkdir -p logs/a2a

# Iniciar GoogleAI Agent
echo "Starting GoogleAI Agent on port 8213..."
python3 googleai_a2a_agent.py > logs/a2a/googleai-agent.log 2>&1 &
echo $! > logs/a2a/googleai-agent.pid

sleep 3

# Verificar que está corriendo
if curl -s http://localhost:8213/health > /dev/null; then
    echo "✅ GoogleAI Agent started successfully"
    echo "📊 Health check: http://localhost:8213/health"
    echo "🔧 Capabilities: http://localhost:8213/capabilities"
    echo "📋 Logs: tail -f logs/a2a/googleai-agent.log"
else
    echo "❌ GoogleAI Agent failed to start"
    echo "📋 Check logs: cat logs/a2a/googleai-agent.log"
    exit 1
fi
EOF

chmod +x start_googleai_agent.sh

echo "🧪 Creando script de testing..."

# Crear script de testing
cat > test_googleai_agent.py << 'EOF'
#!/usr/bin/env python3
"""
Test GoogleAI Agent - Verificar integración A2A
"""

import asyncio
import aiohttp
import json

class GoogleAIAgentTester:
    def __init__(self):
        self.agent_url = "http://localhost:8213"
        self.a2a_server_url = "http://localhost:8200"
    
    async def run_tests(self):
        print("🧪 GoogleAI Agent Integration Tests")
        print("===================================")
        print()
        
        tests = [
            ("Health Check", self.test_health),
            ("Capabilities Check", self.test_capabilities),
            ("A2A Registration", self.test_a2a_registration),
            ("Text Generation", self.test_text_generation),
            ("Text Analysis", self.test_text_analysis),
            ("Translation", self.test_translation),
            ("Code Generation", self.test_code_generation)
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"🔬 Running: {test_name}")
            try:
                result = await test_func()
                if result:
                    print(f"   ✅ PASSED")
                    results.append((test_name, "PASSED"))
                else:
                    print(f"   ❌ FAILED")
                    results.append((test_name, "FAILED"))
            except Exception as e:
                print(f"   💥 ERROR: {e}")
                results.append((test_name, f"ERROR: {e}"))
            print()
        
        # Resumen
        print("📊 Test Results Summary")
        print("======================")
        passed = len([r for r in results if r[1] == "PASSED"])
        total = len(results)
        print(f"✅ Passed: {passed}/{total}")
        
        for test_name, status in results:
            status_icon = "✅" if status == "PASSED" else "❌"
            print(f"{status_icon} {test_name}: {status}")
    
    async def test_health(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.agent_url}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("status") == "healthy"
        return False
    
    async def test_capabilities(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.agent_url}/capabilities") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return len(data.get("capabilities", [])) > 0
        return False
    
    async def test_a2a_registration(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.a2a_server_url}/agents") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    agents = data.get("agents", [])
                    return any(agent.get("agent_id") == "googleai_agent_v1" for agent in agents)
        return False
    
    async def test_text_generation(self):
        task_data = {
            "task_id": "test_generation",
            "task_type": "text_generation",
            "payload": {
                "prompt": "Escribe un saludo profesional para un email",
                "max_tokens": 100
            },
            "requester_id": "test_client"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.agent_url}/a2a", json=task_data) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result = data.get("result", {})
                    return result.get("text_generation_completed", False)
        return False
    
    async def test_text_analysis(self):
        task_data = {
            "task_id": "test_analysis",
            "task_type": "text_analysis",
            "payload": {
                "text": "Me encanta este producto, es fantástico y muy útil.",
                "analysis_type": "sentiment"
            },
            "requester_id": "test_client"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.agent_url}/a2a", json=task_data) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result = data.get("result", {})
                    return result.get("text_analysis_completed", False)
        return False
    
    async def test_translation(self):
        task_data = {
            "task_id": "test_translation",
            "task_type": "translation",
            "payload": {
                "text": "Hello, how are you today?",
                "target_language": "Spanish"
            },
            "requester_id": "test_client"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.agent_url}/a2a", json=task_data) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result = data.get("result", {})
                    return result.get("translation_completed", False)
        return False
    
    async def test_code_generation(self):
        task_data = {
            "task_id": "test_code",
            "task_type": "code_generation",
            "payload": {
                "prompt": "Función Python para calcular factorial",
                "language": "python",
                "subtype": "generation"
            },
            "requester_id": "test_client"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.agent_url}/a2a", json=task_data) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result = data.get("result", {})
                    return result.get("code_task_completed", False)
        return False

async def main():
    tester = GoogleAIAgentTester()
    await tester.run_tests()

if __name__ == "__main__":
    asyncio.run(main())
EOF

chmod +x test_googleai_agent.py

echo "⚙️ Creando archivo de configuración de entorno..."

# Agregar configuración al .env si no existe
if [ ! -f ".env" ]; then
    touch .env
fi

# Verificar si ya está configurado
if ! grep -q "GOOGLE_API_KEY" .env; then
    echo "" >> .env
    echo "# Google AI Studio Configuration" >> .env
    echo "GOOGLE_API_KEY='$GOOGLE_API_KEY'" >> .env
fi

echo "🔄 Integrando con sistema A2A existente..."

# Actualizar configuración A2A para incluir GoogleAI Agent
if [ -f "configs/a2a_config.json" ]; then
    # Backup de configuración actual
    cp configs/a2a_config.json configs/a2a_config.json.backup
    
    # Agregar GoogleAI Agent a la configuración
    python3 -c "
import json
with open('configs/a2a_config.json', 'r') as f:
    config = json.load(f)

config['agents']['googleai'] = {
    'port': 8213,
    'mcp_url': 'http://localhost:8213',
    'capabilities': ['text_generation', 'text_analysis', 'image_analysis', 'translation', 'embedding_generation', 'code_generation', 'summarization']
}

with open('configs/a2a_config.json', 'w') as f:
    json.dump(config, f, indent=2)
"
    echo "✅ Configuración A2A actualizada"
else
    echo "⚠️  Configuración A2A no encontrada, creando nueva..."
    mkdir -p configs
    cp configs/googleai_config.json configs/a2a_config.json
fi

echo "📋 Creando scripts de gestión..."

# Script para parar el agente
cat > stop_googleai_agent.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping GoogleAI Agent..."

if [ -f "logs/a2a/googleai-agent.pid" ]; then
    PID=$(cat logs/a2a/googleai-agent.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✅ GoogleAI Agent stopped (PID: $PID)"
        rm logs/a2a/googleai-agent.pid
    else
        echo "⚠️  GoogleAI Agent not running"
        rm -f logs/a2a/googleai-agent.pid
    fi
else
    echo "⚠️  No PID file found"
fi
EOF

chmod +x stop_googleai_agent.sh

# Script para reiniciar el agente
cat > restart_googleai_agent.sh << 'EOF'
#!/bin/bash
echo "🔄 Restarting GoogleAI Agent..."
./stop_googleai_agent.sh
sleep 2
./start_googleai_agent.sh
EOF

chmod +x restart_googleai_agent.sh

# Script de status
cat > status_googleai_agent.sh << 'EOF'
#!/bin/bash
echo "📊 GoogleAI Agent Status"
echo "========================"

if [ -f "logs/a2a/googleai-agent.pid" ]; then
    PID=$(cat logs/a2a/googleai-agent.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "Status: ✅ Running (PID: $PID)"
        
        # Test health endpoint
        if curl -s http://localhost:8213/health > /dev/null; then
            echo "Health: ✅ Healthy"
            echo "Port: 8213"
            echo "Endpoints:"
            echo "  - Health: http://localhost:8213/health"
            echo "  - A2A: http://localhost:8213/a2a"
            echo "  - Capabilities: http://localhost:8213/capabilities"
        else
            echo "Health: ❌ Not responding"
        fi
    else
        echo "Status: ❌ Not running (stale PID file)"
        rm -f logs/a2a/googleai-agent.pid
    fi
else
    echo "Status: ❌ Not running"
fi

echo ""
echo "Recent logs:"
if [ -f "logs/a2a/googleai-agent.log" ]; then
    tail -n 5 logs/a2a/googleai-agent.log
else
    echo "No logs available"
fi
EOF

chmod +x status_googleai_agent.sh

echo ""
echo "✅ GoogleAI Agent Setup Complete!"
echo "================================="
echo ""
echo "📦 Archivos creados:"
echo "  🤖 googleai_a2a_agent.py      - Agente principal"
echo "  🚀 start_googleai_agent.sh    - Script de inicio"
echo "  🛑 stop_googleai_agent.sh     - Script para parar"
echo "  🔄 restart_googleai_agent.sh  - Script de reinicio"
echo "  📊 status_googleai_agent.sh   - Verificar estado"
echo "  🧪 test_googleai_agent.py     - Suite de testing"
echo "  ⚙️ configs/googleai_config.json - Configuración"
echo ""
echo "🚀 Próximos pasos:"
echo "1. Iniciar GoogleAI Agent:"
echo "   ./start_googleai_agent.sh"
echo ""
echo "2. Verificar que funciona:"
echo "   ./status_googleai_agent.sh"
echo ""
echo "3. Ejecutar tests:"
echo "   python3 test_googleai_agent.py"
echo ""
echo "4. Integrar con sistema A2A:"
echo "   - El agente se registrará automáticamente"
echo "   - Visible en http://localhost:8200/agents"
echo "   - Listo para recibir delegaciones A2A"
echo ""
echo "🌐 URLs importantes:"
echo "  📊 A2A Central Server: http://localhost:8200"
echo "  🤖 GoogleAI Agent: http://localhost:8213"
echo "  🏥 Health Check: http://localhost:8213/health"
echo ""
echo "🎉 ¡GoogleAI Agent listo para integrarse con tu stack SUPERmcp!"agent": {
    "id": "googleai_agent_v1",
    "name": "Google AI Studio Agent",
    "port": 8213,
    "version": "1.0.0"
  },
  "