"""
Agent Communication Service
===========================

Dedicated service for cross-agent communication and coordination,
extracted from additional_services.py for better separation of concerns.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import other services for cross-agent calls
from .transaction_service import TransactionQueryService
from .jar_service import JarManagementService

class AgentCommunicationService:
    """
    Service for managing communication between different agents in the system.
    """
    
    @staticmethod
    async def call_transaction_fetcher(db: AsyncIOMotorDatabase, user_id: str, 
                                     user_query: str, description: str = "") -> Dict[str, Any]:
        """
        Simulate calling the transaction fetcher agent.
        
        Args:
            db: Database connection
            user_id: User identifier
            user_query: Query to process
            description: Additional context
            
        Returns:
            Formatted response from transaction fetcher
        """
        try:
            # Use TransactionQueryService to handle the request
            query_service = TransactionQueryService()
            
            # Parse query for transaction fetching intent
            if "recent" in user_query.lower():
                result = await query_service.get_jar_transactions(db, user_id, limit=10)
            elif "spending" in user_query.lower():
                result = await query_service.get_time_period_transactions(
                    db, user_id, start_date="last_month"
                )
            else:
                result = await query_service.get_jar_transactions(db, user_id, limit=20)
            
            return {
                "agent": "transaction_fetcher",
                "status": "success", 
                "data": result,
                "query": user_query,
                "description": description,
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
                           jar_name: str = None, description: str = "") -> Dict[str, Any]:
        """
        Simulate calling the jar management agent.
        
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
                # Get specific jar information
                jar = await db.jars.find_one({"user_id": user_id, "name": jar_name})
                if jar:
                    result = f"📊 Jar '{jar_name}': {jar.get('percent', 0)*100:.1f}% allocation, ${jar.get('current_amount', 0):.2f} current"
                else:
                    result = f"❌ Jar '{jar_name}' not found"
            else:
                # List all jars
                result = await jar_service.list_jars(db, user_id)
            
            return {
                "agent": "jar_manager",
                "status": "success",
                "data": result,
                "jar_name": jar_name,
                "description": description,
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
        
        # Extract key data based on response structure
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
        communication_service = AgentCommunicationService()
        
        try:
            # Call each required agent
            for agent in required_agents:
                if agent == "transaction_fetcher":
                    result = await communication_service.call_transaction_fetcher(
                        db, user_id, task_description
                    )
                elif agent == "jar_manager":
                    result = await communication_service.call_jar_agent(
                        db, user_id, description=task_description
                    )
                else:
                    result = {"status": "error", "error": f"Unknown agent: {agent}"}
                
                results[agent] = result
            
            # Analyze overall success
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
