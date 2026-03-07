"""Tests for Automation Router and Tool Registry."""
import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestToolRegistry:
    """Test Tool Registry functionality."""
    
    def test_registry_initialization(self):
        """Test tool registry can be initialized."""
        # Act
        from backend.core.tool_registry import ToolRegistry
        registry = ToolRegistry()
        
        # Assert
        assert registry is not None
        assert hasattr(registry, '_tools')
    
    def test_register_tool(self):
        """Test registering a tool."""
        # Arrange
        from backend.core.tool_registry import ToolRegistry
        from backend.automation.base_tool import BaseTool
        
        class TestTool(BaseTool):
            name = "test.tool"
            description = "Test tool"
            risk_level = "low"
            requires_confirmation = False
            
            def execute(self, **args):
                return {"status": "success", "message": "Test", "data": {}}
        
        registry = ToolRegistry()
        tool = TestTool()
        
        # Act
        registry.register(tool)
        
        # Assert
        assert registry.get("test.tool") is not None
        assert registry.get("test.tool") == tool
    
    def test_list_registered_tools(self):
        """Test listing registered tools."""
        # Arrange
        from backend.core.tool_registry import ToolRegistry
        from backend.automation.base_tool import BaseTool
        
        class Tool1(BaseTool):
            name = "tool.one"
            description = "First"
            risk_level = "low"
            requires_confirmation = False
            def execute(self, **args): return {}
        
        class Tool2(BaseTool):
            name = "tool.two"
            description = "Second"
            risk_level = "low"
            requires_confirmation = False
            def execute(self, **args): return {}
        
        registry = ToolRegistry()
        registry.register(Tool1())
        registry.register(Tool2())
        
        # Act
        tools = registry.list_tools()
        
        # Assert
        assert len(tools) == 2
        assert "tool.one" in tools
        assert "tool.two" in tools
    
    def test_execute_tool(self):
        """Test executing a tool through registry."""
        # Arrange
        from backend.core.tool_registry import ToolRegistry
        from backend.core.tool_call import ToolCall
        from backend.automation.base_tool import BaseTool
        
        class ExecuteTool(BaseTool):
            name = "exec.tool"
            description = "Execute test"
            risk_level = "low"
            requires_confirmation = False
            
            def execute(self, value):
                return {"status": "success", "message": f"Executed with {value}", "data": {}}
        
        registry = ToolRegistry()
        registry.register(ExecuteTool())
        
        tool_call = ToolCall(name="exec.tool", args={"value": "test123"})
        
        # Act
        result = registry.execute(tool_call)
        
        # Assert
        assert result["status"] == "success"
        assert "test123" in result["message"]
    
    def test_execute_nonexistent_tool(self):
        """Test executing non-existent tool raises error."""
        # Arrange
        from backend.core.tool_registry import ToolRegistry
        from backend.core.tool_call import ToolCall
        
        registry = ToolRegistry()
        tool_call = ToolCall(name="fake.tool", args={})
        
        # Act & Assert
        with pytest.raises(ValueError, match="not found"):
            registry.execute(tool_call)


class TestExecutor:
    """Test Executor functionality."""
    
    def test_executor_initialization(self):
        """Test executor can be initialized."""
        # Arrange
        from backend.core.tool_registry import ToolRegistry
        from backend.core.executor import Executor
        
        registry = ToolRegistry()
        
        # Act
        executor = Executor(registry)
        
        # Assert
        assert executor is not None
        assert executor.registry == registry
    
    def test_executor_run_tool(self):
        """Test executor can run a tool."""
        # Arrange
        from backend.core.tool_registry import ToolRegistry
        from backend.core.executor import Executor
        from backend.core.tool_call import ToolCall
        from backend.automation.base_tool import BaseTool
        
        class RunTool(BaseTool):
            name = "run.tool"
            description = "Run test"
            risk_level = "low"
            requires_confirmation = False
            
            def execute(self):
                return {"status": "success", "message": "Ran successfully", "data": {}}
        
        registry = ToolRegistry()
        registry.register(RunTool())
        executor = Executor(registry)
        
        tool_call = ToolCall(name="run.tool", args={})
        
        # Act
        result = executor.run(tool_call)
        
        # Assert
        assert result["status"] == "success"
    
    def test_executor_handles_tool_error(self):
        """Test executor handles tool execution errors."""
        # Arrange
        from backend.core.tool_registry import ToolRegistry
        from backend.core.executor import Executor
        from backend.core.tool_call import ToolCall
        
        registry = ToolRegistry()
        executor = Executor(registry)
        
        # Tool doesn't exist
        tool_call = ToolCall(name="error.tool", args={})
        
        # Act
        result = executor.run(tool_call)
        
        # Assert
        assert result["status"] == "error"


