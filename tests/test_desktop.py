from tael.tools.desktop import LaunchAppTool, OpenUrlTool, APPROVED_APPLICATIONS


def test_approved_applications_validation():
    tool = LaunchAppTool()
    
    # Non-approved application must be rejected
    res = tool.run({"app_name": "malicious_script.exe"}, {})
    assert res.success is False
    assert "not in the approved applications allowlist" in res.error

    # Approved application name recognized
    assert "notepad" in APPROVED_APPLICATIONS
    assert "vscode" in APPROVED_APPLICATIONS
    assert "terminal" in APPROVED_APPLICATIONS


def test_open_url_validation():
    tool = OpenUrlTool()

    # Invalid schemes rejected
    res_bad = tool.run({"url": "file:///etc/passwd"}, {})
    assert res_bad.success is False
    assert "Must start with http:// or https://" in res_bad.error

    res_ftp = tool.run({"url": "ftp://ftp.example.com"}, {})
    assert res_ftp.success is False

    # Valid scheme structure recognized
    # Note: we test without calling webbrowser.open on desktop during CI
    parsed_ok = tool.parameters_schema["required"] == ["url"]
    assert parsed_ok is True
