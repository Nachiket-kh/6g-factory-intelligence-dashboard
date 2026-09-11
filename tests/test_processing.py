import app


def test_default_dataset_cleans_and_enriches():
    data = app.enrich_data(app.clean_data(app.load_data("data/Thales_Group_Manufacturing.csv")))
    assert len(data) == 100000
    assert {"Event_Time", "Efficiency_Index", "Network_Stability_Index", "Machine_Health_Score"} <= set(data.columns)
    assert data["Efficiency_Index"].between(0, 100).all()


def test_schema_rejects_invalid_upload():
    assert app.validate_data(app.pd.DataFrame({"Date": ["2025-01-01"]}))


def test_kpis_and_machine_summary_are_dynamic():
    data = app.enrich_data(app.clean_data(app.load_data("data/Thales_Group_Manufacturing.csv"))).head(1000)
    assert 0 <= app.kpis(data)["Factory Health"] <= 100
    assert not app.machine_metrics(data).empty
