"""Job roles do not repeat across industries."""
from app.seeds.jobs_sections_catalog import JOB_SECTIONS


def test_job_roles_do_not_overlap() -> None:
    assert len(JOB_SECTIONS) == 22
    seen: dict[str, str] = {}
    for catalog in JOB_SECTIONS.values():
        roles = [item["label"] for item in catalog["roles"]]
        assert roles
        assert roles[-1].startswith("Друг")
        assert catalog["question"]
        for role in roles:
            assert role not in seen, f"{role} in {seen.get(role)} and {catalog['label']}"
            seen[role] = catalog["label"]
        for group in catalog["filters"]:
            assert group["options"]
    assert seen["Швея"] == "Швейное производство"
    assert seen["Технолог швейного производства"] == "Швейное производство"
    assert seen["Технолог производства"] == "Производство и промышленность"
    assert seen["Директор"] == "Офис и администрация"
    assert seen["Начальник отдела"] == "Офис и администрация"
    assert seen["Начальник производства"] == "Производство и промышленность"
    assert seen["Директор производства"] == "Производство и промышленность"
    assert seen["Администратор гостиницы"] == "Гостиницы, кафе и рестораны"
    assert seen["Медсестра / Медбрат"] == "Медицина и фармацевтика"
    assert seen["Охранник"] == "Охрана и безопасность"
    assert seen["Водитель фуры"] == "Транспорт и логистика"
    assert JOB_SECTIONS["resumes"]["question"] == "В какой сфере ищете работу?"
    medical_filters = {item["label"] for item in JOB_SECTIONS["medical"]["filters"]}
    assert "Работодатель" in medical_filters
    employer = next(
        item for item in JOB_SECTIONS["medical"]["filters"] if item["label"] == "Работодатель"
    )
    labels = [item["label"] for item in employer["options"]]
    assert "Частный мастер" not in labels
    assert "Клиника" in labels