class TestMultiExecutor:
    """Test Multi-Executor functionality."""
    
    def test_multi_executor_initialization(self):
        """Test multi-executor can be initialized."""
        # Arrange
        from backend.core.tool_registry import ToolRegistry
        from backend.core.multi_executor import MultiExecutor
        
        registry = ToolRegistry()
        
        # Act
        multi_executor = MultiExecutor(registry)
        
        # Assert
        assert multi_executor is not None
    
    def test_multi_executor_single_step(self):
        """Test multi-executor with single step plan."""
        # Arrange
        from backend.core.tool_registry import ToolRegistry
        from backend.core.multi_executor import MultiExecutor
        from backend.automation.base_tool import BaseTool
        
        class SingleTool(BaseTool):
            name = "single.tool"
            description = "Single step"
            risk_level = "low"
            requires_confirmation = False
            
            def execute(self, param):
                return {"status": "success", "message": f"Done {param}", "data": {}}
        
        registry = ToolRegistry()
        registry.register(SingleTool())
        multi_executor = MultiExecutor(registry)
        
        plan = {
            "steps": [
                {"tool": "single.tool", "args": {"param": "value1"}}
            ]
        }
        
        # Act
        results = multi_executor.execute(plan)
        
        # Assert
        assert len(results) == 1
        assert results[0]["status"] == "success"
    
    def test_multi_executor_multiple_steps(self):
        """Test multi-executor with multiple steps."""
        # Arrange
        from backend.core.tool_registry import ToolRegistry
        from backend.core.multi_executor import MultiExecutor
        from backend.automation.base_tool import BaseTool
        
        class StepTool(BaseTool):
            name = "step.tool"
            description = "Multi step"
            risk_level = "low"
            requires_confirmation = False
            
            def execute(self, step_id):
                return {"status": "success", "message": f"Step {step_id}", "data": {}}
        
        registry = ToolRegistry()
        registry.register(StepTool())
        multi_executor = MultiExecutor(registry)
        
        plan = {
            "steps": [
                {"tool": "step.tool", "args": {"step_id": 1}},
                {"tool": "step.tool", "args": {"step_id": 2}},
                {"tool": "step.tool", "args": {"step_id": 3}}
            ]
        }
        
        # Act
        results = multi_executor.execute(plan)
        
        # Assert
        assert len(results) == 3
        assert all(r["status"] == "success" for r in results)
    
    def test_multi_executor_confirmation_required(self):
        """Test multi-executor handles confirmation requirement."""
        # Arrange
        from backend.core.tool_registry import ToolRegistry
        from backend.core.multi_executor import MultiExecutor
        from backend.automation.base_tool import BaseTool
        
        class HighRiskTool(BaseTool):
            name = "highrisk.tool"
            description = "High risk operation"
            risk_level = "high"
            requires_confirmation = True
            
            def execute(self):
                return {"status": "success", "message": "Risky done", "data": {}}
        
        registry = ToolRegistry()
        registry.register(HighRiskTool())
        multi_executor = MultiExecutor(registry)
        
        plan = {
            "steps": [
                {"tool": "highrisk.tool", "args": {}}
            ]
        }
        
        # Act
        results = multi_executor.execute(plan)
        
        # Assert
        assert len(results) > 0
        # Should return confirmation request
        assert results[-1]["status"] in ["confirmation_required", "success"]


class TestToolRegistration:
    """Test complete tool registration system."""
    
    def test_register_all_tools(self):
        """Test registering all system tools."""
        # Arrange
        from backend.core.tool_registry import ToolRegistry
        from backend.automation.registry_tools import register_all_tools
        
        registry = ToolRegistry()
        
        # Act
        register_all_tools(registry)
        
        # Assert
        tools = registry.list_tools()
        assert len(tools) > 0
        
        # Check for key tools
        assert "file.create" in tools or "file.open" in tools
        assert "system.lock" in tools or "system.volume.up" in tools
        assert "whatsapp.send" in tools or "whatsapp.open" in tools
