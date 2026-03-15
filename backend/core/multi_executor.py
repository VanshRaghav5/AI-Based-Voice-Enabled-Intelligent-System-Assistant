from backend.config.logger import logger


class MultiExecutor:

    # Tools that require confirmation before execution
    CRITICAL_TOOLS = {
        "whatsapp.send",
        "email.send",
        "file.delete",
        "folder.delete",
        "system.shutdown",
        "system.restart",
        "file.move",
    }

    def __init__(self, registry):
        self.registry = registry
        self.pending_confirmation = None
        self.confirmation_approved = False

    def _extract_step_data(self, step):
        """Extract normalized tool name and arguments from a step."""
        if isinstance(step, dict):
            tool_name = step.get("name") or step.get("tool")
            tool_args = step.get("args") or step.get("params") or step.get("parameters") or {}
            return tool_name, tool_args

        tool_name = getattr(step, "name", None) or getattr(step, "tool", None)
        tool_args = (
            getattr(step, "args", None)
            or getattr(step, "params", None)
            or getattr(step, "parameters", None)
            or {}
        )
        return tool_name, tool_args

    def execute(self, plan):
        """Execute a plan (either object with .steps or dict with 'steps' key).
        
        Args:
            plan: Plan object or dictionary.
            
        Returns:
            List of execution results.
        """
        results = []

        # Handle both object and dictionary formats
        if plan is None:
            logger.warning("[MultiExecutor] Received None plan")
            return results
        
        # Extract steps based on plan type
        if isinstance(plan, dict):
            steps = plan.get("steps", [])
            if not steps:
                logger.warning("[MultiExecutor] Plan has no steps")
                return results
        else:
            # Assume it's an object with .steps attribute
            if not hasattr(plan, 'steps'):
                logger.error(f"[MultiExecutor] Invalid plan format: {type(plan)}")
                return results
            steps = plan.steps

        for step_index, step in enumerate(steps):
            logger.info(f"[MultiExecutor] Executing step #{step_index + 1}: {step}")

            # Extract tool name and arguments from either {name,args} or {tool,params}
            tool_name, tool_args = self._extract_step_data(step)
            
            if not tool_name:
                logger.warning("[MultiExecutor] Step has no name")
                continue

            # Check if this is a critical tool requiring confirmation
            if tool_name in self.CRITICAL_TOOLS:
                logger.warning(f"[MultiExecutor] CRITICAL TOOL: {tool_name} requires confirmation")
                
                # Build confirmation message
                if tool_name == "whatsapp.send":
                    target = tool_args.get("target", "unknown")
                    message = tool_args.get("message", "")
                    confirm_msg = f"Send WhatsApp message to {target}: '{message}'"
                elif tool_name in ["file.delete", "folder.delete"]:
                    path = tool_args.get("path", "unknown")
                    confirm_msg = f"Delete: {path} (THIS CANNOT BE UNDONE)"
                elif tool_name == "email.send":
                    recipient = tool_args.get("recipient") or tool_args.get("target") or "unknown"
                    subject = tool_args.get("subject", "")
                    confirm_msg = f"Send email to {recipient}: subject='{subject}'"
                elif tool_name == "file.move":
                    source = tool_args.get("source", "unknown")
                    dest = tool_args.get("destination", "unknown")
                    confirm_msg = f"Move {source} to {dest}"
                elif tool_name in ["system.shutdown", "system.restart"]:
                    action = "Shutdown" if "shutdown" in tool_name else "Restart"
                    confirm_msg = f"{action} system (ALL WORK WILL BE LOST)"
                else:
                    confirm_msg = f"Execute critical operation: {tool_name}"
                
                # Request confirmation
                results.append({
                    "status": "confirmation_required",
                    "message": confirm_msg,
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "step_index": step_index,
                    "data": {}
                })
                logger.info(f"[MultiExecutor] Confirmation required: {confirm_msg}")
                break  # Stop and wait for confirmation
            
            tool = self.registry.get(tool_name)

            if not tool:
                results.append({
                    "status": "error",
                    "message": f"Tool {tool_name} not found",
                    "data": {}
                })
                continue

            try:
                result = tool.execute(**tool_args)
                results.append(result)
                
                # Stop execution on failure
                if result.get("status") != "success":
                    logger.warning("[MultiExecutor] Stopping due to failure.")
                    break
                    
            except Exception as e:
                logger.error(f"[MultiExecutor] Error executing {tool_name}: {e}")
                results.append({
                    "status": "error",
                    "message": str(e),
                    "data": {}
                })
                break

        return results

    def approve_confirmation(self, plan, step_index=0):
        """Approve and execute a pending critical operation.
        
        Args:
            plan: The plan containing the critical step
            step_index: Index of the step to execute
            
        Returns:
            List of execution results.
        """
        logger.info("[MultiExecutor] Executing confirmed step...")
        results = []
        
        # Extract steps
        if isinstance(plan, dict):
            steps = plan.get("steps", [])
        else:
            steps = plan.steps if hasattr(plan, 'steps') else []
        
        if step_index >= len(steps):
            return [{"status": "error", "message": "Invalid step index for confirmation", "data": {}}]

        # Execute confirmed step, then continue remaining steps until completion,
        # another confirmation gate, or a failure.
        for idx in range(step_index, len(steps)):
            step = steps[idx]
            tool_name, tool_args = self._extract_step_data(step)

            if not tool_name:
                results.append({
                    "status": "error",
                    "message": "Step has no tool name",
                    "data": {}
                })
                break

            # If a later step is critical, request a new confirmation.
            if idx > step_index and tool_name in self.CRITICAL_TOOLS:
                results.append({
                    "status": "confirmation_required",
                    "message": f"Confirm critical operation: {tool_name}",
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "step_index": idx,
                    "data": {}
                })
                logger.info(f"[MultiExecutor] Additional confirmation required at step #{idx + 1}")
                break

            tool = self.registry.get(tool_name)
            if not tool:
                results.append({
                    "status": "error",
                    "message": f"Tool {tool_name} not found",
                    "data": {}
                })
                break

            try:
                result = tool.execute(**tool_args)
                results.append(result)
                logger.info(f"[MultiExecutor] Executed step #{idx + 1}: {result}")

                if result.get("status") != "success":
                    logger.warning("[MultiExecutor] Stopping continuation due to failure")
                    break
            except Exception as e:
                logger.error(f"[MultiExecutor] Error executing {tool_name}: {e}")
                results.append({
                    "status": "error",
                    "message": str(e),
                    "data": {}
                })
                break
        
        return results

    def deny_confirmation(self):
        """Deny the pending critical operation.
        
        Returns:
            Cancellation result.
        """
        logger.info("[MultiExecutor] Critical operation cancelled by user")
        return {
            "status": "cancelled",
            "message": "Operation cancelled by user",
            "data": {}
        }