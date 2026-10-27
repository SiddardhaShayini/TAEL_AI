from pathlib import Path
from tael.tools.base import ToolResult
from tael.tools.registry import ToolRegistry, validate_schema
from tael.tools.workspace import ReadFileTool, WriteFileTool, ListDirTool, SearchFilesTool
from tael.tools.system_info import SystemInfoTool


def test_schema_validator():
    schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "count": {"type": "integer"},
        },
        "required": ["path"],
    }

    # Valid
    assert validate_schema(schema, {"path": "a.txt", "count": 10}) is None
    # Missing required
    assert "Missing required parameter" in validate_schema(schema, {"count": 10})
    # Wrong type
    assert "expected integer" in validate_schema(schema, {"path": "a.txt", "count": "not_an_int"})


def test_workspace_file_tools(tmp_path: Path):
    ws = str(tmp_path)
    context = {"workspace_root": ws}

    write_tool = WriteFileTool()
    read_tool = ReadFileTool()
    list_tool = ListDirTool()
    search_tool = SearchFilesTool()

    # 1. Write file
    w_res = write_tool.run({"path": "src/hello.py", "content": "print('hello world')\n# sample comment\n"}, context)
    assert w_res.success is True
    assert (tmp_path / "src" / "hello.py").exists()

    # 2. Read file
    r_res = read_tool.run({"path": "src/hello.py", "offset": 1, "limit": 10}, context)
    assert r_res.success is True
    assert "hello world" in r_res.data["content"]
    assert r_res.data["total_lines"] == 2

    # 3. List dir
    l_res = list_tool.run({"path": "."}, context)
    assert l_res.success is True
    entries = [e["path"] for e in l_res.data["entries"]]
    assert any("src/hello.py" in p for p in entries)

    # 4. Search files
    s_res = search_tool.run({"query": "sample"}, context)
    assert s_res.success is True
    assert len(s_res.data["matches"]) >= 1
    assert "sample comment" in s_res.data["matches"][0]["text"]


def test_system_info_tool():
    tool = SystemInfoTool()
    res = tool.run({}, {})
    assert res.success is True
    assert "total_ram_gb" in res.data
    assert "cpu_cores_logical" in res.data
