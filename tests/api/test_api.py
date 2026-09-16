from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_companies():
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    assert len(response.json()) == 92


def test_company_details():
    response = client.get("/api/v1/companies/TCS")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "TCS"


def test_company_not_found():
    response = client.get("/api/v1/companies/INVALID")
    assert response.status_code == 404


def test_company_pl():
    response = client.get("/api/v1/companies/TCS/pl")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 12
    assert data[0]["company_id"] == "TCS"


def test_company_bs():
    response = client.get("/api/v1/companies/TCS/bs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 12
    assert data[0]["company_id"] == "TCS"


def test_company_cashflow():
    response = client.get("/api/v1/companies/TCS/cashflow")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 12
    assert data[0]["company_id"] == "TCS"


def test_company_ratios():
    response = client.get("/api/v1/companies/TCS/ratios")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 12
    assert data[0]["company_id"] == "TCS"


def test_tearsheet():
    response = client.get("/api/v1/companies/TCS/tearsheet")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content[:4] == b"%PDF"


def test_screener():
    response = client.get("/api/v1/screener")
    assert response.status_code == 200
    data = response.json()
    assert data["total_companies"] == 92
    assert "results" in data


def test_sectors():
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10


def test_sector_companies():
    response = client.get("/api/v1/sectors/Financials/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 23


def test_peers():
    response = client.get("/api/v1/peers/TCS")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_peer_compare():
    response = client.get("/api/v1/peers/TCS/compare")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_valuation():
    response = client.get("/api/v1/valuation")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 92


def test_market_cap():
    response = client.get("/api/v1/market-cap")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 92
    assert data[0]["year"] == 2024


def test_portfolio_stats():
    response = client.get("/api/v1/portfolio/stats")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5


def test_documents():
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1457
    assert "document_url" in data[0]


def test_documents_by_ticker():
    response = client.get("/api/v1/documents/TCS")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 16
    assert data[0]["company_id"] == "TCS"
