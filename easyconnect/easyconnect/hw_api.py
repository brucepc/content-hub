#!/usr/bin/python
"""
    @file
    The python API for the interface exposed by class connect AP admin.
"""
import subprocess
import logging
    
#
# Each item follow IETF format like below, ref http://en.wikipedia.org/wiki/IETF_language_tag
#    "<primary language tag>" + "-" + "<extended language subtags>"
# 
# where:
#    - primary language tag: 
#      Three lowcase letter language code follow spec ISO 639-2
#        see http://en.wikipedia.org/wiki/List_of_ISO_639-2_codes
#
#    - extended language subtags:
#      Two upper letter country code follow spec ISO 3166-2
#        see http://en.wikipedia.org/wiki/ISO_3166-2
#      or
#      Three digital geographical region code follows spec UN M.49
#        see http://en.wikipedia.org/wiki/UN_M.49
#n
# Note: extended language subtags is optional
#
'''
LANGUAGE_DICT = {
    "0":"eng-US",  # for English (US)
    "1":"spa-ES",  # for Spanish (Spain)
    "2":"spa-419", # for Spanish (Latin America)
    "3":"por-PT",  # for Portuguese (Portugal)
    "4":"por-BR",  # for Portuguese (Brazil)
    "5":"ara",     # for Arabic
    "6":"fra",     # for Frech
    "7":"tur"      # for Turkish
    }
'''

'''
Language dictionary mapped to codes used by Django
'''
DEFAULT_LANGUAGE = 'en'
LANGUAGE_DICT = {
    "0":"en_UK",
    "1":"es",
    "2":"es_AR",
    "3":"pt_PT",
    "4":"pt_BR",
    "5":"ar",
    "6":"fr",
    "7":"tr",
    "8":"zh_CN"
}


