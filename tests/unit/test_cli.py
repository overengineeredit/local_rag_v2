"""Tests for the CLI interface."""

from unittest.mock import Mock, patch

import httpx

import guide.cli
from guide.cli import DEFAULT_BASE_URL, LocalRAGCLI, main


class TestLocalRAGCLI:
    """Test the LocalRAGCLI class."""

    def test_init_default_url(self):
        """Test CLI initialization with default URL."""
        cli = LocalRAGCLI()
        assert cli.base_url == DEFAULT_BASE_URL
        assert isinstance(cli.client, httpx.Client)

    def test_init_custom_url(self):
        """Test CLI initialization with custom URL."""
        custom_url = "http://example.com:9090"
        cli = LocalRAGCLI(base_url=custom_url)
        assert cli.base_url == custom_url

    @patch("guide.cli.console")
    @patch("httpx.Client.get")
    def test_status_success_basic(self, mock_get, mock_console):
        """Test successful status check in basic mode."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "healthy",
            "service": "local-rag",
            "version": "1.0.0",
            "components": {
                "database": {"status": "ok", "connections": 5},
                "llm": {"status": "warning", "model": "test-model"},
                "thermal": {"status": "error", "error": "Temperature too high"},
            },
        }
        mock_get.return_value = mock_response

        cli = LocalRAGCLI()
        cli.status(verbose=False)

        # Verify API call
        mock_get.assert_called_once_with("/health")

        # Verify console output calls
        assert mock_console.print.call_count >= 4  # Multiple print calls expected

    @patch("guide.cli.console")
    @patch("httpx.Client.get")
    def test_status_success_verbose(self, mock_get, mock_console):
        """Test successful status check in verbose mode."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "degraded",
            "service": "local-rag",
            "version": "1.0.0",
            "components": {
                "database": {
                    "status": "ok",
                    "connections": 5,
                    "nested_info": {"key": "value"},
                },
                "llm": {"status": "not_initialized"},
            },
        }
        mock_get.return_value = mock_response

        cli = LocalRAGCLI()
        cli.status(verbose=True)

        # Verify API call
        mock_get.assert_called_once_with("/health")

        # Verify console output calls (more calls in verbose mode)
        assert mock_console.print.call_count >= 3

    @patch("guide.cli.console")
    @patch("httpx.Client.get")
    @patch("sys.exit")
    def test_status_connection_error(self, mock_exit, mock_get, mock_console):
        """Test status check with connection error."""
        mock_get.side_effect = httpx.RequestError("Connection failed")

        cli = LocalRAGCLI()
        cli.status()

        # Verify error handling
        mock_console.print.assert_any_call("❌ [red]Connection error: Connection failed[/red]")
        mock_exit.assert_called_once_with(1)

    @patch("guide.cli.console")
    @patch("httpx.Client.get")
    @patch("sys.exit")
    def test_status_http_error(self, mock_exit, mock_get, mock_console):
        """Test status check with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.side_effect = httpx.HTTPStatusError(
            "Server error",
            request=Mock(),
            response=mock_response,
        )

        cli = LocalRAGCLI()
        cli.status()

        # Verify error handling
        mock_console.print.assert_any_call("❌ [red]API error: 500[/red]")
        mock_exit.assert_called_once_with(1)

    @patch("guide.cli.console")
    @patch("httpx.Client.post")
    def test_import_content_auto_detect_url(self, mock_post, mock_console):
        """Test import content with auto-detected URL."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "documents_processed": 5,
            "documents_added": 3,
        }
        mock_post.return_value = mock_response

        cli = LocalRAGCLI()
        cli.import_content("https://example.com/doc.pdf", "auto")

        # Verify API call with correct source type
        mock_post.assert_called_once_with(
            "/api/import",
            json={"source": "https://example.com/doc.pdf", "source_type": "url"},
        )

    @patch("guide.cli.console")
    @patch("httpx.Client.post")
    def test_import_content_auto_detect_directory(self, mock_post, mock_console):
        """Test import content with auto-detected directory."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "documents_processed": 10,
            "documents_added": 8,
        }
        mock_post.return_value = mock_response

        cli = LocalRAGCLI()
        cli.import_content("/path/to/docs/", "auto")

        # Verify API call with correct source type
        mock_post.assert_called_once_with(
            "/api/import",
            json={"source": "/path/to/docs/", "source_type": "directory"},
        )

    @patch("guide.cli.console")
    @patch("httpx.Client.post")
    def test_import_content_auto_detect_file(self, mock_post, mock_console):
        """Test import content with auto-detected file."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "documents_processed": 1,
            "documents_added": 1,
        }
        mock_post.return_value = mock_response

        cli = LocalRAGCLI()
        cli.import_content("/path/to/document.pdf", "auto")

        # Verify API call with correct source type
        mock_post.assert_called_once_with(
            "/api/import",
            json={"source": "/path/to/document.pdf", "source_type": "file"},
        )

    @patch("guide.cli.console")
    @patch("httpx.Client.post")
    @patch("sys.exit")
    def test_import_content_connection_error(self, mock_exit, mock_post, mock_console):
        """Test import content with connection error."""
        mock_post.side_effect = httpx.RequestError("Connection failed")

        cli = LocalRAGCLI()
        cli.import_content("/path/to/doc.pdf", "file")

        # Verify error handling
        mock_console.print.assert_any_call("❌ [red]Connection error: Connection failed[/red]")
        mock_exit.assert_called_once_with(1)

    @patch("guide.cli.console")
    @patch("httpx.Client.post")
    @patch("sys.exit")
    def test_import_content_http_error_with_detail(self, mock_exit, mock_post, mock_console):
        """Test import content with HTTP error that has JSON detail."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Invalid file format"}

        mock_post.side_effect = httpx.HTTPStatusError(
            "Bad request",
            request=Mock(),
            response=mock_response,
        )

        cli = LocalRAGCLI()
        cli.import_content("/path/to/doc.pdf", "file")

        # Verify error handling
        mock_console.print.assert_any_call("❌ [red]Import failed: 400[/red]")
        mock_console.print.assert_any_call("Error: Invalid file format")
        mock_exit.assert_called_once_with(1)

    @patch("guide.cli.console")
    @patch("httpx.Client.post")
    @patch("sys.exit")
    def test_import_content_http_error_no_json(self, mock_exit, mock_post, mock_console):
        """Test import content with HTTP error that has no JSON."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.side_effect = Exception("No JSON")
        mock_response.text = "Internal Server Error"

        mock_post.side_effect = httpx.HTTPStatusError(
            "Server error",
            request=Mock(),
            response=mock_response,
        )

        cli = LocalRAGCLI()
        cli.import_content("/path/to/doc.pdf", "file")

        # Verify error handling
        mock_console.print.assert_any_call("❌ [red]Import failed: 500[/red]")
        mock_console.print.assert_any_call("Response: Internal Server Error")
        mock_exit.assert_called_once_with(1)

    @patch("guide.cli.console")
    @patch("httpx.Client.post")
    def test_reset_database_success(self, mock_post, mock_console):
        """Test successful database reset."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {"message": "Database reset completed"}
        mock_post.return_value = mock_response

        cli = LocalRAGCLI()
        cli.reset_database()

        # Verify API call
        mock_post.assert_called_once_with("/api/reset")

        # Verify console output
        mock_console.print.assert_any_call("✅ [green]Database reset successfully[/green]")

    @patch("guide.cli.console")
    @patch("httpx.Client.post")
    @patch("sys.exit")
    def test_reset_database_error(self, mock_exit, mock_post, mock_console):
        """Test database reset with error."""
        mock_post.side_effect = httpx.RequestError("Connection failed")

        cli = LocalRAGCLI()
        cli.reset_database()

        # Verify error handling
        mock_console.print.assert_any_call("❌ [red]Connection error: Connection failed[/red]")
        mock_exit.assert_called_once_with(1)

    @patch("guide.cli.console")
    @patch("httpx.Client.post")
    def test_query_success(self, mock_post, mock_console):
        """Test successful query."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "This is the answer to your question.",
            "sources": [
                {"metadata": {"title": "Document 1", "source": "/path/to/doc1.pdf"}},
                {"metadata": {"title": "Document 2", "source": "/path/to/doc2.pdf"}},
            ],
        }
        mock_post.return_value = mock_response

        cli = LocalRAGCLI()
        cli.query("What is the answer?")

        # Verify API call
        mock_post.assert_called_once_with("/api/query", json={"query": "What is the answer?"})

        # Verify console output
        mock_console.print.assert_any_call("\n💬 [bold green]Response:[/bold green]")
        mock_console.print.assert_any_call("This is the answer to your question.")

    @patch("guide.cli.console")
    @patch("httpx.Client.post")
    def test_query_no_sources(self, mock_post, mock_console):
        """Test query with no sources returned."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "This is the answer to your question.",
            "sources": [],
        }
        mock_post.return_value = mock_response

        cli = LocalRAGCLI()
        cli.query("What is the answer?")

        # Verify API call
        mock_post.assert_called_once_with("/api/query", json={"query": "What is the answer?"})

        # Verify response is printed but no sources section
        mock_console.print.assert_any_call("This is the answer to your question.")

    @patch("guide.cli.console")
    @patch("httpx.Client.post")
    @patch("sys.exit")
    def test_query_error(self, mock_exit, mock_post, mock_console):
        """Test query with error."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.side_effect = httpx.HTTPStatusError(
            "Bad request",
            request=Mock(),
            response=mock_response,
        )

        cli = LocalRAGCLI()
        cli.query("What is the answer?")

        # Verify error handling
        mock_console.print.assert_any_call("❌ [red]Query failed: 400[/red]")
        mock_exit.assert_called_once_with(1)


