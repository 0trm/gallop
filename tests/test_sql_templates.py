from pathlib import Path
from string import Template

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"

PARAMS = {
    "table": "analytics.experiment_units",
    "unit_column": "user_id",
    "arm_column": "arm",
    "metric_column": "activated",
    "pre_metric_column": "activated_pre",
    "exposure_event": "saw_new_checkout",
}


def test_templates_substitute_fully_with_stdlib_template():
    paths = sorted(SQL_DIR.glob("*.sql.tmpl"))
    assert {p.name for p in paths} == {
        "assignment_counts.sql.tmpl", "exposure_counts.sql.tmpl", "primary_metric.sql.tmpl"}
    for p in paths:
        rendered = Template(p.read_text()).substitute(PARAMS)
        assert "$" not in rendered, f"{p.name} has an unsubstituted placeholder"
        assert rendered.strip().startswith("--")
