"""Run the existing dashboard against disposable, clearly synthetic fixtures."""

import argparse
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT = Path(__file__).resolve().parents[2] / "practice_04/vkusvill-collections"
sys.path.insert(0, str(PROJECT))

from fastapi.testclient import TestClient
import uvicorn

from app.main import create_app
from tests.conftest import make_collection


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8015)
    args = parser.parse_args()
    with TemporaryDirectory(prefix="itmo-search-demo-") as directory:
        app = create_app(Path(directory) / "collections.db")
        with TestClient(app) as client:
            for title, category in [("Тест: Завтрак на двоих", "Завтраки"),
                                    ("Тест: Завтрак в дорогу", "Пикник"),
                                    ("Тест: Ужин дома", "Ужины")]:
                response = client.post("/api/collections", json=make_collection(title=title, category=category))
                assert response.status_code == 201, response.text
        print("Synthetic test data only; production data/ is untouched.", flush=True)
        uvicorn.run(app, host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