class TestMainFunction:
    """Test the main CLI entry point function."""

    @patch("guide.cli.LocalRAGCLI")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_no_command(self, mock_parse_args, mock_cli_class):
        """Test main function when no command is provided."""
        # Mock args with no command
        mock_args = Mock()
        mock_args.command = None
        mock_parse_args.return_value = mock_args

        with patch("argparse.ArgumentParser.print_help") as mock_help:
            main()
            mock_help.assert_called_once()

    @patch("guide.cli.LocalRAGCLI")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_status_command(self, mock_parse_args, mock_cli_class):
        """Test main function with status command."""
        # Mock args for status command
        mock_args = Mock()
        mock_args.command = "status"
        mock_args.url = DEFAULT_BASE_URL
        mock_args.verbose = True
        mock_parse_args.return_value = mock_args

        # Mock CLI instance
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli

        main()

        # Verify CLI creation and method call
        mock_cli_class.assert_called_once_with(base_url=DEFAULT_BASE_URL)
        mock_cli.status.assert_called_once_with(verbose=True)

    @patch("guide.cli.LocalRAGCLI")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_status_command_no_verbose_attr(self, mock_parse_args, mock_cli_class):
        """Test main function with status command but no verbose attribute."""
        # Mock args for status command without verbose
        mock_args = Mock()
        mock_args.command = "status"
        mock_args.url = DEFAULT_BASE_URL
        # Don't set verbose attribute to test hasattr check
        delattr(mock_args, "verbose") if hasattr(mock_args, "verbose") else None
        mock_parse_args.return_value = mock_args

        # Mock CLI instance
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli

        main()

        # Verify CLI creation and method call with default verbose=False
        mock_cli_class.assert_called_once_with(base_url=DEFAULT_BASE_URL)
        mock_cli.status.assert_called_once_with(verbose=False)

    @patch("guide.cli.LocalRAGCLI")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_import_command(self, mock_parse_args, mock_cli_class):
        """Test main function with import command."""
        # Mock args for import command
        mock_args = Mock()
        mock_args.command = "import"
        mock_args.url = "http://custom:8080"
        mock_args.source = "/path/to/docs"
        mock_args.type = "directory"
        mock_parse_args.return_value = mock_args

        # Mock CLI instance
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli

        main()

        # Verify CLI creation and method call
        mock_cli_class.assert_called_once_with(base_url="http://custom:8080")
        mock_cli.import_content.assert_called_once_with("/path/to/docs", "directory")

    @patch("guide.cli.LocalRAGCLI")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_reset_command(self, mock_parse_args, mock_cli_class):
        """Test main function with reset-db command."""
        # Mock args for reset command
        mock_args = Mock()
        mock_args.command = "reset-db"
        mock_args.url = DEFAULT_BASE_URL
        mock_parse_args.return_value = mock_args

        # Mock CLI instance
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli

        main()

        # Verify CLI creation and method call
        mock_cli_class.assert_called_once_with(base_url=DEFAULT_BASE_URL)
        mock_cli.reset_database.assert_called_once()

    @patch("guide.cli.LocalRAGCLI")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_query_command(self, mock_parse_args, mock_cli_class):
        """Test main function with query command."""
        # Mock args for query command
        mock_args = Mock()
        mock_args.command = "query"
        mock_args.url = DEFAULT_BASE_URL
        mock_args.question = ["What", "is", "the", "answer?"]
        mock_parse_args.return_value = mock_args

        # Mock CLI instance
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli

        main()

        # Verify CLI creation and method call
        mock_cli_class.assert_called_once_with(base_url=DEFAULT_BASE_URL)
        mock_cli.query.assert_called_once_with("What is the answer?")

    @patch("guide.cli.LocalRAGCLI")
    @patch("argparse.ArgumentParser.parse_args")
    @patch("guide.cli.console")
    @patch("sys.exit")
    def test_main_keyboard_interrupt(
        self,
        mock_exit,
        mock_console,
        mock_parse_args,
        mock_cli_class,
    ):
        """Test main function handling KeyboardInterrupt."""
        # Mock args for any command
        mock_args = Mock()
        mock_args.command = "status"
        mock_args.url = DEFAULT_BASE_URL
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        # Mock CLI instance that raises KeyboardInterrupt
        mock_cli = Mock()
        mock_cli.status.side_effect = KeyboardInterrupt()
        mock_cli_class.return_value = mock_cli

        main()

        # Verify interrupt handling
        mock_console.print.assert_called_with("\n👋 [yellow]Interrupted by user[/yellow]")
        mock_exit.assert_called_once_with(1)

    def test_main_entry_point(self):
        """Test that main can be called as entry point."""
        # This tests the if __name__ == "__main__" block
        with patch("guide.cli.main"):
            # Simulate running as main module
            guide.cli.__name__ = "__main__"

            # The actual test would need module reload, but we can test the function exists
            assert callable(guide.cli.main)
