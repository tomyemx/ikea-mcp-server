# IKEA MCP Server - AI Agent Instructions

## Architecture Overview
This is a Model Context Protocol (MCP) server built with FastMCP, providing AI agents with IKEA-related tools. The server integrates Google Generative AI for enhanced functionality.

**Key Components:**
- `server.py`: Main server file containing MCP tool definitions and Google AI integration
- Uses FastMCP framework for MCP protocol implementation
- Google Generative AI configured for potential future AI-powered features

## Development Workflow
- **Run Server**: Execute `python server.py` to start the MCP server
- **MCP Integration**: Server must be connected to MCP-compatible clients (e.g., Claude Desktop, VS Code extensions)
- **Testing**: Tools currently return dummy data - modify return values in tool functions for real implementation

## Code Patterns & Conventions
- **Tool Definition**: Use `@mcp.tool()` decorator for new IKEA-related functions
- **Dummy Data**: Follow pattern of returning test strings during development (e.g., `"Test Result: Sofa KIVIK, 500 NIS"`)
- **Comments**: Mix of English code and Hebrew explanatory comments
- **API Keys**: Currently hardcoded (replace with environment variables for production)

## Dependencies & Integration
- **FastMCP**: Core MCP server framework
- **google-generativeai**: Configured but not yet utilized in tools
- **Environment Setup**: Requires Google AI API key (currently hardcoded as `MY_API_KEY`)

## Common Tasks
- **Add New Tool**: Define function with `@mcp.tool()` decorator in `server.py`
- **Test Tools**: Call functions directly or via MCP client to verify dummy responses
- **AI Integration**: Use `genai` object for Google AI features in future tools

## Security Notes
- Move hardcoded API keys to environment variables before deployment
- Validate inputs in tool functions for production use