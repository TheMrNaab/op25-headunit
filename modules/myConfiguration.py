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

    def getUserPath(self, section, key):
        print("Getting User Path (section, key): " , section, key)
        return self.config.get(section, key, fallback=None).replace("~", os.path.expanduser("~"))

    def getOP25Properties(self, name, defaultNameVal: str):
        # ADD PROPERTIES IF THEY DO NOT EXIST.
        if self.get("ENABLED", name, fallback=None) is None:
            print(f"[INFO] Bool Property {name} not found in OP25 setting default value: {name} false")
            self.set("ENABLED", name, False)
        if self.get("OP25", name, fallback=None) is None:
            print(f"[INFO] Property {name} not found in OP25, setting default value: {name} = {defaultNameVal}")
            self.set("OP25", name, defaultNameVal)
            
        return self.get("ENABLED", name), self.get("OP25", name)

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
        
    def buildCommandV2(self, trunk_config_path):
        builder = op25CommandBuilder(trunk_config_path, self)
        cmd = builder.buildCommand()
        return cmd

    def build_command(self, trunk_config_path):
        cmd = [sys.executable, self.getUserPath("paths", "rx_script")]
        
        c = self.config
        
        if not c.has_section("ENABLED"):
            return []

        enabled = lambda k: c.getboolean("ENABLED", k, fallback=False)
        value = lambda k: c.get("OP25", k, fallback=None)

        # ADD THE TRUNK CONFIG FILE AND OTHER OPTIONS
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
        if enabled("http_port") and value("http_port"):
            cmd += ["-l", value("http_port")]
        if enabled("trunk_tsv") and value("trunk_tsv"):
            cmd += ["-T", trunk_config_path]

        return cmd

    def get_log_files(self):
        stdout_file = self.get("OP25", "stdout_file", fallback="stdout.log")
        stderr_file = self.get("OP25", "stderr_file", fallback="stderr.log")
        return stdout_file, stderr_file

    def toJson(self):
         # Ensure the configuration is loaded
        if not self.config.sections():  # Check if config is empty
            self.reload()  # Reload only if necessary
        result = {}
        
        for section in self.config.sections():
            result[section] = {}
            for key in self.config[section]:
                result[section][key] = self.config[section][key]
        
        
        return result
    
class op25CommandBuilder():
    def __init__(self, rxScript, _configManager):
        self._rx_script = rxScript
        self._configManager = _configManager
     
    def buildCommand(self):
        cmd = [self.rx_script]

        # Append optional parameters based on configManager flags
        cmd += [self.NOCRYPT()]
        cmd += [self.ARGS()]
        cmd += [self.GAINS()]
        cmd += [self.SAMPLE_RATE()]
        cmd += [self.FREQ_CORR()]
        cmd += [self.VERBOSITY()]
        cmd += [self.TDMA()]
        cmd += [self.VOCODER()]
        cmd += [self.UDP_PLAYER()]
        cmd += [self.TERMINAL_PORT()]
        cmd += [self.TRUNK_CONF_FILE()]

        # Filter out empty strings and return the final command list
        return [arg for arg in cmd if arg]

    @property
    def configManager(self):
        return self._configManager
    
    @property
    def rx_script(self):
        return self._rx_script
    
    def ARGS(self): 
        # --args 'rtl'  
        defaultNameVal = "'rtl'"     
        flag, value = self.configManager.getOP25Properties("args", defaultNameVal)         

        
        return f"--args '{value}'" if flag else ""
    
    def VERBOSITY(self):            
        #-v value
        flag, value = self.configManager.getOP25Properties("verbosity", "")
        return f"-v {value}" if flag else ""
    
    def NOCRYPT(self):
        flag, value = self.configManager.getOP25Properties("nocrypt","--nocrypt")
        return "--nocrypt" if flag else ""
    
    def GAINS(self):                
        # --gains 'lna:40'
        flag, value = self.configManager.getOP25Properties("gains", 40)
        return f"--gains 'lna:{value}'" if flag else ""
    
    def SAMPLE_RATE(self):    
        # -S 960000
        flag, value = self.configManager.getOP25Properties("sample_rate", 960000)
        return f"-S {value}" if flag else ""
    
    def FREQ_CORR(self):    
        flag, value = self.configManager.getOP25Properties("ppm", 0)                     
        # -q 0
        return f"-q {value}" if flag else ""
    
    def TRUNK_CONF_FILE(self):   
        flag, value = self.configManager.getOP25Properties("trunk_tsv", "")     
        # -T path
        return f"-T {value}" if flag else ""
    
    def UDP_PLAYER(self):             
        flag, value = self.configManager.getOP25Properties("audio_output", "alsa")
        return "-U" if flag else ""
        
    def TERMINAL_PORT(self):         
        # -l
        # 'curses' or udp port or 'http:host:port'
        flag, value = self.configManager.getOP25Properties("terminal_port", 5000) 
        return f"-l {value}" if flag else ""
    
    def TDMA(self):            
        # -2
        flag, value = self.configManager.getOP25Properties("tdma", -2) 
        return f"{value}" if flag else ""
    
    def VOCODER(self):               
        # -V, --vocoder
        flag, value = self.configManager.getOP25Properties("vocoder", "-V") 
        return f"{value}" if flag else ""
    
    # self.op25_command = [
#     self.rx_script , "--nocrypt", "--args", "rtl",
#     "--gains", "lna:35", "-S", "960000", "-q", "0",
#     "-v", "1", "-2", "-V", "-U",
#     "-T", "/opt/op25-project/templates/_trunk.tsv",

#     "-U", "-l", "5000"
# ]

# CODE I DO NOT WANT TO LOSE
#  echo '{"command": "whitelist", "arg1": 47021, "arg2": 0}' | nc -u 127.0.0.1 5000

# self.op25_command = [
#     self.rx_script, "--nocrypt", "--args", "rtl",
#     "--gains", "lna:40", "-S", "960000", "-q", "0",
#     "-v", "2", "-2", "-V", "-U",
#     "-T", self.session.activeSystem.toTrunkTSV(self.session),
#     "-U", "-l", "5000"
# ]
# self.op25_command = [
#     self.rx_script , "--nocrypt", "--args", "rtl",
#     "--gains", "lna:35", "-S", "960000", "-q", "0",
#     "-v", "1", "-2", "-V", "-U",
#     "-T", "/opt/op25-project/templates/_trunk.tsv",
#     "-U", "-l", "5000"
# ]