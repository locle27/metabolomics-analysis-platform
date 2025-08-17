
import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add the archon python src directory to the path to allow imports
import sys
sys.path.append(str(Path(__file__).resolve().parent / "archon/python/src"))

try:
    from agents.mcp_client import MCPClient
except ImportError:
    print("Error: Could not import MCPClient.")
    print("Please ensure that the archon submodule is present and the script is run from the project root.")
    sys.exit(1)

async def manage_projects(client: MCPClient, action: str, **kwargs):
    """Helper function to manage projects."""
    try:
        result = await client.manage_project(action=action, **kwargs)
        return json.loads(result)
    except Exception as e:
        return {"error": str(e)}

async def manage_tasks(client: MCPClient, action: str, **kwargs):
    """Helper function to manage tasks."""
    try:
        # Filter out None values from kwargs
        params = {k: v for k, v in kwargs.items() if v is not None}
        result = await client.manage_task(action=action, **params)
        return json.loads(result)
    except Exception as e:
        return {"error": str(e)}

async def perform_rag_query(client: MCPClient, query: str, **kwargs):
    """Helper function for RAG queries."""
    try:
        result = await client.perform_rag_query(query=query, **kwargs)
        return json.loads(result)
    except Exception as e:
        return {"error": str(e)}

async def main():
    """Main function to parse arguments and call the appropriate MCP tool."""
    parser = argparse.ArgumentParser(description="A command-line interface for the Archon MCP server.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- Projects ---
    project_parser = subparsers.add_parser("projects", help="Manage projects")
    project_subparsers = project_parser.add_subparsers(dest="action", required=True)
    project_list_parser = project_subparsers.add_parser("list", help="List all projects")

    # --- Tasks ---
    task_parser = subparsers.add_parser("tasks", help="Manage tasks")
    task_subparsers = task_parser.add_subparsers(dest="action", required=True)
    
    task_list_parser = task_subparsers.add_parser("list", help="List tasks for a project")
    task_list_parser.add_argument("--project_id", required=True, help="ID of the project")

    task_update_parser = task_subparsers.add_parser("update", help="Update a task")
    task_update_parser.add_argument("--project_id", required=True, help="ID of the project")
    task_update_parser.add_argument("--task_id", required=True, help="ID of the task")
    task_update_parser.add_argument("--status", help="New status for the task")
    task_update_parser.add_argument("--description", help="New description for the task")
    task_update_parser.add_argument("--assignee", help="New assignee for the task")

    # --- RAG ---
    rag_parser = subparsers.add_parser("rag", help="Perform RAG queries")
    rag_parser.add_argument("query", help="The search query")
    rag_parser.add_argument("--source", help="Optional source ID to filter by")
    rag_parser.add_argument("--match_count", type=int, default=5, help="Number of results to return")

    args = parser.parse_args()

    result = {}
    async with MCPClient(mcp_url="http://localhost:8051") as client:
        if args.command == "projects":
            if args.action == "list":
                result = await manage_projects(client, "get_projects")
        
        elif args.command == "tasks":
            if args.action == "list":
                result = await manage_tasks(client, "get_tasks", project_id=args.project_id)
            elif args.action == "update":
                update_args = {
                    "project_id": args.project_id,
                    "task_id": args.task_id,
                    "status": args.status,
                    "description": args.description,
                    "assignee": args.assignee,
                }
                result = await manage_tasks(client, "update_task", **update_args)

        elif args.command == "rag":
            rag_args = {
                "query": args.query,
                "source": args.source,
                "match_count": args.match_count
            }
            result = await perform_rag_query(client, **rag_args)

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    # This check is to prevent a RuntimeError with asyncio on Windows.
    if sys.platform == "win32" and sys.version_info >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())
