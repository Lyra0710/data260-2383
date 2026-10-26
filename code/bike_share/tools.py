"""Schema-defined tools for the Capital Bikeshare recommendation agent."""

from __future__ import annotations

import ast
import csv
import re
import sqlite3
from datetime import datetime, timezone
from html.parser import HTMLParser
from io import StringIO
from typing import Any

import httpx

CSV_SQL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "csv_sql",
        "description": "Run one read-only SELECT query over the uploaded trips CSV.",
        "parameters": {
            "type": "object",
            "properties": {"sql": {"type": "string"}},
            "required": ["sql"],
            "additionalProperties": False,
        },
    },
}

POLICY_RETRIEVER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "policy_retriever",
        "description": "Retrieve short pricing-policy passages from a supplied URL.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "query": {"type": "string"},
                "k": {"type": "integer", "minimum": 1, "maximum": 5},
            },
            "required": ["url", "query"],
            "additionalProperties": False,
        },
    },
}

CALCULATOR_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Evaluate a basic arithmetic expression safely.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string"},
                "units": {"type": "string"},
            },
            "required": ["expression"],
            "additionalProperties": False,
        },
    },
}

TOOL_SCHEMAS = [CSV_SQL_SCHEMA, POLICY_RETRIEVER_SCHEMA, CALCULATOR_SCHEMA]
CALCULATOR_PATTERN = re.compile(r"^[0-9+\-*/().\s]+$")
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; DATA260-HW7/1.0)"}


def timestamp() -> str:
    """Return a UTC timestamp for the common tool response shape."""

    return datetime.now(timezone.utc).isoformat()


def success(data: Any, source: str) -> dict[str, Any]:
    return {"success": True, "data": data, "source": source, "ts": timestamp()}


def failure(error: str, source: str) -> dict[str, Any]:
    return {"success": False, "error": error, "source": source, "ts": timestamp()}


def is_read_only_select(sql: str) -> bool:
    """Allow one SELECT statement and reject write or multi-statement SQL."""

    statement = sql.strip().rstrip(";").strip()
    return (
        bool(statement)
        and statement.upper().startswith("SELECT ")
        and ";" not in statement
    )


def quote_identifier(name: str) -> str:
    """Quote a CSV header for use as a SQLite column identifier."""

    return '"' + name.replace('"', '""') + '"'


def csv_sql(csv_text: str, sql: str) -> dict[str, Any]:
    """Run a read-only SELECT query against an uploaded CSV represented as text."""

    source = "uploaded.csv"
    if not is_read_only_select(sql):
        return failure("Only one read-only SELECT statement is allowed.", source)

    try:
        reader = csv.DictReader(StringIO(csv_text))
        headers = reader.fieldnames
        if not headers:
            return failure("The uploaded CSV has no header row.", source)

        connection = sqlite3.connect(":memory:")
        quoted_columns = ", ".join(f"{quote_identifier(name)} TEXT" for name in headers)
        connection.execute(f"CREATE TABLE trips ({quoted_columns})")
        placeholders = ", ".join("?" for _ in headers)
        connection.executemany(
            f"INSERT INTO trips VALUES ({placeholders})",
            [tuple(row.get(header, "") for header in headers) for row in reader],
        )
        cursor = connection.execute(sql.rstrip(";").strip())
        column_names = [column[0] for column in cursor.description or []]
        rows = [
            dict(zip(column_names, row, strict=True)) for row in cursor.fetchmany(1000)
        ]
        connection.close()
        return success({"rows": rows, "row_count": len(rows), "source": source}, source)
    except (csv.Error, sqlite3.Error, UnicodeError) as error:
        return failure(f"CSV or SQL error: {error}", source)


class PricingTextParser(HTMLParser):
    """Extract visible text while skipping script and style contents."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag in {"script", "style"}:
            self.hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth:
            self.parts.append(data)


def pricing_text(html: str) -> str:
    parser = PricingTextParser()
    parser.feed(html)
    return " ".join(" ".join(parser.parts).split())


def policy_retriever(url: str, query: str, k: int = 3) -> dict[str, Any]:
    """Fetch a policy page and return short, query-ranked text passages."""

    if not 1 <= k <= 5:
        return failure("k must be an integer from 1 through 5.", url)
    if not url.startswith(("http://", "https://")):
        return failure("The pricing URL must use http or https.", url)

    try:
        response = httpx.get(
            url,
            follow_redirects=True,
            headers=HTTP_HEADERS,
            timeout=20.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        return failure(f"Could not retrieve the pricing page: {error}", url)

    text = pricing_text(response.text)
    query_words = {word.casefold() for word in re.findall(r"[a-zA-Z]+", query)}
    passages = [text[index : index + 500] for index in range(0, len(text), 500)]

    scored = []
    for passage in passages:
        lowered = passage.casefold()
        score = sum(word in lowered for word in query_words) / max(len(query_words), 1)
        if score:
            scored.append({"text": passage, "source": url, "score": round(score, 3)})
    scored.sort(key=lambda passage: passage["score"], reverse=True)
    return success({"passages": scored[:k]}, url)


def evaluate_expression(node: ast.AST) -> float:
    """Evaluate numeric arithmetic AST nodes without using eval."""

    if isinstance(node, ast.Expression):
        return evaluate_expression(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = evaluate_expression(node.operand)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp) and isinstance(
        node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)
    ):
        left = evaluate_expression(node.left)
        right = evaluate_expression(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        return left / right
    raise ValueError(
        "Only arithmetic with numbers, parentheses, and + - * / is allowed."
    )


def calculator(expression: str, units: str | None = None) -> dict[str, Any]:
    """Evaluate an allow-listed arithmetic expression."""

    source = "calculator"
    if not CALCULATOR_PATTERN.fullmatch(expression):
        return failure("Expression contains unsupported characters.", source)
    try:
        value = evaluate_expression(ast.parse(expression, mode="eval"))
    except (SyntaxError, ValueError, ZeroDivisionError) as error:
        return failure(f"Calculation error: {error}", source)

    data: dict[str, Any] = {"value": value}
    if units:
        data["units"] = units
    return success(data, source)
