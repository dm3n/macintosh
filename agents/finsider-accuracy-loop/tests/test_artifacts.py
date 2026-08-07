import os
import plistlib
import stat
import subprocess
import tempfile
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLIST = os.path.join(ROOT, "com.finsider.accuracy-loop.plist")
INSTALLER = os.path.join(ROOT, "install.sh")


class RuntimeArtifactTests(unittest.TestCase):
    def test_launchd_is_persistent_but_does_not_restart_clean_completion(self):
        with open(PLIST, "rb") as plist_file:
            config = plistlib.load(plist_file)

        self.assertNotIn("StartInterval", config)
        self.assertTrue(config["RunAtLoad"])
        self.assertEqual(config["KeepAlive"], {"SuccessfulExit": False})
        self.assertEqual(config["ThrottleInterval"], 30)
        self.assertTrue(config["ProgramArguments"][1].endswith("finsider-accuracy-loop/run.py"))

    def test_plist_and_installer_parse(self):
        plist = subprocess.run(["plutil", "-lint", PLIST], text=True, capture_output=True)
        shell = subprocess.run(["bash", "-n", INSTALLER], text=True, capture_output=True)

        self.assertEqual(plist.returncode, 0, plist.stderr)
        self.assertEqual(shell.returncode, 0, shell.stderr)

    def test_non_mutating_preflight_passes(self):
        result = subprocess.run(
            [INSTALLER, "--check"], text=True, capture_output=True, cwd=ROOT
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("preflight passed", result.stdout)

    def test_activation_refuses_while_legacy_iteration_is_active(self):
        with tempfile.TemporaryDirectory() as directory:
            fake_pgrep = os.path.join(directory, "pgrep")
            with open(fake_pgrep, "w") as executable:
                executable.write("#!/bin/sh\nexit 0\n")
            os.chmod(fake_pgrep, os.stat(fake_pgrep).st_mode | stat.S_IXUSR)
            environment = dict(os.environ)
            environment["PATH"] = directory + os.pathsep + environment["PATH"]
            environment["FINSIDER_ACCURACY_RUNTIME"] = os.path.join(directory, "runtime")
            environment["FINSIDER_LAUNCH_AGENTS_DIR"] = os.path.join(directory, "agents")
            environment["FINSIDER_LOG_DIR"] = os.path.join(directory, "logs")

            result = subprocess.run(
                [INSTALLER, "--activate"],
                text=True,
                capture_output=True,
                cwd=ROOT,
                env=environment,
            )

            self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
            self.assertIn("legacy accuracy process is still active", result.stderr)
            self.assertFalse(os.path.exists(environment["FINSIDER_LAUNCH_AGENTS_DIR"]))


if __name__ == "__main__":
    unittest.main()
