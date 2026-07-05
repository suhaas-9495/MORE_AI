from typing import Dict, Callable, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class ToolDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    input_schema: Dict[str, Any]
    version: str = "1.0.0"
    registered_at: str = ""
    
class ToolRegistry:
    """central registry of all tools available to agents.
    like a store for all agent capabilities and the tools will register themselves and agents query for to see whats available
    mcp server exposed these same tools to external clients
    """
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self._handlers: Dict[str, Callable] = {}

    def register(self, name: str, description: str, input_schema: Dict, handler: Callable, version: str = "1.0.0"):
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
            version=version,
            registered_at=datetime.utcnow().isoformat(),
        )
        self._handlers[name] = handler

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def get_handler(self, name: str) -> Optional[Callable]:
        return self._handlers.get(name)

    def list_tools(self) -> list:
        return list(self._tools.values())

    def disable(self, name: str):
        if name in self._tools:
            self._tools[name].enabled = False

    async def execute(self, name: str, inputs: Dict) -> Any:
        handler = self._handlers.get(name)
        if not handler:
            raise ValueError(f"Tool not found: {name}")
        if not self._tools[name].enabled:
            raise ValueError(f"Tool is disabled: {name}")
        return await handler(**inputs)


# singleton — shared across the whole app
tool_registry = ToolRegistry()