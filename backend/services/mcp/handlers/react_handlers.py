"""
ReAct (Reasoning + Acting) Handlers
Handles multi-chain planning, reasoning steps, and plan execution for the MCP stack
"""

import logging
from typing import Dict, List, Any, Optional
import httpx
import json
import os
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

# Configuration
AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://agent-service:8000")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")

# In-memory plan storage (could use Redis for persistence)
active_plans: Dict[str, Dict] = {}


async def reason_step(question: str, context: str = "") -> Dict[str, Any]:
    """
    Perform a single reasoning step with the LLM.
    Useful for breaking down complex problems into smaller, manageable steps.

    Args:
        question: Current question or step to reason about
        context: Available context from previous steps or RAG

    Returns:
        Dictionary with reasoning step result and next action suggestion
    """
    try:
        logger.info(f"Performing reasoning step for: {question}")

        # Build reasoning prompt
        prompt = f"""You are a reasoning agent. Think step-by-step about the following question:

Context: {context if context else "No additional context provided"}

Question: {question}

Please:
1. Analyze the question
2. Break it down into smaller steps if needed
3. Identify what information is needed
4. Suggest the best approach

Format your response as JSON with these fields:
{{
  "analysis": "Your analysis of the question",
  "steps_needed": ["step1", "step2", ...],
  "information_needed": ["info1", "info2", ...],
  "approach": "Suggested approach",
  "confidence": 0.0-1.0
}}"""

        # Get LLM response
        response_text = await call_llm(prompt)

        # Try to parse as JSON
        try:
            reasoning = json.loads(response_text)
        except json.JSONDecodeError:
            # If not JSON, wrap in default structure
            reasoning = {
                "analysis": response_text,
                "steps_needed": [],
                "information_needed": [],
                "approach": "Direct approach",
                "confidence": 0.7,
                "raw_response": response_text,
            }

        return {
            "success": True,
            "question": question,
            "reasoning": reasoning,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Reasoning step error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "question": question}


async def create_plan(goal: str, context: str = "") -> Dict[str, Any]:
    """
    Create a multi-step plan for complex tasks.
    Analyzes the goal and breaks it into achievable, ordered steps.

    Args:
        goal: The goal to achieve
        context: Additional context about the task

    Returns:
        Dictionary with the generated plan and plan ID
    """
    try:
        logger.info(f"Creating plan for goal: {goal}")

        # Build planning prompt
        prompt = f"""You are a planning agent. Create a detailed plan to achieve this goal:

Goal: {goal}
Context: {context if context else "No additional context"}

Create a step-by-step plan that:
1. Breaks down the goal into achievable steps
2. Identifies dependencies between steps
3. Specifies tools or resources needed for each step
4. Estimates complexity/time

Format as JSON:
{{
  "plan_summary": "Brief summary of the overall approach",
  "steps": [
    {{
      "step_number": 1,
      "description": "What this step does",
      "dependencies": [],
      "tools_needed": ["tool1", "tool2"],
      "complexity": "low|medium|high",
      "estimated_time": "time estimate"
    }}
  ],
  "total_estimated_time": "overall estimate",
  "critical_path": [1, 3, 5]
}}"""

        # Get LLM response
        response_text = await call_llm(prompt)

        # Parse plan
        try:
            plan_data = json.loads(response_text)
        except json.JSONDecodeError:
            plan_data = {
                "plan_summary": response_text,
                "steps": [{"step_number": 1, "description": response_text}],
                "total_estimated_time": "Unknown",
                "critical_path": [1],
                "raw_response": response_text,
            }

        # Generate plan ID
        plan_id = str(uuid.uuid4())

        # Store plan
        active_plans[plan_id] = {
            "plan_id": plan_id,
            "goal": goal,
            "context": context,
            "plan_data": plan_data,
            "status": "created",
            "created_at": datetime.utcnow().isoformat(),
            "current_step": 0,
            "completed_steps": [],
        }

        logger.info(f"Plan created with ID: {plan_id}")

        return {
            "success": True,
            "plan_id": plan_id,
            "goal": goal,
            "plan": plan_data,
            "status": "created",
        }

    except Exception as e:
        logger.error(f"Plan creation error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "goal": goal}


async def execute_plan_step(
    plan_id: str,
    step_description: Optional[str] = None,
    step_number: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Execute a specific step in a multi-step plan.
    Handles dependencies between steps and tracks progress.

    Args:
        plan_id: ID of the plan to execute
        step_description: Optional manual step description
        step_number: Optional specific step number to execute

    Returns:
        Dictionary with execution result and updated plan status
    """
    try:
        logger.info(f"Executing step for plan {plan_id}")

        # Retrieve plan
        if plan_id not in active_plans:
            return {"success": False, "error": f"Plan not found: {plan_id}"}

        plan = active_plans[plan_id]

        # Determine which step to execute
        if step_number is not None:
            step_index = step_number - 1
        elif step_description is not None:
            # Find step by description
            step_index = None
            for i, step in enumerate(plan["plan_data"]["steps"]):
                if step["description"] == step_description:
                    step_index = i
                    break
            if step_index is None:
                step_index = plan["current_step"]
        else:
            step_index = plan["current_step"]

        # Check if step exists
        if step_index >= len(plan["plan_data"]["steps"]):
            return {
                "success": False,
                "error": "No more steps to execute",
                "plan_status": plan["status"],
            }

        step = plan["plan_data"]["steps"][step_index]

        # Check dependencies
        if step["dependencies"]:
            missing_deps = [
                dep
                for dep in step["dependencies"]
                if dep not in plan["completed_steps"]
            ]
            if missing_deps:
                return {
                    "success": False,
                    "error": f"Missing dependencies: {missing_deps}",
                    "step": step,
                }

        logger.info(f"Executing step {step_index + 1}: {step['description']}")

        # Execute the step (this would integrate with actual tools)
        execution_result = {
            "step_executed": True,
            "description": step["description"],
            "tools_used": step.get("tools_needed", []),
            "complexity": step.get("complexity", "unknown"),
        }

        # Update plan
        plan["completed_steps"].append(step_index + 1)
        plan["current_step"] = step_index + 1

        # Check if plan is complete
        if plan["current_step"] >= len(plan["plan_data"]["steps"]):
            plan["status"] = "completed"
            plan["completed_at"] = datetime.utcnow().isoformat()
        else:
            plan["status"] = "in_progress"

        active_plans[plan_id] = plan

        return {
            "success": True,
            "plan_id": plan_id,
            "step_number": step_index + 1,
            "step": step,
            "result": execution_result,
            "plan_status": plan["status"],
            "steps_completed": len(plan["completed_steps"]),
            "total_steps": len(plan["plan_data"]["steps"]),
        }

    except Exception as e:
        logger.error(f"Plan execution error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "plan_id": plan_id}


async def call_llm(prompt: str, model: Optional[str] = None) -> str:
    """
    Internal helper to call the LLM service.

    Args:
        prompt: The prompt to send to the LLM
        model: Optional model override

    Returns:
        LLM response text
    """
    try:
        if LLM_PROVIDER == "ollama":
            model = model or "llama3:8b"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.7},
                    },
                    timeout=120.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "")
                else:
                    logger.error(f"LLM error: {response.status_code}")
                    return f"Error: LLM returned status {response.status_code}"
        else:
            return f"LLM provider {LLM_PROVIDER} not implemented in reasoning handler"

    except Exception as e:
        logger.error(f"LLM call error: {e}", exc_info=True)
        return f"Error calling LLM: {str(e)}"
