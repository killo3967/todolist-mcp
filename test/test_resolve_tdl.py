"""Unit tests for _resolve_tdl_file() — env var > mcp_server.ini > fallback."""



class TestResolveTdlFile:
    def test_env_var_wins_over_ini(self, tmp_path, monkeypatch):
        """Explicit TODOLIST_FILE env var takes priority over INI."""
        from src.manager import _resolve_tdl_file

        ini_path = tmp_path / "mcp_server.ini"
        ini_path.write_text("[server]\nactive = yes\ntdl_file = /tmp/from_ini.tdl\n")

        import src.manager as tdl_mcp_server
        monkeypatch.setattr(tdl_mcp_server, "__file__", str(tmp_path / "tdl_mcp_server.py"))
        monkeypatch.setenv("TODOLIST_FILE", "/tmp/from_env.tdl")

        assert _resolve_tdl_file() == "/tmp/from_env.tdl"

    def test_ini_active_yes_when_no_env(self, tmp_path, monkeypatch):
        """Without env var, active INI is used."""
        from src.manager import _resolve_tdl_file

        ini_path = tmp_path / "mcp_server.ini"
        ini_path.write_text("[server]\nactive = yes\ntdl_file = /tmp/from_ini.tdl\n")

        import src.manager as tdl_mcp_server
        monkeypatch.setattr(tdl_mcp_server, "__file__", str(tmp_path / "tdl_mcp_server.py"))
        monkeypatch.delenv("TODOLIST_FILE", raising=False)

        assert _resolve_tdl_file() == "/tmp/from_ini.tdl"

    def test_ini_active_no_falls_back_to_fallback(self, tmp_path, monkeypatch):
        """active=no + no env var → hardcoded fallback."""
        from src.manager import _resolve_tdl_file

        ini_path = tmp_path / "mcp_server.ini"
        ini_path.write_text("[server]\nactive = no\ntdl_file = /tmp/from_ini.tdl\n")

        import src.manager as tdl_mcp_server
        monkeypatch.setattr(tdl_mcp_server, "__file__", str(tmp_path / "tdl_mcp_server.py"))
        monkeypatch.delenv("TODOLIST_FILE", raising=False)

        result = _resolve_tdl_file()
        assert "todolist.tdl" in result

    def test_ini_missing_tdl_file_falls_back(self, tmp_path, monkeypatch):
        """active=yes but no tdl_file → fallback."""
        from src.manager import _resolve_tdl_file

        ini_path = tmp_path / "mcp_server.ini"
        ini_path.write_text("[server]\nactive = yes\n# no tdl_file\n")

        import src.manager as tdl_mcp_server
        monkeypatch.setattr(tdl_mcp_server, "__file__", str(tmp_path / "tdl_mcp_server.py"))
        monkeypatch.delenv("TODOLIST_FILE", raising=False)

        result = _resolve_tdl_file()
        assert "todolist.tdl" in result

    def test_ini_active_defaults_true(self, tmp_path, monkeypatch):
        """When active key is missing, defaults to True."""
        from src.manager import _resolve_tdl_file

        ini_path = tmp_path / "mcp_server.ini"
        ini_path.write_text("[server]\ntdl_file = /tmp/from_ini.tdl\n")

        import src.manager as tdl_mcp_server
        monkeypatch.setattr(tdl_mcp_server, "__file__", str(tmp_path / "tdl_mcp_server.py"))
        monkeypatch.delenv("TODOLIST_FILE", raising=False)

        assert _resolve_tdl_file() == "/tmp/from_ini.tdl"

    def test_no_env_no_ini_uses_fallback(self, tmp_path, monkeypatch):
        """Without env var or INI file, hardcoded fallback is used."""
        import src.manager as tdl_mcp_server
        from src.manager import _resolve_tdl_file
        monkeypatch.setattr(tdl_mcp_server, "__file__", str(tmp_path / "tdl_mcp_server.py"))
        monkeypatch.delenv("TODOLIST_FILE", raising=False)

        result = _resolve_tdl_file()
        assert "todolist.tdl" in result
