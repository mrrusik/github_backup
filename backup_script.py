import os
import sys
import re
import json
import requests
from subprocess import PIPE, run

# - обвязать проверками склонилась репо или нет
# - смогло push’нуть или нет
# - сомгло создать диру или нет
# - нотификация в слак


cwd = os.getcwd()
webhook_url = '***'
GH_repo = "***" #Github repo uri. Which need backup
BB_repo = "***" #Bitbucket repository url

def out(command):
    result = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)
    return result.stderr

def send_error(slack_data):
    global webhook_url
    response = requests.post(
        webhook_url, data=json.dumps(slack_data),
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )

def main():
    global github_project_folder


    def send_to_slack(strerror):


        re_strerror = re.search('(fatal.*$)', strerror)[1]
        print ("Oops! error -> " + strerror)
        slack_data = {"text" : "Oops! error -> " + re_strerror}
        send_error(slack_data)

        try:
            if os.path.isdir(cwd + "/"+ github_project_folder):
                os.system('rm -rf ' + cwd + "/"+ github_project_folder)
            if os.path.isdir(cwd + "/"+ bb_project_folder):
                os.system('rm -rf ' + cwd + "/"+ bb_project_folder)
        finally:
            exit(1)


    #GIT CLONE REPOSITORIES
    git_clone = out("git clone --mirror "+ GH_repo)
    if 'fatal' in git_clone:
        send_to_slack(git_clone)
    else:
        github_project_folder = re.search('^.*\/(\w+\.git$)', GH_repo)[1]


    git_clone = out("git clone --mirror " + BB_repo)
    if ('not found' in git_clone or 'fatal' in git_clone):
        send_to_slack(git_clone)
    else:
        bb_project_folder = re.search('^.*\/(\w+\.git$)', BB_repo)[1]
        os.chdir(bb_project_folder)
        #Clean Bitbucket repo
        os.system('git rm -r *')
        os.system('git add .')
        os.system('git commit -m "delete"')
        os.system('git push --mirror')
        os.chdir(cwd)


    #Pull github and push to bitbucket
    os.chdir(github_project_folder)
    os.system('git fetch --all')
    os.system('git remote add NEW-REMOTE ' + BB_repo)

    push = out("git push " + BB_repo +" --mirror")
    # push = out("git push https://Genesis_test@bitbucket.org/Genesis_test/test77.git --mirror")
    if 'fatal' in push:
        send_to_slack(push)

    os.chdir(cwd)
    os.system('rm -rf ' + github_project_folder)
    os.system('rm -rf ' + bb_project_folder)

    print('SUCCESS')

if __name__ == "__main__":
    main()
