import json
from pathlib import Path

import toml

ENC = dict(encoding="utf-8")
ROOT = Path(__file__).parent.parent
PYPROJECT = ROOT / "pyproject.toml"
PACKAGE_JSON = ROOT / "package.json"


def main():
  # read the Python version
  pyproject = PYPROJECT.read_text(**ENC)
  data = toml.loads(pyproject)
  project = data.get("tool", {}).get("tbump", {}).get("version", {})
  py_version = project.get("current")

  # set the JS version
  js_version = py_version.replace("a", "-alpha").replace("b", "-beta").replace("rc", "-rc").replace(".dev", "dev")
  package_json = json.loads(PACKAGE_JSON.read_text(**ENC))
  package_json["version"] = js_version
  PACKAGE_JSON.write_text(json.dumps(package_json, indent=2), **ENC)


if __name__ == "__main__":
  main()