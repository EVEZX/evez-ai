"""Robust tool call parser for ClawBreak."""
import re
import json

def parse_tool_calls(text):
    """Parse tool calls from LLM response.
    
    Supported formats:
    - [tool:name(json_args)]  e.g. [tool:shell({"command": "ls"})]
    - [tool:name(key=val, key2=val2)]  e.g. [tool:shell(command=ls -la)]
    - ```tool:name\njson\n```  code block format
    - <tool:name>json</tool:name>  XML format
    """
    calls = []
    
    # Format 1: [tool:name(args)]
    pattern = r'\[tool:(\w+)\((.*?)\)\]'
    for match in re.finditer(pattern, text, re.DOTALL):
        tool_name = match.group(1)
        args_str = match.group(2).strip()
        args = _parse_args(args_str)
        calls.append({"name": tool_name, "args": args})
    
    # Format 2: ```tool:name\njson\n```
    pattern2 = r'```tool:(\w+)\s*\n(.*?)```'
    for match in re.finditer(pattern2, text, re.DOTALL):
        tool_name = match.group(1)
        args_str = match.group(2).strip()
        args = _parse_args(args_str)
        calls.append({"name": tool_name, "args": args})
    
    # Format 3: <tool:name>json</tool:name>
    pattern3 = r'<tool:(\w+)>(.*?)</tool:\1>'
    for match in re.finditer(pattern3, text, re.DOTALL):
        tool_name = match.group(1)
        args_str = match.group(2).strip()
        args = _parse_args(args_str)
        calls.append({"name": tool_name, "args": args})
    
    return calls

def _parse_args(args_str):
    """Parse arguments string into dict."""
    args_str = args_str.strip()
    
    # Try JSON first
    try:
        return json.loads(args_str)
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Try key=value pairs
    args = {}
    # Match key="value" or key=value pairs
    kv_pattern = r'(\w+)\s*=\s*"([^"]*)"'
    for match in re.finditer(kv_pattern, args_str):
        args[match.group(1)] = match.group(2)
    
    if args:
        # Also grab unquoted values
        kv_pattern2 = r'(\w+)\s*=\s*([^\s,]+(?:\s+[^\s,]+)*?)(?=\s*,\s*\w+\s*=|$)'
        for match in re.finditer(kv_pattern2, args_str):
            key = match.group(1)
            val = match.group(2).strip().rstrip(',')
            if key not in args:
                args[key] = val
        return args
    
    # Fallback: treat as a single input
    if args_str:
        return {"input": args_str}
    return {}
