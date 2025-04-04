import os
import configparser
import sys

class MyConfig:
    def __init__(self, config_file="config.ini"):
        self._configFile = config_file
        self.config = configparser.ConfigParser()
        self.config.optionxform = str  # ← Preserve case
        self.config.read(config_file)
        
    def reload(self):
        self.config = configparser.ConfigParser()
        self.config.optionxform = str  # ← Preserve case
        self.config.read(self.config_file)

    @property
    def config_file(self):
        return self._configFile

    def get(self, section, key, fallback=None):
        return self.config.get(section, key, fallback=fallback)

    def getint(self, section, key, fallback=0):
        return self.config.getint(section, key, fallback=fallback)

    def getboolean(self, section, key, fallback=False):
        return self.config.getboolean(section, key, fallback=fallback)

    def set(self, section, key, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))

    def save(self):
        with open(self.config_file, "w") as configfile:
            self.config.write(configfile)

    def fetchOP25Settings(self):
        result = {
            "OP25": dict(self.config.items("OP25")) if self.config.has_section("OP25") else {},
            "ENABLED": dict(self.config.items("ENABLED")) if self.config.has_section("ENABLED") else {}
        }
        return result

    def updateOP25Settings(self, new_settings):
        for section in ["OP25", "ENABLED"]:
            if section in new_settings:
                for key, value in new_settings[section].items():
                    self.set(section, key, value)
        self.save()
        self.reload()
        
    def update(self, data):
        for section, values in data.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            for key, value in values.items():
                self.config.set(section, key, str(value))
        self.save()
        self.reload()

    def build_command(self):
        c = self.config
        if not c.has_section("ENABLED"):
            return []

        enabled = lambda k: c.getboolean("ENABLED", k, fallback=False)
        value = lambda k: c.get("OP25", k, fallback=None)

        cmd = ["python3", "rx.py"]

        if enabled("nocrypt"):
            cmd.append("--nocrypt")
        if enabled("device_args") and value("device_args"):
            cmd += ["--args", value("device_args")]
        if enabled("gain") and value("gain"):
            cmd += ["--gains", f"lna:{value('gain')}"]
        if enabled("sample_rate") and value("sample_rate"):
            cmd += ["-S", value("sample_rate")]
        if enabled("ppm") and value("ppm"):
            cmd += ["-q", value("ppm")]
        if enabled("verbosity") and value("verbosity"):
            cmd += ["-v", value("verbosity")]
        if enabled("audio_output") and value("audio_output") == "alsa":
            cmd.append("-2")
        if enabled("audio_output") and value("audio_output") == "udp":
            cmd.append("-U")
        if enabled("audio_device") and value("audio_device"):
            cmd += ["--audio-dev", value("audio_device")]
        if enabled("log_limit") and value("log_limit"):
            cmd += ["-l", value("log_limit")]
        if enabled("trunk_tsv") and value("trunk_tsv"):
            cmd += ["-T", value("trunk_tsv")]

        return cmd

    def get_log_files(self):
        stdout_file = self.get("OP25", "stdout_file", fallback="stdout.log")
        stderr_file = self.get("OP25", "stderr_file", fallback="stderr.log")
        return stdout_file, stderr_file

    def toJson(self):
        self.reload() # TEMPORARILY FIXES BUG WHERE self.configManager.toJson() returns nothing
        result = {}
        for section in self.config.sections():
            result[section] = {}
            for key in self.config[section]:
                result[section][key] = self.config[section][key]
        return result