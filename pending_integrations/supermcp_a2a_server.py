#!/usr/bin/env python3
"""
SUPERmcp A2A Server - Agent2Agent Protocol Implementation
Primera implementación empresarial de MCP + A2A integrados

Author: Manus AI
Date: June 24, 2025
Version: 1.0.0
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import aiohttp
from aiohttp import web, ClientSession
import logging
from pathlib import Path
import jsonschema

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# A2A Protocol Schemas
A2A_AGENT_CARD_SCHEMA = {
    "type": "object",
    "required": ["agent_id", "name", "version", "capabilities", "protocols", "endpoints"],
    "properties": {
        "agent_id": {"type": "string"},
        "name": {"type": "string"},
        "version": {"type": "string"},
        "capabilities": {"type": "array", "items": {"type": "string"}},
        "protocols": {"type": "array", "items": {"type": "string"}},
        "endpoints": {
            "type": "object",
            "required": ["a2a", "health"],
            "properties": {
                "a2a": {"type": "string"},
                "health": {"type": "string"}
            }
        },
        "metadata": {"type": "object"}
    }
}

A2A_TASK_SCHEMA = {
    "type": "object",
    "required": ["task_id", "task_type", "payload", "requester_id"],
    "properties": {
        "task_id": {"type": "string"},
        "task_type": {"type": "string"},
        "payload": {"type": "object"},
        "requester_id": {"type": "string"},
        "priority": {"type": "integer", "minimum": 1, "maximum": 10},
        "timeout": {"type": "integer"},
        "metadata": {"type": "object"}
    }
}

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

class AgentStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"

@dataclass
class AgentCard:
    agent_id: str
    name: str
    version: str
    capabilities: List[str]
    protocols: List[str]
    endpoints: Dict[str, str]
    metadata: Optional[Dict[str, Any]] = None
    status: AgentStatus = AgentStatus.ONLINE
    last_heartbeat: Optional[datetime] = None
    load_score: float = 0.0

@dataclass
class A2ATask:
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    requester_id: str
    assigned_agent_id: Optional[str] = None
    priority: int = 5
    timeout: int = 300
    status: TaskStatus = TaskStatus.PENDING
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AgentRegistry:
    """Registro centralizado de agentes A2A con persistencia SQLite"""
    
    def __init__(self, db_path: str = "data/a2a_agents.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self.agents: Dict[str, AgentCard] = {}
        self._load_agents()

    def _init_database(self):
        """Inicializar esquema de base de datos"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    capabilities TEXT NOT NULL,  -- JSON array
                    protocols TEXT NOT NULL,     -- JSON array
                    endpoints TEXT NOT NULL,     -- JSON object
                    metadata TEXT,               -- JSON object
                    status TEXT NOT NULL,
                    last_heartbeat TIMESTAMP,
                    load_score REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_capabilities (
                    agent_id TEXT,
                    capability TEXT,
                    confidence REAL DEFAULT 1.0,
                    PRIMARY KEY (agent_id, capability),
                    FOREIGN KEY (agent_id) REFERENCES agents (agent_id)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_capabilities 
                ON agent_capabilities (capability)
            """)

    def _load_agents(self):
        """Cargar agentes desde la base de datos"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM agents")
            
            for row in cursor.fetchall():
                agent_card = AgentCard(
                    agent_id=row['agent_id'],
                    name=row['name'],
                    version=row['version'],
                    capabilities=json.loads(row['capabilities']),
                    protocols=json.loads(row['protocols']),
                    endpoints=json.loads(row['endpoints']),
                    metadata=json.loads(row['metadata']) if row['metadata'] else None,
                    status=AgentStatus(row['status']),
                    last_heartbeat=datetime.fromisoformat(row['last_heartbeat']) if row['last_heartbeat'] else None,
                    load_score=row['load_score']
                )
                self.agents[agent_card.agent_id] = agent_card

    async def register_agent(self, agent_card_data: Dict[str, Any]) -> bool:
        """Registrar nuevo agente con validación"""
        try:
            # Validar schema
            jsonschema.validate(agent_card_data, A2A_AGENT_CARD_SCHEMA)
            
            agent_card = AgentCard(
                agent_id=agent_card_data['agent_id'],
                name=agent_card_data['name'],
                version=agent_card_data['version'],
                capabilities=agent_card_data['capabilities'],
                protocols=agent_card_data['protocols'],
                endpoints=agent_card_data['endpoints'],
                metadata=agent_card_data.get('metadata'),
                last_heartbeat=datetime.utcnow()
            )
            
            # Verificar que el agente responde
            health_check = await self._health_check(agent_card.endpoints['health'])
            if not health_check:
                logger.warning(f"Agent {agent_card.agent_id} failed health check")
                return False
            
            # Persistir en base de datos
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO agents 
                    (agent_id, name, version, capabilities, protocols, endpoints, 
                     metadata, status, last_heartbeat, load_score, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    agent_card.agent_id,
                    agent_card.name,
                    agent_card.version,
                    json.dumps(agent_card.capabilities),
                    json.dumps(agent_card.protocols),
                    json.dumps(agent_card.endpoints),
                    json.dumps(agent_card.metadata) if agent_card.metadata else None,
                    agent_card.status.value,
                    agent_card.last_heartbeat.isoformat(),
                    agent_card.load_score
                ))
                
                # Indexar capacidades
                conn.execute("DELETE FROM agent_capabilities WHERE agent_id = ?", 
                           (agent_card.agent_id,))
                
                for capability in agent_card.capabilities:
                    conn.execute("""
                        INSERT INTO agent_capabilities (agent_id, capability)
                        VALUES (?, ?)
                    """, (agent_card.agent_id, capability))
            
            self.agents[agent_card.agent_id] = agent_card
            logger.info(f"Agent {agent_card.agent_id} registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
            return False

    async def discover_agents_for_task(self, task_type: str, required_capabilities: List[str] = None) -> List[AgentCard]:
        """Descubrir agentes capaces de realizar una tarea específica"""
        candidates = []
        
        # Si se especifican capacidades, filtrar por ellas
        if required_capabilities:
            for agent in self.agents.values():
                if agent.status == AgentStatus.ONLINE:
                    capability_match = len(set(required_capabilities) & set(agent.capabilities))
                    if capability_match > 0:
                        # Score basado en capacidades coincidentes y carga actual
                        score = capability_match / len(required_capabilities) * (1 - agent.load_score)
                        candidates.append((agent, score))
        else:
            # Buscar por tipo de tarea en capacidades
            for agent in self.agents.values():
                if agent.status == AgentStatus.ONLINE and task_type in agent.capabilities:
                    score = 1 - agent.load_score
                    candidates.append((agent, score))
        
        # Ordenar por score descendente
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        return [agent for agent, score in candidates]

    async def _health_check(self, health_endpoint: str) -> bool:
        """Verificar salud de un agente"""
        try:
            async with ClientSession() as session:
                async with session.get(health_endpoint, timeout=5) as response:
                    return response.status == 200
        except Exception as e:
            logger.debug(f"Health check failed for {health_endpoint}: {e}")
            return False

    async def update_agent_load(self, agent_id: str, load_score: float):
        """Actualizar carga de trabajo de un agente"""
        if agent_id in self.agents:
            self.agents[agent_id].load_score = load_score
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE agents SET load_score = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE agent_id = ?
                """, (load_score, agent_id))

    def get_agent(self, agent_id: str) -> Optional[AgentCard]:
        """Obtener información de un agente específico"""
        return self.agents.get(agent_id)

    def list_agents(self, status: Optional[AgentStatus] = None) -> List[AgentCard]:
        """Listar agentes, opcionalmente filtrados por estado"""
        if status:
            return [agent for agent in self.agents.values() if agent.status == status]
        return list(self.agents.values())

class A2ATaskManager:
    """Gestor de tareas A2A con persistencia y estado"""
    
    def __init__(self, db_path: str = "data/a2a_tasks.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self.active_tasks: Dict[str, A2ATask] = {}

    def _init_database(self):
        """Inicializar esquema de base de datos para tareas"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    requester_id TEXT NOT NULL,
                    assigned_agent_id TEXT,
                    priority INTEGER DEFAULT 5,
                    timeout INTEGER DEFAULT 300,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    result TEXT,
                    error TEXT,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_status ON tasks (status)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_type ON tasks (task_type)
            """)

    async def create_task(self, task_data: Dict[str, Any]) -> A2ATask:
        """Crear nueva tarea A2A"""
        # Validar schema
        jsonschema.validate(task_data, A2A_TASK_SCHEMA)
        
        task = A2ATask(
            task_id=task_data.get('task_id', str(uuid.uuid4())),
            task_type=task_data['task_type'],
            payload=task_data['payload'],
            requester_id=task_data['requester_id'],
            priority=task_data.get('priority', 5),
            timeout=task_data.get('timeout', 300),
            created_at=datetime.utcnow(),
            metadata=task_data.get('metadata')
        )
        
        # Persistir en base de datos
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO tasks 
                (task_id, task_type, payload, requester_id, priority, timeout, 
                 status, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.task_id, task.task_type, json.dumps(task.payload),
                task.requester_id, task.priority, task.timeout,
                task.status.value, task.created_at.isoformat(),
                json.dumps(task.metadata) if task.metadata else None
            ))
        
        self.active_tasks[task.task_id] = task
        logger.info(f"Task {task.task_id} created")
        return task

    async def assign_task(self, task_id: str, agent_id: str) -> bool:
        """Asignar tarea a un agente específico"""
        if task_id not in self.active_tasks:
            return False
        
        task = self.active_tasks[task_id]
        task.assigned_agent_id = agent_id
        task.status = TaskStatus.IN_PROGRESS
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE tasks SET assigned_agent_id = ?, status = ?
                WHERE task_id = ?
            """, (agent_id, task.status.value, task_id))
        
        logger.info(f"Task {task_id} assigned to agent {agent_id}")
        return True

    async def complete_task(self, task_id: str, result: Dict[str, Any]) -> bool:
        """Marcar tarea como completada con resultado"""
        if task_id not in self.active_tasks:
            return False
        
        task = self.active_tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.result = result
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE tasks SET status = ?, completed_at = ?, result = ?
                WHERE task_id = ?
            """, (task.status.value, task.completed_at.isoformat(), 
                  json.dumps(result), task_id))
        
        logger.info(f"Task {task_id} completed")
        return True

    async def fail_task(self, task_id: str, error: str) -> bool:
        """Marcar tarea como fallida"""
        if task_id not in self.active_tasks:
            return False
        
        task = self.active_tasks[task_id]
        task.status = TaskStatus.FAILED
        task.completed_at = datetime.utcnow()
        task.error = error
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE tasks SET status = ?, completed_at = ?, error = ?
                WHERE task_id = ?
            """, (task.status.value, task.completed_at.isoformat(), error, task_id))
        
        logger.error(f"Task {task_id} failed: {error}")
        return True

    def get_task(self, task_id: str) -> Optional[A2ATask]:
        """Obtener información de una tarea"""
        return self.active_tasks.get(task_id)

