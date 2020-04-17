# cybercet

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

You can get help by using the option -h or --help, e.g. python win2016dc_lab_script.py --help


