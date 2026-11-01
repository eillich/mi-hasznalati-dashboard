"""A felület indítási tesztje a Streamlit saját tesztelőjével (böngésző nélkül)."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

GYOKER = Path(__file__).resolve().parents[1]


def _app():
    at = AppTest.from_file(str(GYOKER / "app.py"), default_timeout=120)
    return at


def test_indul_helyi_pillanatkeppel_api_nelkul():
    at = _app()
    at.run()
    at.sidebar.checkbox[0].uncheck().run()
    assert not at.exception
    assert "helyi pillanatkép" in at.markdown[0].value
    assert not at.error


def test_agazati_adatkeszlet():
    at = _app()
    at.run()
    at.sidebar.checkbox[0].uncheck().run()
    at.sidebar.radio[0].set_value("agazat").run()
    assert not at.exception
    assert "isoc_eb_ain2" in at.markdown[0].value
