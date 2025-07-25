"""
Agent Communication Service - Complete Implementation from Lab
=============================================================

This module implements the cross-agent communication service from the lab,
including all functions: call_transaction_fetcher, call_jar_agent,
format_cross_agent_request, handle_cross_agent_response, coordinate_multi_agent_task.
Integrated with database for user context.
All methods async where appropriate.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.utils import general_utils, user_setting_utils
from .transaction_service import TransactionQueryService
from .jar_service import JarManagementService

class AgentCommunicationService:
    """
    Service for managing communication between different agents.
    """
    
    @staticmethod
    async def call_transaction_fetcher(db: AsyncIOMotorDatabase, user_id: str, 
                                       user_query: str, description: str = "") -> Dict[str, Any]:
        """
        Call transaction fetcher service.
        
        Args:
            db: Database connection
            user_id: User identifier
            user_query: Query to process
            description: Additional context
            
        Returns:
            Formatted response from transaction fetcher
        """
        try:
            query_service = TransactionQueryService()
            # Assuming get_complex_transaction can handle the query
            result = await query_service.get_complex_transaction(
                db=db,
                user_id=user_id,
                description=user_query  # Pass query as description or parse accordingly
            )
            
            return {
                "agent": "transaction_fetcher",
                "status": "success",
                "data": result["data"],
                "query": user_query,
                "description": description or result["description"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "agent": "transaction_fetcher",
                "status": "error",
                "error": str(e),
                "query": user_query,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @staticmethod
    async def call_jar_agent(db: AsyncIOMotorDatabase, user_id: str,
                             jar_name: Optional[str] = None, description: str = "") -> Dict[str, Any]:
        """
        Call jar management service.
        
        Args:
            db: Database connection
            user_id: User identifier  
            jar_name: Specific jar to query (optional)
            description: Additional context
            
        Returns:
            Formatted response from jar agent
        """
        try:
            jar_service = JarManagementService()
            
            if jar_name:
                jar = await general_utils.get_jar_by_name(db, user_id, jar_name.lower().replace(' ', '_'))
                if not jar:
                    return {
                        "agent": "jar_manager",
                        "status": "error",
                        "error": f"Jar '{jar_name}' not found",
                        "jar_name": jar_name,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                result = jar.dict()
                desc = f"Information for jar '{jar_name}'"
            else:
                jars = await jar_service.list_jars(db, user_id)
                result = [j.dict() for j in jars]  # Assuming list_jars returns list of JarInDB
                desc = "All jars information"
            
            return {
                "agent": "jar_manager",
                "status": "success",
                "data": result,
                "jar_name": jar_name,
                "description": description or desc,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "agent": "jar_manager",
                "status": "error",
                "error": str(e),
                "jar_name": jar_name,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def format_cross_agent_request(target_agent: str, request: Dict) -> Dict:
        """
        Format a request for cross-agent communication.
        
        Args:
            target_agent: Name of the target agent
            request: Request data
            
        Returns:
            Formatted request dictionary
        """
        return {
            "target_agent": target_agent,
            "request_id": f"req_{datetime.utcnow().timestamp()}",
            "timestamp": datetime.utcnow().isoformat(),
            "source_agent": request.get("source_agent", "unknown"),
            "data": request,
            "priority": request.get("priority", "normal")
        }
    
    @staticmethod
    def handle_cross_agent_response(response: Dict) -> Dict:
        """
        Handle and format response from cross-agent communication.
        
        Args:
            response: Response from target agent
            
        Returns:
            Processed response dictionary
        """
        processed = {
            "response_id": f"resp_{datetime.utcnow().timestamp()}",
            "processed_at": datetime.utcnow().isoformat(),
            "original_response": response,
            "status": response.get("status", "unknown"),
            "success": response.get("status") == "success"
        }
        
        if "data" in response:
            processed["extracted_data"] = response["data"]
        
        if "error" in response:
            processed["error_details"] = response["error"]
            processed["success"] = False
        
        return processed
    
    @staticmethod
    async def coordinate_multi_agent_task(db: AsyncIOMotorDatabase, user_id: str,
                                          task_description: str, required_agents: List[str]) -> Dict[str, Any]:
        """
        Coordinate a task that requires multiple agents.
        
        Args:
            db: Database connection
            user_id: User identifier
            task_description: Description of the task
            required_agents: List of agents needed for the task
            
        Returns:
            Coordination result
        """
        results = {}
        
        try:
            for agent in required_agents:
                if agent == "transaction_fetcher":
                    result = await AgentCommunicationService.call_transaction_fetcher(
                        db, user_id, task_description
                    )
                elif agent == "jar_manager":
                    result = await AgentCommunicationService.call_jar_agent(
                        db, user_id, description=task_description
                    )
                else:
                    result = {"status": "error", "error": f"Unknown agent: {agent}"}
                
                results[agent] = result
            
            success_count = sum(1 for r in results.values() if r.get("status") == "success")
            overall_success = success_count == len(required_agents)
            
            return {
                "task": task_description,
                "required_agents": required_agents,
                "results": results,
                "overall_success": overall_success,
                "success_rate": f"{success_count}/{len(required_agents)}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "task": task_description,
                "required_agents": required_agents,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    @staticmethod
    async def get_user_total_income(db: AsyncIOMotorDatabase, user_id: str) -> Dict[str, Any]:
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")

        user_income = await user_setting_utils.get_user_total_income(db, user_id)
        if user_income is None:
            raise ValueError(f"No income data found for user {user_id}")
        return user_income