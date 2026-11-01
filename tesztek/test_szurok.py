"""A szűrők felületi tesztjei a Streamlit tesztelőjével (böngésző nélkül)."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def indit():
    at = AppTest.from_file(APP, default_timeout=180)
    at.run()
    at.sidebar.checkbox[0].uncheck().run()  # élő letöltés ki: a pillanatképből dolgozunk
    return at


def szoveg(at) -> str:
    return " ".join(m.value for m in at.markdown) + " " + " ".join(
        f"{m.label} {m.value}" for m in at.metric)


def test_alapertekek():
    at = indit()
    assert not at.exception
    assert "Magyarország, 2025 10,4%" in szoveg(at)
    assert "EU-27 átlag, 2025 19,9%" in szoveg(at)


def test_ev_es_orszag_valtasa():
    at = indit()
    at.sidebar.select_slider[0].set_value(2021).run()
    at.sidebar.selectbox(key="kiemelt").set_value("AT").run()
    assert not at.exception
    assert "Ausztria, 2021" in szoveg(at)


def test_mutato_valtasa_csak_letezo_evek():
    at = indit()
    at.sidebar.selectbox[0].set_value("E_AI_BLEG").run()  # 2023-tól kérdezték
    assert not at.exception
    assert at.sidebar.select_slider[0].options == ["2023", "2024", "2025"]
    assert "Magyarország, 2025 51,3%" in szoveg(at)


def test_tobb_orszag_osszevetese():
    at = indit()
    at.sidebar.multiselect[0].set_value(["EU27_2020", "AT", "SK"]).run()
    assert not at.exception


def test_agazat_szures():
    at = indit()
    at.sidebar.radio[0].set_value("agazat").run()
    at.sidebar.selectbox[1].set_value("M69-M71").run()
    assert not at.exception
    assert "Magyarország, 2025 22,5%" in szoveg(at)
