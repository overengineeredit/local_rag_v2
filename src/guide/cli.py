"""
Command-line interface for Local RAG system.
Provides user-friendly commands that communicate with the FastAPI backend.
"""
from __future__ import annotations

import sys
import argparse
import httpx
import json
from typing import Dict, Any
from rich.console import Console
from rich.table import Table
from rich import print as rprint

console = Console()

DEFAULT_BASE_URL = "http://localhost:8080"


class LocalRAGCLI:
    """Command-line interface for Local RAG operations."""
    
    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        """Initialize CLI with API base URL."""
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url, timeout=30.0)
    
    def status(self) -> None:
        """Check and display system status."""
        try:
            response = self.client.get("/health")
            response.raise_for_status()
            data = response.json()
            
            console.print("🏥 [bold green]System Health Check[/bold green]")
            console.print(f"Status: {data.get('status', 'unknown')}")
            
            # Display component status
            components = data.get('components', {})
            table = Table(title="Component Status")
            table.add_column("Component")
            table.add_column("Status")
            table.add_column("Details")
            
            for name, info in components.items():
                status = info.get('status', 'unknown')
                details = ', '.join([f"{k}: {v}" for k, v in info.items() if k != 'status'])
                
                status_color = "green" if status == "ok" else "red"
                table.add_row(name, f"[{status_color}]{status}[/{status_color}]", details)
            
            console.print(table)
            
        except httpx.RequestError as e:
            console.print(f"❌ [red]Connection error: {e}[/red]")
            console.print("Make sure the local-rag service is running:")
            console.print("  sudo systemctl start local-rag")
            sys.exit(1)
        except httpx.HTTPStatusError as e:
            console.print(f"❌ [red]API error: {e.response.status_code}[/red]")
            sys.exit(1)
    
    def import_content(self, source: str, source_type: str = "auto") -> None:
        """Import content from file, directory, or URL."""
        # Auto-detect source type if not specified
        if source_type == "auto":
            if source.startswith(("http://", "https://")):
                source_type = "url"
            elif source.endswith(("/", "\\")):
                source_type = "directory"
            else:
                source_type = "file"
        
        console.print(f"📥 [bold blue]Importing content from {source_type}: {source}[/bold blue]")
        
        try:
            response = self.client.post("/api/import", json={
                "source": source,
                "source_type": source_type
            })
            response.raise_for_status()
            data = response.json()
            
            console.print("✅ [green]Import completed successfully[/green]")
            console.print(f"Documents processed: {data.get('documents_processed', 0)}")
            console.print(f"Documents added: {data.get('documents_added', 0)}")
            
        except httpx.RequestError as e:
            console.print(f"❌ [red]Connection error: {e}[/red]")
            sys.exit(1)
        except httpx.HTTPStatusError as e:
            console.print(f"❌ [red]Import failed: {e.response.status_code}[/red]")
            try:
                error_detail = e.response.json().get('detail', 'Unknown error')
                console.print(f"Error: {error_detail}")
            except:
                console.print(f"Response: {e.response.text}")
            sys.exit(1)
    
    def reset_database(self) -> None:
        """Reset the vector database."""
        console.print("🗑️  [bold yellow]Resetting vector database...[/bold yellow]")
        
        try:
            response = self.client.post("/api/reset")
            response.raise_for_status()
            data = response.json()
            
            console.print("✅ [green]Database reset successfully[/green]")
            console.print(f"Message: {data.get('message', 'Reset completed')}")
            
        except httpx.RequestError as e:
            console.print(f"❌ [red]Connection error: {e}[/red]")
            sys.exit(1)
        except httpx.HTTPStatusError as e:
            console.print(f"❌ [red]Reset failed: {e.response.status_code}[/red]")
            sys.exit(1)
    
    def query(self, question: str) -> None:
        """Ask a question to the RAG system."""
        console.print(f"❓ [bold blue]Query: {question}[/bold blue]")
        
        try:
            response = self.client.post("/api/query", json={"query": question})
            response.raise_for_status()
            data = response.json()
            
            console.print("\n💬 [bold green]Response:[/bold green]")
            console.print(data.get('response', 'No response generated'))
            
            # Show sources if available
            sources = data.get('sources', [])
            if sources:
                console.print(f"\n📚 [bold cyan]Sources ({len(sources)}):[/bold cyan]")
                for i, source in enumerate(sources[:3], 1):  # Show top 3 sources
                    metadata = source.get('metadata', {})
                    title = metadata.get('title', 'Unknown')
                    source_path = metadata.get('source', 'Unknown')
                    console.print(f"  {i}. {title} ({source_path})")
            
        except httpx.RequestError as e:
            console.print(f"❌ [red]Connection error: {e}[/red]")
            sys.exit(1)
        except httpx.HTTPStatusError as e:
            console.print(f"❌ [red]Query failed: {e.response.status_code}[/red]")
            sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Local RAG CLI")
    parser.add_argument("--url", default=DEFAULT_BASE_URL, help="API base URL")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Status command
    subparsers.add_parser("status", help="Check system health")
    
    # Import command
    import_parser = subparsers.add_parser("import", help="Import content")
    import_parser.add_argument("source", help="File path, directory, or URL")
    import_parser.add_argument("--type", choices=["file", "directory", "url", "auto"], 
                              default="auto", help="Source type")
    
    # Reset command
    subparsers.add_parser("reset-db", help="Reset vector database")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Ask a question")
    query_parser.add_argument("question", nargs="+", help="Question to ask")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = LocalRAGCLI(base_url=args.url)
    
    try:
        if args.command == "status":
            cli.status()
        elif args.command == "import":
            cli.import_content(args.source, args.type)
        elif args.command == "reset-db":
            cli.reset_database()
        elif args.command == "query":
            question = " ".join(args.question)
            cli.query(question)
    except KeyboardInterrupt:
        console.print("\n👋 [yellow]Interrupted by user[/yellow]")
        sys.exit(1)


if __name__ == "__main__":
    main()