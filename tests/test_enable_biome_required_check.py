import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "enable_biome_required_check.py"
SPEC = importlib.util.spec_from_file_location("enable_biome_required_check", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Failed to load enable_biome_required_check module")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class EnableBiomeRequiredCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.prev_gh_token = os.environ.get("GH_TOKEN")
        self.prev_github_token = os.environ.get("GITHUB_TOKEN")
        os.environ.pop("GH_TOKEN", None)
        os.environ.pop("GITHUB_TOKEN", None)

    def tearDown(self) -> None:
        os.environ.pop("GH_TOKEN", None)
        os.environ.pop("GITHUB_TOKEN", None)
        if self.prev_gh_token is not None:
            os.environ["GH_TOKEN"] = self.prev_gh_token
        if self.prev_github_token is not None:
            os.environ["GITHUB_TOKEN"] = self.prev_github_token

    def test_get_token_reads_from_dotenv_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("GH_TOKEN=from-dotenv\n", encoding="utf-8")

            with patch.object(MODULE, "dotenv_candidate_paths", return_value=[str(env_path)]):
                token = MODULE.get_token()

        self.assertEqual(token, "from-dotenv")

    def test_load_token_from_dotenv_does_not_override_existing_env(self) -> None:
        os.environ["GH_TOKEN"] = "from-env"

        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("GH_TOKEN=from-dotenv\n", encoding="utf-8")
            with patch.object(MODULE, "dotenv_candidate_paths", return_value=[str(env_path)]):
                MODULE.load_token_from_dotenv()

        self.assertEqual(os.environ.get("GH_TOKEN"), "from-env")

    def test_parse_env_assignment_handles_export_and_quotes(self) -> None:
        parsed = MODULE.parse_env_assignment('export GITHUB_TOKEN="quoted-value"')
        self.assertEqual(parsed, ("GITHUB_TOKEN", "quoted-value"))


if __name__ == "__main__":
    unittest.main()
