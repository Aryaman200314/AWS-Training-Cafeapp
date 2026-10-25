"""Check the standalone launch-template payload against the source files."""

import base64
import io
import tarfile
import unittest

from tools.build_user_data import DEPLOY_FILES, OUTPUT, ROOT, build_script


class DeploymentBundleTests(unittest.TestCase):
    def test_generated_user_data_is_current_and_fits_ec2(self):
        script = OUTPUT.read_bytes()
        self.assertEqual(script, build_script().encode("utf-8"))
        self.assertLessEqual(len(script), 16_384)
        self.assertTrue(script.startswith(b"#!/bin/bash\n"))
        self.assertNotIn(b"\r", script)

    def test_embedded_files_match_project_byte_for_byte(self):
        script = OUTPUT.read_text(encoding="utf-8")
        payload = script.split('--no-same-owner\n', 1)[1].split("\nCLOUD_CAFE_PAYLOAD", 1)[0]
        with tarfile.open(fileobj=io.BytesIO(base64.b64decode(payload)), mode="r:gz") as bundle:
            self.assertCountEqual(bundle.getnames(), DEPLOY_FILES)
            for member in bundle.getmembers():
                with self.subTest(file=member.name):
                    self.assertTrue(member.isfile())
                    self.assertEqual(bundle.extractfile(member).read(), (ROOT / member.name).read_text(encoding="utf-8").encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
