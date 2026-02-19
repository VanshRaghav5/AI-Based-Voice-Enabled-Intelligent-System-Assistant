from backend.llm.llm_client import LLMClient
from backend.core.tool_registry import ToolRegistry
from backend.core.executor import Executor
from backend.core.multi_executor import MultiExecutor
from backend.memory.session_state import SessionState
from backend.automation.registry_tools import register_all_tools
from backend.config.logger import logger
import keyboard


class AssistantController:

    def __init__(self):
        """Initialize the assistant controller with core components."""
        # Initialize LLM client with qwen model
        self.llm_client = LLMClient(model="qwen2.5")
        
        # Initialize registry and tool executor
        self.registry = ToolRegistry()
        self.executor = Executor(self.registry)
        register_all_tools(self.registry)
        
        # Initialize multi-executor
        self.multi_executor = MultiExecutor(self.registry)
        
        # Initialize session state
        self.memory = SessionState()
        
        # Track pending plan and step for confirmation
        self.pending_plan = None
        self.pending_step_index = 0
        
        logger.info("[AssistantController] Initialized successfully")

    def process(self, text: str):
        """Process user input and execute actions.
        
        Args:
            text: User input text.
            
        Returns:
            Result dictionary with status and data.
        """
        try:
            logger.info(f"[AssistantController] Processing: {text}")
            
            # Generate plan from LLM
            plan_data = self.llm_client.generate_plan(text)
            
            if not plan_data:
                return {
                    "status": "error",
                    "message": "I did not understand that command.",
                    "data": {}
                }
            
            # Execute plan using multi-executor
            results = self.multi_executor.execute(plan_data)
            
            # Check if confirmation is required
            if results and results[-1].get("status") == "confirmation_required":
                # Store plan for later confirmation
                self.pending_plan = plan_data
                confirm_msg = results[-1].get("message", "Confirm action?")
                logger.info(f"[AssistantController] Waiting for confirmation: {confirm_msg}")
                
                # Return confirmation request
                return {
                    "status": "confirmation_required",
                    "message": confirm_msg,
                    "data": {}
                }
            
            # Store in memory
            for result in results:
                self.memory.add_history(result)
            
            logger.info(f"[AssistantController] Result: {results}")
            return results[-1] if results else {
                "status": "error",
                "message": "Execution failed.",
                "data": {}
            }
            
        except Exception as e:
            logger.error(f"[AssistantController Error] {e}")
            return {
                "status": "error",
                "message": str(e),
                "data": {}
            }

    def confirm_action(self, approved: bool):
        """Handle user confirmation of critical actions.
        
        Args:
            approved: True to approve, False to deny.
            
        Returns:
            Result of the action.
        """
        if not self.pending_plan:
            return {
                "status": "error",
                "message": "No pending action to confirm",
                "data": {}
            }
        
        if approved:
            logger.info("[AssistantController] User approved critical action")
            results = self.multi_executor.approve_confirmation(self.pending_plan, self.pending_step_index)
        else:
            logger.info("[AssistantController] User denied critical action")
            results = [self.multi_executor.deny_confirmation()]
        
        # Clear pending plan
        self.pending_plan = None
        
        # Store in memory
        for result in results:
            self.memory.add_history(result)
        
        return results[-1] if results else {"status": "cancelled", "message": "Action cancelled"}