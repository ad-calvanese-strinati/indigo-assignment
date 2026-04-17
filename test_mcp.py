#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp/")
DEFAULT_TOKEN = os.getenv("MCP_AUTH_TOKEN", "change-me")
DEFAULT_PROTOCOL_VERSION = os.getenv("MCP_PROTOCOL_VERSION", "2025-03-26")


@dataclass
class McpClient:
    url: str
    token: str
    protocol_version: str

    def post(self, payload: dict[str, Any]) -> tuple[int, dict[str, str], str]:
        body = json.dumps(payload).encode("utf-8")
        normalized_url = self.url if self.url.endswith("/") else f"{self.url}/"
        request = urllib.request.Request(
            normalized_url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": self.protocol_version,
            },
        )

        try:
            with urllib.request.urlopen(request) as response:
                raw_body = response.read().decode("utf-8")
                headers = {key: value for key, value in response.headers.items()}
                return response.status, headers, raw_body
        except urllib.error.HTTPError as error:
            raw_body = error.read().decode("utf-8", errors="replace")
            headers = {key: value for key, value in error.headers.items()}
            return error.code, headers, raw_body

    def rpc(self, method: str, params: dict[str, Any], request_id: int) -> dict[str, Any]:
        status, headers, body = self.post(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params,
            }
        )

        if status >= 400:
            raise RuntimeError(
                f"HTTP {status} calling {method}\nHeaders: {json.dumps(headers, indent=2)}\nBody: {body}"
            )

        if headers.get("Content-Type", "").startswith("text/event-stream"):
            raise RuntimeError(
                "Received SSE response. This test client expects a JSON response.\n"
                "If needed, we can extend it to parse streamable responses too."
            )

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Non-JSON response for {method}.\n"
                f"Headers: {json.dumps(headers, indent=2)}\n"
                f"Body: {body!r}"
            ) from exc

        if "error" in payload:
            raise RuntimeError(f"MCP error for {method}: {json.dumps(payload['error'], indent=2)}")

        return payload


def initialize(client: McpClient) -> dict[str, Any]:
    return client.rpc(
        "initialize",
        {
            "protocolVersion": client.protocol_version,
            "capabilities": {},
            "clientInfo": {
                "name": "indigo-mcp-test-client",
                "version": "0.1.0",
            },
        },
        request_id=1,
    )


def list_tools(client: McpClient) -> dict[str, Any]:
    return client.rpc("tools/list", {}, request_id=2)


def call_tool(client: McpClient, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return client.rpc(
        "tools/call",
        {
            "name": tool_name,
            "arguments": arguments,
        },
        request_id=3,
    )


def run_smoke(client: McpClient, query: str, tag: str | None) -> dict[str, Any]:
    results: dict[str, Any] = {
        "initialize": initialize(client),
        "tools_list": list_tools(client),
        "list_documents": call_tool(client, "list_documents", {}),
        "list_tags": call_tool(client, "list_tags", {}),
        "search": call_tool(client, "search", {"query": query, "limit": 3}),
    }
    if tag:
        results["search_by_tag"] = call_tool(
            client,
            "search_by_tag",
            {"query": query, "tags": [tag], "limit": 3},
        )
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Minimal MCP test client for Indigo.")
    parser.add_argument(
        "command",
        choices=["initialize", "list-tools", "call", "smoke"],
        help="Operation to run against the MCP server.",
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="MCP server URL.")
    parser.add_argument("--token", default=DEFAULT_TOKEN, help="Bearer token for MCP auth.")
    parser.add_argument(
        "--protocol-version",
        default=DEFAULT_PROTOCOL_VERSION,
        help="MCP protocol version header and initialize protocol version.",
    )
    parser.add_argument("--tool", help="Tool name for the call command.")
    parser.add_argument(
        "--args",
        default="{}",
        help='JSON object passed as tool arguments for the "call" command.',
    )
    parser.add_argument(
        "--query",
        default="remote setup",
        help='Search query used by the "smoke" command.',
    )
    parser.add_argument(
        "--tag",
        default=None,
        help='Optional tag used by the "smoke" command for search_by_tag.',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    client = McpClient(
        url=args.url,
        token=args.token,
        protocol_version=args.protocol_version,
    )

    try:
        if args.command == "initialize":
            output = initialize(client)
        elif args.command == "list-tools":
            initialize(client)
            output = list_tools(client)
        elif args.command == "call":
            if not args.tool:
                raise ValueError('--tool is required when command is "call".')
            initialize(client)
            output = call_tool(client, args.tool, json.loads(args.args))
        else:
            output = run_smoke(client, query=args.query, tag=args.tag)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
