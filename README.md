# Cyber Security CET - AWS Cloud User Guide

**Updated 8th June 2020**


To save computing costs, you may want to use smaller instances when provisioning. You can check out the script versions that provision smaller instances using the following git commands:

```bash
git checkout lite-version
```

This repo contains scripts to provision various aws instances for different labs
utils contains the core functions. 

To run the scripts you need the following to be setup before hand:
1. Install Python 3.6 or later 
2. Install Boto3 (AWS Python SDK) by running the following command: 
   ```
   pip install boto3
   ```
3. Create a credential file in your home directory (e.g. /Users/markk/.aws/credentials on Mac or c:/Users/markk/.aws/credentials on Windows) with the following content:

    ```
    [default]
    aws_access_key_id = YOUR_ACCESS_KEY
    aws_secret_access_key = YOUR_SECRET_KEY
    ```
    **Note**: access and secret keys can be obtained from your administrator
4. Set a default region. This can be done in the configuration file. By default, its location is at /Users/markk/.aws/config on Mac or c:/Users/markk/.aws/config on Windows. 
    ```
    [default]
    region=ap-southeast-1
    output=json
    ```
5. Clone this git repository: 
    ```
    git clone https://github.com/khengkok/cybercet.git
    ```

Assuming you clone the repo to the directory c:\Users\markk\git\cybercet, to run the script, for example to provision the windows server 2016 DC lab, change the git repo directory: 

 ```
 cd c:\Users\markk\git\cybercet 
 python win2016dc_lab_script.py -p 3 -o netinfo.csv 
 ```
    
The command above will provision instances for 3 participants. If the lab needs 3 VMs per participant, then a total of 9 VMs will be provisioned. In the case above, only 1 VM is required per participant, so only 3 VMs will be provisioned. 

You can get help by using the option `-h` or `--help`, e.g. 

```python win2016dc_lab_script.py --help```

To deprovision all the VMs after the lesson, you run the same script with the -d option and specify the csv file you specified earlier in your provisioning, e.g. 

 ```
 python win2016dc_lab_script.py -d netinfo.csv 
 ```

Here are the different scripts for the various labs (based on Wanling's Google Spreadsheet as of 18 April 2020)

|Topic               |Workshop                   |Primary Teaching Staff|Course|VM1|VM2|VM3                     |Scripts_to_use |
|--------------------|---------------------------|----------------------|------|---|---|------------------------|---------------|
|CyberSecurity(CSIT) |All five days              |Tin Aung Win          |CSC   |Win 10|   |                     |Win10-CSC-D345-image.py|
|Cyber Forensics     |Data Acquisition           |Wanling               |CEFP  |Win 10|   |                        |win10_forensic_appsec_script.py|
|Cyber Forensics     |Data Examination           |Wanling               |CEFP  |Win 10|   |                        |win10_forensic_appsec_script.py|
|Malware Analysis    |Lab Setup                  |Wanling               |CEFP  |Win 7 - malware analysis|Win 7 - Gateway|                        |malware_lab_script.py|
|Malware Analysis    |Static and Dynamic Analysis|Wanling               |CEFP  |Win 7 - malware analysis|Win 7 - Gateway|                        |malware_lab_script.py|
|Network Security    |Hack Lab                   |Bala                  |CDF   |Kali 2020|Win 7|Win 7 - Gateway         |hacklab.py     |
|Network Security    |Firewall                   |Bala                  |CEFP  |Cloud pfsense|Win 7|Win 7 - Gateway         |firewall_ids_script.py|
|Network Security    |IDS                        |Bala                  |CEFP  |Cloud pfsense|Win 7|Win 7 - Gateway         |firewall_ids_script.py|
|Network Security    |Firewall                   |Wie Leng              |CDF   |Cloud pfsense|Win 7|Win 7 - Gateway         |firewall_ids_script.py|
|Network Security    |IDS                        |Wie Leng              |CDF   |Cloud pfsense|Win 7|Win 7 - Gateway         |firewall_ids_script.py|
|Application Security|Application Security       |Peck Leng             |CEFP  |Win 10|   |                        |win10_forensic_appsec_script.py|
|Network Security |IIS/SSL |Bala             |CDF  |Win server 2016dc|   |                        |win2016dc_lab_script.py|
|Pen Testing |DNS Zone Transfer |Wie Leng            |CEFP  |Win server 2016|   Kali|                        |dnszonexfer_script.py|
|Pen Testing |Hacking/Password Crack |Wie Leng            |CEFP  |Kali|   Windows 10 gateway| Windows 7                        |hacklab.py|
|Server Security |Audit Events/DoS Alert | Sunny            |CDF  |Win srv 2016|   |   |win2016dc_lab_script.py|
|Server Security |Audit Events/DoS Alert | Sunny            |CEFP  |Win srv 2016|   |   |win2016dc_lab_script.py|
|Server Security |Windows AD Policy | Sunny            |CDF  |Win srv 2016 AD|   |   |win2016AD_lab_script.py (TBD)|
|Server Security |Windows AD Policy | Sunny            |CEFP |Win srv 2016 AD|   |   |win2016AD_lab_script.py (TBD)|
|Server Security |Linux Access Control | Sunny            |CDF  |CentOS|   |   |linux_acl_lab_script.py (TBD)|
|Server Security |Linux Access Control | Sunny            |CDF  |CentOS|   |   |linux_acl_lab_script.py (TBD)|