class EasyconnectApApi:
    def __init__(self):
        pass

    def _run_cmd(self, cmd_list):
        if len(cmd_list) == 0:
            logging.error("Invalid param")
            return
        print(cmd_list)
        try:
            p = subprocess.Popen(cmd_list,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        except:
            logging.error("Fail to execute the command %s" % " ".join(cmd_list))
            return None

        out, err = p.communicate()
        if len(err) != 0:
            logging.error("Fail to execute the command %s, error is %s" % (" ".join(cmd_list), err))
            return None

        return out.split("\n")

    def get_teacher_account(self):
        ret_lines = self._run_cmd(['objReq', 'account', 'show'])
        username = None
        password = None
        for line in ret_lines:
            line = line.strip()
            if line.startswith("TeacherUsername"):
                username = line.split(":")[1].strip()
            if line.startswith("TeacherPassword"):
                password = line.split(":")[1].strip()
        logging.debug("Success to read teacher account username: %s, password: %s" %
                      (username, password))
        return (username, password)

    def set_teacher_account(self, username, password):
        if len(username) == 0 or len(password) == 0:
            logging.error("Invalid parameters")
            return False

        if self._run_cmd(['objReq', 'account', 'setparam', 'TeacherUsername', username]) == None:
            logging.error("Fail to set teacher account.")
            return False

        if self._run_cmd(['objReq', 'account', 'setparam', 'TeacherPassword', password]) == None:
            logging.error("Fail to set teacher account.")
            return False
        return True

    def reset_teacher_account(self):
        if self._run_cmd(['objReq', 'account', 'setparam', 'TeacherUsername', 'teacher']) == None:
            logging.error("Fail to reset teacher account.")
            return False

        if self._run_cmd(['objReq', 'account', 'setparam', 'TeacherPassword', 'teacher']) == None:
            logging.error("Fail to reset teacher account.")
            return False
        return True

    def get_admin_account(self):
        ret_lines = self._run_cmd(['objReq', 'account', 'show'])
        admin_username = None
        admin_password = None
        for line in ret_lines:
            line = line.strip()
            if line.startswith("AdminUsername"):
                admin_username = line.split(":")[1].strip()
            if line.startswith("AdminPassword"):
                admin_password = line.split(":")[1].strip()
        logging.debug("Success to read admin account username: %s, password: %s" %
                      (admin_username, admin_password))
        return (admin_username, admin_password)

    def get_battery_status(self):
        try:
            f = open("/tmp/batteryLastChargeLevel")
            value_str = f.read().strip()
            f.close()
        except:
            #logging.error("Fail to open the battery status file, trying old location.")
            try:
                f = open("/tmp/batteryStatus")
                value_str = f.read().strip()
                f.close()
            except:
                #logging.error("Fail to open the battery status file.")
                return
        try:
            value = int(value_str)
        except:
            logging.error("Invalid format for /tmp/batteryStatus")
            return None

        if value < 0 or value > 100:
            logging.error("Invalid battery value read from /tmp/batteryStatus or /tmp/batteryLastChargeLevel")
        logging.debug("Success: Read battery status; value %d" % value)
        return value

    def get_ssid(self):
        try:
            f = open("/var/rtl8192c/wlan0/ssid")
            value_str = f.read().strip()
            f.close()
        except:
            logging.error("Fail to open the ssid file")
            return
        return value_str

    def set_ssid(self, ssid_str):
        if len(ssid_str) == 0:
            logging.error("Invalid ssid string")
            return False

        if self._run_cmd(['objReq', 'wlanSsid', 'setparam', '0', 'ssid', ssid_str]) == None:
            logging.error("Fail to set SSID")
            return False
        self._run_cmd(['rcConf', 'restart', 'wireless'])
        self._run_cmd(['rcConf', 'restart', 'dhcps'])
        return True

    #
    # Get internet mode:
    # 0 - internet is turned off
    # 1 - internet is only for content update
    # 2 - full internet access
    #
    def get_internet_mode(self):
        ret_lines = self._run_cmd(['objReq', 'nat', 'show'])
        mode = -1
        for line in ret_lines:
            line = line.strip()
            if line.startswith("networkMode"):
                mode = int(line.split("=")[1].strip())
        if mode == -1:
            logging.error("Fail to get network mode value.")
        else:
            logging.debug("Success to network mode value: %d" % mode)
        return mode

    #
    # Set internet mode:
    # 0 - internet is turned off
    # 1 - internet is only for content update
    # 2 - full internet access
    #
    def set_internet_mode(self, mode):
        if mode < 0 or mode > 2:
            logging.error("Invalid internet mode.")
            return

        self._run_cmd(["objReq", "nat", "setparam", "networkMode", "%d" % mode])
        self._run_cmd(["rcConf", "restart", "firewall"])
        return
   
    #
    # @param on True for enable captive portal feature
    #           False for disable captive portal feature
    #
    def enable_captive_portal(self, on=True):
        if on:
            self._run_cmd(["objReq", "nat", "setParam", "captivePortal 1"])
            self._run_cmd(["rcConf", "restart", "firewall"])
        else:
            self._run_cmd(["objReq", "nat", "setParam", "captivePortal 0"])
            self._run_cmd(["rcConf", "restart", "firewall"])

    #
    # Get system information dictionary
    #
    # @return string dict for system information.
    #  
    def get_sys_info(self):
        ret_dict = {}
        info_lines = self._run_cmd(["objReq", "sys", "show"])
        if info_lines is not None:
            for line in info_lines:
                # skip blane line
                line = line.strip()
                if len(line) == 0:
                    continue
                sep_index = line.find(":")
                # skip line with invalid format
                if sep_index < 0:
                    continue
                key = line[0:sep_index].strip()
                value = line[sep_index + 1:].strip()
                ret_dict[key.lower()] = value
        return ret_dict

    #
    # Get language tag
    #
    # @return the language code follows IETF format ref http://en.wikipedia.org/wiki/IETF_language_tag
    #         <ISO 639-2>
    #         or
    #         <ISO 639-2> - <ISO 3166-2>
    #         or 
    #         <ISO 639-2> - <UN M.49>
    # @retval None fail to get language code
    #
    def get_language_tag(self):
        sys_info = self.get_sys_info()
        if not sys_info.has_key("language"):
            return DEFAULT_LANGUAGE
        if not LANGUAGE_DICT.has_key(sys_info["language"]):
            return None
        return LANGUAGE_DICT[sys_info["language"]]


    def get_exit_code_stdout(self, stdout):
        itemsCount = len(stdout)
        if itemsCount > 0:
            exitItem = stdout[itemsCount -2]
            if exitItem.startswith("Exit Code"):
                code = [int(s) for s in exitItem.split() if s.isdigit()]
                return code[0]
        return

 # Aidan Commented out code below as per request from Bun 01-06-16
    ##
    ## Check whether Study has been enabled or not
    ##
    ## 1 = Started, 2 = Stopped, any number > 10 is an error
    #def get_study_status(self):
    #    response = -1
    #    try:
    #        stdout = self._run_cmd(["kno-service-status-monitor", "study", "status"])
    #        response = self.get_exit_code_stdout(stdout)
    #    except Exception as ex:
    #        logging.error("Failed to get study status: " + ex.message)
    #        return -1

    #    return response
    
    ##
    ## Turn the Study service ON or OFF
    ## 
    ## returns 0 for success
    #def toggle_study(self, turnOn) :
    #    response = -1
    #    try:
    #        if turnOn:
    #            stdout = self._run_cmd(["kno-service-status-monitor", "study", "start"])
    #            study = self.get_exit_code_stdout(stdout)
    #            response = study
    #        else:
    #            stdout = self._run_cmd(["kno-service-status-monitor", "study", "stop"]) 
    #            study = self.get_exit_code_stdout(stdout)
    #            response = study
    #    except Exception as ex:
    #        logging.error("Failed to toggle Study: %s" % ex.message)
    #        return -1

    #    return response

    #
    # Get CAP version
    #
    # 1 = CAP 1, 2 = CAP 2
    #
    def get_cap_version(self):
        ret_lines = self._run_cmd(['objReq', 'sys', 'show'])
        cap_version = None
        majorVersion = None
        if ret_lines is not None:
            for line in ret_lines:
                line = line.strip()
                if line.startswith("firmware"):
                    cap_version = line.split(":")[1].strip()
            logging.debug("Success to read firmware version: %s" % (cap_version))
            majorVersion = cap_version.split(".")[0]
        return (majorVersion)


     #Get the status of the weaved client
    
     #0 = Off, ON > 0
    
    def get_remote_management_status(self):
        ret = -1
        try:
            readfile = open("/etc/weaved/status", "r")
            weaved_status = readfile.readline()
            ret = int(weaved_status)
        except Exception as ex:
            logging.error("Failed to read weaved status: %s" % ex.message)

        logging.debug("Weaved status %s" % (ret))

        return ret


    def invoke_shell_command(self, command):
        sp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        for line in sp.stdout.readlines():
            print line,
        retval = sp.wait()
        return retval


    #Turn Weaved on
    def start_remote_management(self):
   # turn on Weaved
        self.invoke_shell_command('weavedstart.sh')
        self.invoke_shell_command('weavedenablestartup')

    # set status to 1
        writefile = open("/etc/weaved/status", "w")
        writefile.write("1")
        writefile.close()
        status = 1

        return status > 0


    #Turn Weaved off
    def stop_remote_management(self):
    # turn off Weaved
        self.invoke_shell_command('weavedstop.sh')
        self.invoke_shell_command('weaveddisablestartup')

    # set status to 0        
	writefile = open("/etc/weaved/status", "w")
        writefile.write("0")
        writefile.close()

        return
    
    def restore_db(self):        
	writefile = open("srv/easyconnect/restore_db", "w")
        writefile.write("1")
        writefile.close()
	return 1
