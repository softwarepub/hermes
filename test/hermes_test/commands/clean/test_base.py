import argparse
import logging

from hermes.commands import HermesCleanCommand


def test_clean_base(tmp_path, caplog):
    caplog.set_level(logging.DEBUG)
    parser = argparse.ArgumentParser()
    cmd = HermesCleanCommand(parser)
    ns = argparse.Namespace()
    d = tmp_path / ".hermes"
    d.mkdir()
    assert d.exists()
    ns.__init__(path=tmp_path)
    cmd.__call__(ns)
    assert not d.exists()
    assert caplog.record_tuples[0][2] == "Removing HERMES caches..."
