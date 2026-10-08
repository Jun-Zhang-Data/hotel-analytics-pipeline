import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from semantic_api.environment import load_local_environment


class EnvironmentTests(unittest.TestCase):
    def test_loads_values_from_dotenv_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "OPENAI_API_KEY=test-key\n"
                "OPENAI_SEMANTIC_MODEL=test-model\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {}, clear=True):
                loaded = load_local_environment(env_path)

                self.assertTrue(loaded)
                self.assertEqual(os.environ["OPENAI_API_KEY"], "test-key")
                self.assertEqual(
                    os.environ["OPENAI_SEMANTIC_MODEL"],
                    "test-model",
                )

    def test_does_not_override_existing_environment(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "OPENAI_API_KEY=file-key\n",
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {"OPENAI_API_KEY": "shell-key"},
                clear=True,
            ):
                load_local_environment(env_path)
                self.assertEqual(
                    os.environ["OPENAI_API_KEY"],
                    "shell-key",
                )


if __name__ == "__main__":
    unittest.main()
