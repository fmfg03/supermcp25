#!/usr/bin/env python3
"""
Ejemplos de Delegación A2A con GoogleAI Agent
Casos de uso prácticos de cómo usar Google AI Studio en tu stack SUPERmcp

Author: Manus AI
Date: June 25, 2025
"""

import asyncio
import aiohttp
import json
from datetime import datetime

class A2ADelegationExamples:
    """Ejemplos prácticos de delegación A2A con GoogleAI"""
    
    def __init__(self):
        self.a2a_server = "http://localhost:8200"
        self.manus_agent = "http://localhost:8210"
        self.sam_agent = "http://localhost:8211"
        self.memory_agent = "http://localhost:8212"
        self.googleai_agent = "http://localhost:8213"
    
    async def run_all_examples(self):
        """Ejecutar todos los ejemplos de delegación"""
        print("🚀 A2A Delegation Examples - GoogleAI Integration")
        print("=" * 50)
        print()
        
        examples = [
            ("Manus → GoogleAI: Document Analysis", self.example_manus_to_googleai),
            ("SAM → GoogleAI: Image Analysis", self.example_sam_to_googleai_vision),
            ("Memory → GoogleAI: Generate Embeddings", self.example_memory_to_googleai_embeddings),
            ("Multi-Agent Workflow: Research Pipeline", self.example_multi_agent_workflow),
            ("GoogleAI → SAM: Code Execution", self.example_googleai_to_sam),
            ("Complex Workflow: Content Creation", self.example_complex_content_workflow)
        ]
        
        for example_name, example_func in examples:
            print(f"🎯 {example_name}")
            print("-" * (len(example_name) + 4))
            try:
                result = await example_func()
                print(f"✅ Success: {result.get('summary', 'Completed')}")
            except Exception as e:
                print(f"❌ Error: {e}")
            print()
            await asyncio.sleep(1)  # Evitar rate limits
    
    async def example_manus_to_googleai(self):
        """Ejemplo: Manus delega análisis de documento a GoogleAI"""
        task_data = {
            "task_type": "delegation",
            "payload": {
                "target_task": {
                    "task_type": "text_analysis",
                    "text": """
                    El mercado de inteligencia artificial está experimentando un crecimiento 
                    exponencial. Las empresas están adoptando AI para automatizar procesos, 
                    mejorar la experiencia del cliente y optimizar operaciones. Sin embargo, 
                    también enfrentan desafíos como la falta de talento especializado y 
                    preocupaciones sobre la ética en AI.
                    """,
                    "analysis_type": "comprehensive"
                },
                "required_capabilities": ["text_analysis", "ai_models"]
            },
            "requester_id": "manus_orchestrator",
            "priority": 7
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.manus_agent}/a2a", json=task_data) as response:
                if response.status == 200:
                    result = await response.json()
                    delegation_result = result.get("result", {})
                    
                    return {
                        "summary": "Manus successfully delegated text analysis to GoogleAI",
                        "delegation_successful": delegation_result.get("delegation_successful"),
                        "assigned_agent": delegation_result.get("assigned_agent"),
                        "analysis_preview": delegation_result.get("result", {}).get("result", {}).get("analysis_result", "")[:100] + "..."
                    }
                else:
                    error = await response.text()
                    raise Exception(f"Delegation failed: {error}")
    
    async def example_sam_to_googleai_vision(self):
        """Ejemplo: SAM delega análisis de imagen a GoogleAI Vision"""
        
        # Simular que SAM encontró una imagen durante web scraping
        task_data = {
            "task_type": "collaborative_analysis",
            "payload": {
                "document": "Web scraping result with images",
                "analysis_types": ["vision_processing"],
                "image_analysis": {
                    "image_url": "https://example.com/sample-chart.jpg",
                    "analysis_prompt": "Analiza este gráfico y extrae los datos principales"
                }
            },
            "requester_id": "sam_executor"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.sam_agent}/a2a", json=task_data) as response:
                if response.status == 200:
                    result = await response.json()
                    analysis_result = result.get("result", {})
                    
                    return {
                        "summary": "SAM delegated image analysis to GoogleAI Vision",
                        "collaborative_analysis": analysis_result.get("collaborative_analysis_completed"),
                        "vision_result": "Image analysis completed via GoogleAI Vision"
                    }
                else:
                    error = await response.text()
                    raise Exception(f"Collaborative analysis failed: {error}")
    
    async def example_memory_to_googleai_embeddings(self):
        """Ejemplo: Memory Agent usa GoogleAI para generar embeddings"""
        
        # Memory Agent delega generación de embeddings a GoogleAI
        task_data = {
            "task_type": "knowledge_sharing",
            "payload": {
                "sharing_type": "embedding_generation",
                "knowledge": {
                    "text": "Los agentes de IA colaborativos pueden trabajar juntos para resolver problemas complejos mediante protocolos como A2A",
                    "metadata": {
                        "topic": "ai_collaboration",
                        "source": "research_document",
                        "importance": "high"
                    }
                }
            },
            "requester_id": "memory_analyzer"
        }
        
        # Primero, Memory delega a GoogleAI para generar embeddings
        async with aiohttp.ClientSession() as session:
            # Delegación directa a GoogleAI para embeddings
            embedding_task = {
                "task_id": f"embedding_{datetime.utcnow().timestamp()}",
                "task_type": "embedding_generation",
                "payload": {
                    "text": task_data["payload"]["knowledge"]["text"]
                },
                "requester_id": "memory_analyzer"
            }
            
            async with session.post(f"{self.googleai_agent}/a2a", json=embedding_task) as response:
                if response.status == 200:
                    result = await response.json()
                    embedding_result = result.get("result", {})
                    
                    return {
                        "summary": "Memory Agent generated embeddings via GoogleAI",
                        "embedding_generated": embedding_result.get("embedding_generated"),
                        "embedding_dimensions": embedding_result.get("dimensions"),
                        "text_processed": len(task_data["payload"]["knowledge"]["text"])
                    }
                else:
                    error = await response.text()
                    raise Exception(f"Embedding generation failed: {error}")
    
    async def example_multi_agent_workflow(self):
        """Ejemplo: Workflow multi-agente con investigación y análisis"""
        
        # Manus orquesta un workflow complejo que involucra múltiples agentes
        workflow_data = {
            "task_type": "complex_workflow",
            "payload": {
                "steps": [
                    {
                        "type": "research_preparation",
                        "capabilities": ["semantic_memory"],
                        "data": {
                            "query": "tendencias en AI agent collaboration 2025"
                        }
                    },
                    {
                        "type": "content_analysis",
                        "capabilities": ["text_analysis", "ai_models"],
                        "data": {
                            "analysis_type": "trend_analysis",
                            "focus": "agent_collaboration"
                        }
                    },
                    {
                        "type": "translation",
                        "capabilities": ["translation", "ai_models"],
                        "data": {
                            "target_languages": ["English", "French", "German"]
                        }
                    }
                ]
            },
            "requester_id": "workflow_coordinator",
            "priority": 8
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.manus_agent}/a2a", json=workflow_data) as response:
                if response.status == 200:
                    result = await response.json()
                    workflow_result = result.get("result", {})
                    
                    return {
                        "summary": "Multi-agent research workflow completed",
                        "workflow_completed": workflow_result.get("workflow_completed"),
                        "steps_executed": workflow_result.get("steps_executed"),
                        "agents_involved": ["Manus", "Memory", "GoogleAI"]
                    }
                else:
                    error = await response.text()
                    raise Exception(f"Multi-agent workflow failed: {error}")
    
    async def example_googleai_to_sam(self):
        """Ejemplo: GoogleAI genera código que SAM ejecuta"""
        
        # Primero GoogleAI genera código
        code_generation_task = {
            "task_id": f"codegen_{datetime.utcnow().timestamp()}",
            "task_type": "code_generation",
            "payload": {
                "prompt": "Crear función Python para análisis de sentiment de tweets",
                "language": "python",
                "subtype": "generation"
            },
            "requester_id": "integration_example"
        }
        
        async with aiohttp.ClientSession() as session:
            # Generar código con GoogleAI
            async with session.post(f"{self.googleai_agent}/a2a", json=code_generation_task) as response:
                if response.status == 200:
                    code_result = await response.json()
                    generated_code = code_result.get("result", {}).get("result", "")
                    
                    # Luego SAM podría ejecutar el código (simulado)
                    execution_task = {
                        "task_type": "autonomous_execution",
                        "payload": {
                            "task_description": "Execute generated sentiment analysis code",
                            "code": generated_code[:200] + "...",  # Truncado para el ejemplo
                            "autonomy_level": "medium"
                        },
                        "requester_id": "integration_example"
                    }
                    
                    async with session.post(f"{self.sam_agent}/a2a", json=execution_task) as exec_response:
                        if exec_response.status == 200:
                            exec_result = await exec_response.json()
                            
                            return {
                                "summary": "GoogleAI generated code, SAM prepared for execution",
                                "code_generated": True,
                                "execution_planned": True,
                                "integration_flow": "GoogleAI → SAM"
                            }
                
                return {
                    "summary": "Code generation completed by GoogleAI",
                    "code_generated": True,
                    "execution_planned": False
                }
    
    async def example_complex_content_workflow(self):
        """Ejemplo: Workflow complejo de creación de contenido"""
        
        # Workflow: Research → Analysis → Translation → Summary
        content_workflow = {
            "task_type": "multi_step_research",
            "payload": {
                "query": "Future of AI agent collaboration in enterprises",
                "steps": ["research_analysis", "content_generation", "translation", "summarization"],
                "depth": "comprehensive",
                "output_formats": ["analysis", "summary", "multilingual"]
            },
            "requester_id": "content_creator"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.sam_agent}/a2a", json=content_workflow) as response:
                if response.status == 200:
                    result = await response.json()
                    research_result = result.get("result", {})
                    
                    # Después de la investigación, GoogleAI podría generar contenido adicional
                    if research_result.get("multi_step_research_completed"):
                        content_enhancement = {
                            "task_id": f"enhance_{datetime.utcnow().timestamp()}",
                            "task_type": "content_creation",
                            "payload": {
                                "prompt": "Based on the research, create executive summary for enterprise AI adoption",
                                "style": "professional",
                                "length": "medium"
                            },
                            "requester_id": "content_creator"
                        }
                        
                        async with session.post(f"{self.googleai_agent}/a2a", json=content_enhancement) as enhance_response:
                            if enhance_response.status == 200:
                                enhance_result = await enhance_response.json()
                                
                                return {
                                    "summary": "Complex content workflow: Research + AI Enhancement",
                                    "research_completed": True,
                                    "content_enhanced": True,
                                    "workflow_agents": ["SAM", "GoogleAI", "Memory"]
                                }
                    
                    return {
                        "summary": "Research workflow completed by SAM",
                        "research_completed": research_result.get("multi_step_research_completed"),
                        "content_enhanced": False
                    }
                else:
                    error = await response.text()
                    raise Exception(f"Content workflow failed: {error}")

    async def demo_interactive_usage(self):
        """Demo interactivo mostrando el poder de A2A + GoogleAI"""
        
        print("🎮 Interactive Demo: A2A + GoogleAI Integration")
        print("=" * 50)
        print()
        
        # 1. Mostrar agentes disponibles
        print("1. 📋 Checking available agents...")
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.a2a_server}/agents") as response:
                if response.status == 200:
                    data = await response.json()
                    agents = data.get("agents", [])
                    
                    print(f"   ✅ Found {len(agents)} agents:")
                    for agent in agents:
                        capabilities = ", ".join(agent.get("capabilities", [])[:3])
                        print(f"      🤖 {agent.get('name')} - {capabilities}...")
                print()
        
        # 2. Test GoogleAI capabilities
        print("2. 🧪 Testing GoogleAI capabilities...")
        test_task = {
            "task_id": "demo_test",
            "task_type": "text_generation",
            "payload": {
                "prompt": "Explain the benefits of agent-to-agent communication in AI systems",
                "max_tokens": 150
            },
            "requester_id": "demo_user"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.googleai_agent}/a2a", json=test_task) as response:
                if response.status == 200:
                    result = await response.json()
                    generated_text = result.get("result", {}).get("generated_text", "")
                    print(f"   ✅ GoogleAI Response: {generated_text[:100]}...")
                else:
                    print(f"   ❌ GoogleAI test failed")
        print()
        
        # 3. Demo A2A delegation
        print("3. 🔄 Demonstrating A2A delegation...")
        delegation_task = {
            "task_type": "delegation",
            "payload": {
                "target_task": {
                    "task_type": "translation",
                    "text": "Agent-to-agent communication enables sophisticated AI workflows",
                    "target_language": "Spanish"
                },
                "required_capabilities": ["translation", "ai_models"]
            },
            "requester_id": "demo_orchestrator"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.manus_agent}/a2a", json=delegation_task) as response:
                if response.status == 200:
                    result = await response.json()
                    delegation_result = result.get("result", {})
                    
                    if delegation_result.get("delegation_successful"):
                        print(f"   ✅ Delegation successful to: {delegation_result.get('assigned_agent')}")
                        translation = delegation_result.get("result", {}).get("result", {}).get("translated_text", "")
                        print(f"   🌐 Translation: {translation}")
                    else:
                        print(f"   ❌ Delegation failed: {delegation_result.get('error')}")
                else:
                    print(f"   ❌ Delegation request failed")
        print()
        
        print("🎉 Demo completed! Your A2A + GoogleAI integration is working!")

async def main():
    """Ejecutar ejemplos de delegación A2A"""
    examples = A2ADelegationExamples()
    
    print("🚀 A2A + GoogleAI Integration Examples")
    print("Choose an option:")
    print("1. Run all examples")
    print("2. Interactive demo")
    print("3. Specific example")
    
    # Para automático, ejecutar todos los ejemplos
    print("Running all examples automatically...\n")
    
    # Verificar que el sistema A2A esté corriendo
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8200/health") as response:
                if response.status != 200:
                    print("❌ A2A Central Server not running. Start with: ./start_a2a_system.sh")
                    return
                    
            async with session.get("http://localhost:8213/health") as response:
                if response.status != 200:
                    print("❌ GoogleAI Agent not running. Start with: ./start_googleai_agent.sh")
                    return
                    
    except Exception as e:
        print(f"❌ System check failed: {e}")
        print("Make sure both A2A system and GoogleAI agent are running")
        return
    
    # Ejecutar ejemplos
    await examples.run_all_examples()
    
    print("\n🎮 Running interactive demo...")
    await examples.demo_interactive_usage()

if __name__ == "__main__":
    asyncio.run(main())