class SuperMCPA2AServer:
    """Servidor principal A2A para SUPERmcp"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8200):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.agent_registry = AgentRegistry()
        self.task_manager = A2ATaskManager()
        self._setup_routes()
        
        # Registrar agentes SUPERmcp existentes
        asyncio.create_task(self._register_supermcp_agents())

    def _setup_routes(self):
        """Configurar rutas HTTP para A2A"""
        # A2A Protocol Routes
        self.app.router.add_post('/a2a/discover', self.handle_agent_discovery)
        self.app.router.add_post('/a2a/delegate', self.handle_task_delegation)
        self.app.router.add_get('/a2a/task/{task_id}', self.handle_task_status)
        self.app.router.add_post('/a2a/task/{task_id}/complete', self.handle_task_completion)
        
        # Agent Management Routes
        self.app.router.add_post('/agents/register', self.handle_agent_registration)
        self.app.router.add_get('/agents', self.handle_list_agents)
        self.app.router.add_get('/agents/{agent_id}', self.handle_get_agent)
        self.app.router.add_post('/agents/{agent_id}/heartbeat', self.handle_agent_heartbeat)
        
        # System Routes
        self.app.router.add_get('/health', self.handle_health)
        self.app.router.add_get('/metrics', self.handle_metrics)

    async def _register_supermcp_agents(self):
        """Registrar agentes SUPERmcp existentes como agentes A2A"""
        await asyncio.sleep(2)  # Esperar que otros servicios inicien
        
        # Agente Manus (Orchestrator)
        manus_card = {
            "agent_id": "manus_orchestrator_v2",
            "name": "Manus Orchestrator Agent",
            "version": "2.0.0",
            "capabilities": [
                "orchestration",
                "task_planning", 
                "delegation",
                "workflow_management",
                "agent_coordination"
            ],
            "protocols": ["mcp", "a2a"],
            "endpoints": {
                "a2a": "http://65.109.54.94:3000/a2a",
                "health": "http://65.109.54.94:3000/health"
            },
            "metadata": {
                "description": "Central orchestrator for SUPERmcp system",
                "max_concurrent_tasks": 100,
                "specialization": "coordination"
            }
        }
        
        # Agente SAM (Executor)
        sam_card = {
            "agent_id": "sam_executor_v2", 
            "name": "SAM Autonomous Executor",
            "version": "2.0.0",
            "capabilities": [
                "document_analysis",
                "autonomous_execution",
                "web_scraping",
                "data_processing", 
                "content_generation",
                "memory_analysis"
            ],
            "protocols": ["mcp", "a2a"],
            "endpoints": {
                "a2a": "http://65.109.54.94:3001/a2a",
                "health": "http://65.109.54.94:3001/health"
            },
            "metadata": {
                "description": "Autonomous executor with advanced AI capabilities",
                "max_concurrent_tasks": 50,
                "specialization": "execution"
            }
        }
        
        # Agente Memory (Semantic Memory)
        memory_card = {
            "agent_id": "memory_analyzer_v2",
            "name": "Memory Analyzer Agent", 
            "version": "2.0.0",
            "capabilities": [
                "semantic_memory",
                "embedding_search",
                "context_retrieval",
                "memory_storage",
                "similarity_search"
            ],
            "protocols": ["mcp", "a2a"],
            "endpoints": {
                "a2a": "http://65.109.54.94:3000/memory/a2a",
                "health": "http://65.109.54.94:3000/memory/health"
            },
            "metadata": {
                "description": "Semantic memory and context management",
                "vector_dimensions": 1536,
                "specialization": "memory"
            }
        }
        
        # Registrar agentes
        agents = [manus_card, sam_card, memory_card]
        for agent_card in agents:
            success = await self.agent_registry.register_agent(agent_card)
            logger.info(f"SUPERmcp agent {agent_card['agent_id']} registration: {success}")

    async def handle_agent_discovery(self, request):
        """Manejar solicitudes de descubrimiento de agentes"""
        try:
            data = await request.json()
            task_type = data.get('task_type')
            required_capabilities = data.get('capabilities', [])
            
            agents = await self.agent_registry.discover_agents_for_task(
                task_type, required_capabilities
            )
            
            agent_cards = [asdict(agent) for agent in agents[:5]]  # Top 5
            
            return web.json_response({
                "success": True,
                "agents": agent_cards,
                "count": len(agent_cards)
            })
            
        except Exception as e:
            logger.error(f"Agent discovery error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def handle_task_delegation(self, request):
        """Manejar delegación de tareas entre agentes"""
        try:
            data = await request.json()
            
            # Crear tarea
            task = await self.task_manager.create_task(data)
            
            # Descubrir agentes apropiados
            agents = await self.agent_registry.discover_agents_for_task(
                task.task_type, data.get('required_capabilities', [])
            )
            
            if not agents:
                await self.task_manager.fail_task(task.task_id, "No suitable agents found")
                return web.json_response({
                    "success": False,
                    "task_id": task.task_id,
                    "error": "No suitable agents found"
                }, status=404)
            
            # Asignar al mejor agente
            best_agent = agents[0]
            await self.task_manager.assign_task(task.task_id, best_agent.agent_id)
            
            # Delegar tarea al agente (llamada A2A real)
            delegation_result = await self._delegate_to_agent(best_agent, task)
            
            return web.json_response({
                "success": True,
                "task_id": task.task_id,
                "assigned_agent": best_agent.agent_id,
                "delegation_status": delegation_result
            })
            
        except Exception as e:
            logger.error(f"Task delegation error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def _delegate_to_agent(self, agent: AgentCard, task: A2ATask) -> Dict[str, Any]:
        """Delegar tarea a un agente específico usando A2A"""
        try:
            async with ClientSession() as session:
                delegation_payload = {
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "payload": task.payload,
                    "requester_id": task.requester_id,
                    "priority": task.priority,
                    "timeout": task.timeout
                }
                
                async with session.post(
                    agent.endpoints['a2a'], 
                    json=delegation_payload,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {"success": True, "response": result}
                    else:
                        error_text = await response.text()
                        await self.task_manager.fail_task(
                            task.task_id, 
                            f"Agent delegation failed: {error_text}"
                        )
                        return {"success": False, "error": error_text}
                        
        except Exception as e:
            await self.task_manager.fail_task(task.task_id, f"Delegation error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def handle_task_status(self, request):
        """Obtener estado de una tarea"""
        task_id = request.match_info['task_id']
        task = self.task_manager.get_task(task_id)
        
        if not task:
            return web.json_response({
                "success": False,
                "error": "Task not found"
            }, status=404)
        
        return web.json_response({
            "success": True,
            "task": asdict(task)
        })

    async def handle_task_completion(self, request):
        """Manejar completación de tarea por parte de un agente"""
        try:
            task_id = request.match_info['task_id']
            data = await request.json()
            
            if data.get('success', True):
                await self.task_manager.complete_task(task_id, data.get('result', {}))
            else:
                await self.task_manager.fail_task(task_id, data.get('error', 'Unknown error'))
            
            return web.json_response({"success": True})
            
        except Exception as e:
            logger.error(f"Task completion error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def handle_agent_registration(self, request):
        """Registrar nuevo agente A2A"""
        try:
            agent_data = await request.json()
            success = await self.agent_registry.register_agent(agent_data)
            
            return web.json_response({
                "success": success,
                "agent_id": agent_data.get('agent_id')
            })
            
        except Exception as e:
            logger.error(f"Agent registration error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=400)

    async def handle_list_agents(self, request):
        """Listar todos los agentes registrados"""
        status_filter = request.query.get('status')
        status = AgentStatus(status_filter) if status_filter else None
        
        agents = self.agent_registry.list_agents(status)
        agent_cards = [asdict(agent) for agent in agents]
        
        return web.json_response({
            "success": True,
            "agents": agent_cards,
            "count": len(agent_cards)
        })

    async def handle_get_agent(self, request):
        """Obtener información de un agente específico"""
        agent_id = request.match_info['agent_id']
        agent = self.agent_registry.get_agent(agent_id)
        
        if not agent:
            return web.json_response({
                "success": False,
                "error": "Agent not found"
            }, status=404)
        
        return web.json_response({
            "success": True,
            "agent": asdict(agent)
        })

    async def handle_agent_heartbeat(self, request):
        """Procesar heartbeat de agente"""
        agent_id = request.match_info['agent_id']
        data = await request.json()
        
        load_score = data.get('load_score', 0.0)
        await self.agent_registry.update_agent_load(agent_id, load_score)
        
        return web.json_response({"success": True})

    async def handle_health(self, request):
        """Health check del sistema A2A"""
        agent_count = len(self.agent_registry.list_agents(AgentStatus.ONLINE))
        
        return web.json_response({
            "status": "healthy",
            "service": "SUPERmcp A2A Server",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "agents_online": agent_count
        })

    async def handle_metrics(self, request):
        """Métricas del sistema A2A"""
        agents = self.agent_registry.list_agents()
        online_agents = len([a for a in agents if a.status == AgentStatus.ONLINE])
        
        # Contar tareas por estado
        task_counts = {status.value: 0 for status in TaskStatus}
        for task in self.task_manager.active_tasks.values():
            task_counts[task.status.value] += 1
        
        return web.json_response({
            "agents": {
                "total": len(agents),
                "online": online_agents,
                "offline": len(agents) - online_agents
            },
            "tasks": task_counts,
            "system": {
                "uptime": time.time(),
                "version": "1.0.0"
            }
        })

    async def start_server(self):
        """Iniciar servidor A2A"""
        logger.info(f"Starting SUPERmcp A2A Server on {self.host}:{self.port}")
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info("SUPERmcp A2A Server started successfully")

async def main():
    """Función principal"""
    server = SuperMCPA2AServer()
    await server.start_server()
    
    # Mantener servidor corriendo
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down SUPERmcp A2A Server")

if __name__ == "__main__":
    asyncio.run(main())