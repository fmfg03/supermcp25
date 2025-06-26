#!/usr/bin/env python3
"""
GoogleAI A2A Agent - Integración completa con Google AI Studio
Agente especializado que expone capacidades de Google AI via protocolo A2A

Author: Manus AI  
Date: June 25, 2025
Version: 1.0.0
"""

import asyncio
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from aiohttp import ClientSession, web
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import os
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GoogleAICapability:
    """Capacidad específica de Google AI"""
    name: str
    model: str
    description: str
    input_types: List[str]
    output_types: List[str]
    rate_limit: Dict[str, int]

class GoogleAIA2AAgent:
    """Agente A2A que integra Google AI Studio completamente"""
    
    def __init__(self, api_key: str, port: int = 8213, a2a_server_url: str = "http://localhost:8200"):
        self.agent_id = "googleai_agent_v1"
        self.name = "Google AI Studio Agent"
        self.port = port
        self.a2a_server_url = a2a_server_url
        self.api_key = api_key
        self.app = web.Application()
        
        # Configurar Google AI
        genai.configure(api_key=api_key)
        
        # Inicializar modelos disponibles
        self.models = self._initialize_models()
        
        # Capacidades del agente
        self.capabilities = [
            "text_generation", "text_analysis", "content_creation",
            "code_generation", "code_explanation", "translation",
            "summarization", "question_answering", "sentiment_analysis",
            "image_analysis", "vision_processing", "multimodal_analysis",
            "embedding_generation", "similarity_search", "classification"
        ]
        
        # Configurar rutas HTTP
        self._setup_routes()
        
        # Estado del agente
        self.is_registered = False
        self.active_tasks: Dict[str, Any] = {}
        self.task_history: List[Dict[str, Any]] = []
        
    def _initialize_models(self) -> Dict[str, Any]:
        """Inicializar modelos disponibles de Google AI"""
        return {
            "gemini-pro": {
                "instance": genai.GenerativeModel('gemini-pro'),
                "capabilities": ["text_generation", "analysis", "reasoning"],
                "max_tokens": 30720,
                "supports_vision": False
            },
            "gemini-pro-vision": {
                "instance": genai.GenerativeModel('gemini-pro-vision'),  
                "capabilities": ["image_analysis", "vision_processing", "multimodal"],
                "max_tokens": 30720,
                "supports_vision": True
            },
            "text-embedding-004": {
                "instance": "embedding_model",
                "capabilities": ["embedding_generation", "similarity_search"],
                "dimensions": 768,
                "supports_vision": False
            }
        }
    
    def _setup_routes(self):
        """Configurar rutas HTTP para A2A"""
        # Rutas A2A principales
        self.app.router.add_post('/a2a', self.handle_a2a_task)
        self.app.router.add_get('/health', self.handle_health)
        self.app.router.add_get('/capabilities', self.handle_capabilities)
        
        # Rutas específicas de Google AI
        self.app.router.add_post('/ai/generate', self.handle_text_generation)
        self.app.router.add_post('/ai/analyze', self.handle_analysis)
        self.app.router.add_post('/ai/vision', self.handle_vision_analysis)
        self.app.router.add_post('/ai/embed', self.handle_embedding)
        self.app.router.add_post('/ai/translate', self.handle_translation)
        
        # Rutas de gestión
        self.app.router.add_get('/models', self.handle_list_models)
        self.app.router.add_get('/tasks', self.handle_list_tasks)
        self.app.router.add_get('/metrics', self.handle_metrics)
    
    async def register_with_a2a_server(self) -> bool:
        """Registrar agente con el servidor A2A central"""
        agent_card = {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": "1.0.0",
            "capabilities": self.capabilities,
            "protocols": ["a2a", "http"],
            "endpoints": {
                "a2a": f"http://65.109.54.94:{self.port}/a2a",
                "health": f"http://65.109.54.94:{self.port}/health"
            },
            "metadata": {
                "description": "Google AI Studio integration with Gemini Pro/Vision",
                "provider": "Google",
                "models": list(self.models.keys()),
                "specialization": "ai_models",
                "rate_limits": {
                    "requests_per_minute": 60,
                    "tokens_per_minute": 1000000
                }
            }
        }
        
        try:
            async with ClientSession() as session:
                async with session.post(
                    f"{self.a2a_server_url}/agents/register",
                    json=agent_card
                ) as response:
                    if response.status == 200:
                        self.is_registered = True
                        logger.info(f"GoogleAI Agent registered successfully")
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"Registration failed: {error}")
                        return False
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False
    
    async def handle_a2a_task(self, request):
        """Manejar tareas delegadas via protocolo A2A"""
        try:
            task_data = await request.json()
            task_id = task_data.get('task_id', str(uuid.uuid4()))
            task_type = task_data.get('task_type', 'general')
            payload = task_data.get('payload', {})
            
            # Registrar tarea activa
            self.active_tasks[task_id] = {
                "task_id": task_id,
                "task_type": task_type,
                "status": "processing",
                "started_at": datetime.utcnow().isoformat(),
                "requester_id": task_data.get('requester_id')
            }
            
            logger.info(f"GoogleAI processing A2A task: {task_type}")
            
            # Procesar según tipo de tarea
            result = await self._process_a2a_task(task_type, payload)
            
            # Actualizar estado de tarea
            self.active_tasks[task_id]["status"] = "completed"
            self.active_tasks[task_id]["completed_at"] = datetime.utcnow().isoformat()
            self.active_tasks[task_id]["result"] = result
            
            # Mover a historial
            self.task_history.append(self.active_tasks[task_id])
            del self.active_tasks[task_id]
            
            return web.json_response({
                "success": True,
                "task_id": task_id,
                "result": result
            })
            
        except Exception as e:
            logger.error(f"A2A task error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def _process_a2a_task(self, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar tarea específica de Google AI"""
        
        if task_type in ["text_generation", "content_creation"]:
            return await self._handle_text_generation(payload)
        
        elif task_type in ["text_analysis", "sentiment_analysis"]:
            return await self._handle_text_analysis(payload)
        
        elif task_type in ["image_analysis", "vision_processing"]:
            return await self._handle_vision_processing(payload)
        
        elif task_type in ["translation", "language_translation"]:
            return await self._handle_translation_task(payload)
        
        elif task_type in ["embedding_generation", "embeddings"]:
            return await self._handle_embedding_generation(payload)
        
        elif task_type in ["code_generation", "code_explanation"]:
            return await self._handle_code_tasks(payload)
        
        elif task_type in ["summarization", "summary"]:
            return await self._handle_summarization(payload)
        
        else:
            # Fallback: texto general con Gemini Pro
            return await self._handle_general_task(payload)
    
    async def _handle_text_generation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generar texto usando Gemini Pro"""
        try:
            prompt = payload.get('prompt', payload.get('text', ''))
            model_name = payload.get('model', 'gemini-pro')
            max_tokens = payload.get('max_tokens', 1000)
            temperature = payload.get('temperature', 0.7)
            
            model = self.models[model_name]["instance"]
            
            # Configurar parámetros de generación
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
                top_p=0.8,
                top_k=40
            )
            
            # Generar respuesta
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config=generation_config
            )
            
            return {
                "text_generation_completed": True,
                "generated_text": response.text,
                "model_used": model_name,
                "tokens_used": len(response.text.split()),
                "finish_reason": "completed"
            }
            
        except Exception as e:
            logger.error(f"Text generation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_text_analysis(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analizar texto con Gemini Pro"""
        try:
            text = payload.get('text', '')
            analysis_type = payload.get('analysis_type', 'general')
            
            if analysis_type == 'sentiment':
                prompt = f"""Analiza el sentimiento del siguiente texto y proporciona:
1. Sentimiento principal (positivo/negativo/neutral)
2. Puntuación de confianza (0-1)
3. Emociones detectadas
4. Justificación del análisis

Texto: "{text}"
"""
            elif analysis_type == 'entities':
                prompt = f"""Extrae y categoriza todas las entidades del siguiente texto:
1. Personas
2. Organizaciones  
3. Ubicaciones
4. Fechas
5. Conceptos clave

Texto: "{text}"
"""
            else:
                prompt = f"""Realiza un análisis comprehensivo del siguiente texto incluyendo:
1. Tema principal
2. Puntos clave
3. Tono y estilo
4. Estructura
5. Insights relevantes

Texto: "{text}"
"""
            
            model = self.models["gemini-pro"]["instance"]
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            return {
                "text_analysis_completed": True,
                "analysis_type": analysis_type,
                "analysis_result": response.text,
                "input_text_length": len(text),
                "model_used": "gemini-pro"
            }
            
        except Exception as e:
            logger.error(f"Text analysis error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_vision_processing(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar imágenes con Gemini Vision"""
        try:
            image_url = payload.get('image_url', '')
            image_data = payload.get('image_data', '')
            analysis_prompt = payload.get('prompt', 'Describe esta imagen en detalle')
            
            if not image_url and not image_data:
                return {"success": False, "error": "No image provided"}
            
            model = self.models["gemini-pro-vision"]["instance"]
            
            # Preparar input multimodal
            if image_url:
                # Descargar imagen si es URL
                async with ClientSession() as session:
                    async with session.get(image_url) as resp:
                        image_content = await resp.read()
            else:
                # Usar datos de imagen directamente
                import base64
                image_content = base64.b64decode(image_data)
            
            # Procesar con Gemini Vision
            response = await asyncio.to_thread(
                model.generate_content,
                [analysis_prompt, {"mime_type": "image/jpeg", "data": image_content}]
            )
            
            return {
                "vision_analysis_completed": True,
                "analysis_result": response.text,
                "image_source": "url" if image_url else "data",
                "model_used": "gemini-pro-vision"
            }
            
        except Exception as e:
            logger.error(f"Vision processing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_translation_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Traducir texto usando Gemini Pro"""
        try:
            text = payload.get('text', '')
            target_language = payload.get('target_language', 'Spanish')
            source_language = payload.get('source_language', 'auto-detect')
            
            prompt = f"""Traduce el siguiente texto a {target_language}. 
Mantén el tono y el contexto original.

Texto a traducir: "{text}"

Proporciona solo la traducción, sin explicaciones adicionales."""
            
            model = self.models["gemini-pro"]["instance"]
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            return {
                "translation_completed": True,
                "translated_text": response.text,
                "source_language": source_language,
                "target_language": target_language,
                "original_text": text
            }
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_embedding_generation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generar embeddings usando Google AI"""
        try:
            text = payload.get('text', '')
            model_name = 'models/text-embedding-004'
            
            # Generar embedding
            embedding_result = await asyncio.to_thread(
                genai.embed_content,
                model=model_name,
                content=text,
                task_type="retrieval_document"
            )
            
            return {
                "embedding_generated": True,
                "embedding": embedding_result['embedding'],
                "dimensions": len(embedding_result['embedding']),
                "text_length": len(text),
                "model_used": model_name
            }
            
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_code_tasks(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Manejar tareas relacionadas con código"""
        try:
            task_subtype = payload.get('subtype', 'generation')
            code = payload.get('code', '')
            language = payload.get('language', 'python')
            prompt = payload.get('prompt', '')
            
            if task_subtype == 'generation':
                full_prompt = f"""Genera código en {language} para: {prompt}
                
Proporciona:
1. Código completo y funcional
2. Comentarios explicativos
3. Ejemplo de uso
4. Dependencias necesarias
"""
            else:  # explanation
                full_prompt = f"""Explica el siguiente código en {language}:
                
```{language}
{code}
```

Proporciona:
1. Explicación línea por línea
2. Propósito general del código
3. Optimizaciones posibles
4. Posibles mejoras
"""
            
            model = self.models["gemini-pro"]["instance"]
            response = await asyncio.to_thread(model.generate_content, full_prompt)
            
            return {
                "code_task_completed": True,
                "task_subtype": task_subtype,
                "language": language,
                "result": response.text,
                "model_used": "gemini-pro"
            }
            
        except Exception as e:
            logger.error(f"Code task error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_summarization(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Resumir texto con Gemini Pro"""
        try:
            text = payload.get('text', '')
            summary_length = payload.get('length', 'medium')
            style = payload.get('style', 'professional')
            
            length_instructions = {
                'short': 'en 2-3 oraciones',
                'medium': 'en 1-2 párrafos', 
                'long': 'en 3-4 párrafos detallados'
            }
            
            prompt = f"""Resume el siguiente texto {length_instructions.get(summary_length, 'brevemente')} 
con un estilo {style}. Incluye los puntos más importantes y mantén la información clave.

Texto: "{text}"
"""
            
            model = self.models["gemini-pro"]["instance"]
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            return {
                "summarization_completed": True,
                "summary": response.text,
                "original_length": len(text),
                "summary_length": len(response.text),
                "compression_ratio": round(len(response.text) / len(text), 2)
            }
            
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_general_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Manejar tarea general con Gemini Pro"""
        try:
            prompt = payload.get('prompt', payload.get('query', payload.get('text', '')))
            
            model = self.models["gemini-pro"]["instance"]
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            return {
                "general_task_completed": True,
                "response": response.text,
                "model_used": "gemini-pro"
            }
            
        except Exception as e:
            logger.error(f"General task error: {e}")
            return {"success": False, "error": str(e)}
    
    async def handle_health(self, request):
        """Health check del agente"""
        return web.json_response({
            "status": "healthy",
            "agent_id": self.agent_id,
            "version": "1.0.0",
            "capabilities": self.capabilities,
            "models_available": list(self.models.keys()),
            "active_tasks": len(self.active_tasks),
            "total_tasks_processed": len(self.task_history),
            "registered_with_a2a": self.is_registered
        })
    
    async def handle_capabilities(self, request):
        """Listar capacidades del agente"""
        return web.json_response({
            "agent_id": self.agent_id,
            "capabilities": self.capabilities,
            "specializations": [
                "text_generation", "image_analysis", "translation",
                "embedding_generation", "code_tasks", "summarization"
            ],
            "models": {
                model_name: {
                    "capabilities": model_info["capabilities"],
                    "supports_vision": model_info.get("supports_vision", False)
                }
                for model_name, model_info in self.models.items()
            }
        })
    
    async def handle_metrics(self, request):
        """Métricas del agente"""
        completed_tasks = len(self.task_history)
        active_tasks = len(self.active_tasks)
        
        # Calcular estadísticas básicas
        if self.task_history:
            avg_duration = sum(
                (datetime.fromisoformat(task.get("completed_at", task["started_at"])) - 
                 datetime.fromisoformat(task["started_at"])).total_seconds()
                for task in self.task_history if task.get("completed_at")
            ) / len([t for t in self.task_history if t.get("completed_at")])
        else:
            avg_duration = 0
        
        return web.json_response({
            "metrics": {
                "tasks_completed": completed_tasks,
                "tasks_active": active_tasks,
                "success_rate": 0.95,  # Placeholder
                "average_duration_seconds": round(avg_duration, 2),
                "models_used": list(self.models.keys()),
                "uptime_hours": 1.0  # Placeholder
            },
            "performance": {
                "requests_per_minute": 12,  # Placeholder
                "tokens_generated": 15420,  # Placeholder
                "api_calls_made": completed_tasks
            }
        })
    
    async def send_heartbeat(self):
        """Enviar heartbeat al servidor A2A"""
        if not self.is_registered:
            return False
        
        try:
            load_score = len(self.active_tasks) / 10.0  # Score basado en tareas activas
            
            async with ClientSession() as session:
                async with session.post(
                    f"{self.a2a_server_url}/agents/{self.agent_id}/heartbeat",
                    json={"load_score": load_score}
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.debug(f"Heartbeat error: {e}")
            return False
    
    async def start_server(self):
        """Iniciar servidor HTTP del agente"""
        logger.info(f"Starting GoogleAI A2A Agent on port {self.port}")
        
        # Registrar con servidor A2A
        registration_success = await self.register_with_a2a_server()
        if registration_success:
            logger.info("Successfully registered with A2A Central Server")
        else:
            logger.warning("Failed to register with A2A server, continuing anyway")
        
        # Iniciar servidor HTTP
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self.port)
        await site.start()
        
        logger.info(f"GoogleAI Agent available at http://localhost:{self.port}")
        
        # Iniciar heartbeat en background
        asyncio.create_task(self._heartbeat_loop())
    
    async def _heartbeat_loop(self):
        """Loop de heartbeat"""
        while True:
            await asyncio.sleep(30)  # Heartbeat cada 30 segundos
            await self.send_heartbeat()

async def main():
    """Función principal"""
    # Obtener API key de Google AI
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        logger.error("GOOGLE_API_KEY environment variable not set")
        return
    
    # Crear y iniciar agente
    agent = GoogleAIA2AAgent(api_key=api_key)
    await agent.start_server()
    
    print(f"""
🚀 GoogleAI A2A Agent Started Successfully!
==========================================

📊 Agent Details:
   ID: {agent.agent_id}
   Port: {agent.port}
   Capabilities: {len(agent.capabilities)}
   Models: {list(agent.models.keys())}

🌐 Endpoints:
   A2A: http://localhost:{agent.port}/a2a
   Health: http://localhost:{agent.port}/health
   Capabilities: http://localhost:{agent.port}/capabilities

🤖 Available Models:
   • Gemini Pro (Text generation & analysis)
   • Gemini Pro Vision (Image analysis)
   • Text Embedding 004 (Embeddings)

✨ Ready for A2A task delegation!
""")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down GoogleAI A2A Agent")

if __name__ == "__main__":
    asyncio.run(main())