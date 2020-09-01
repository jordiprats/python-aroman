#!/usr/bin/env python

from __future__ import print_function

"""
Ansible ROle MANager
"""

import os
import sys
import json
import argparse
from github import Github
from configparser import SafeConfigParser
from distutils.version import LooseVersion

GH_TOKEN = ""
debug = False
write_to = sys.stdout

# TODO: afegir les opcions:
# * truncate-pattern
# * name-prefix=mya.

def eprint(*args, **kwargs):
    global debug
    if debug:
        print(*args, file=sys.stderr, **kwargs)

def printPuppetfileItem(modulename, url, tag):
    global write_to
    # - name: git
    #   src: https://github.com/jordiprats/ansible-git
    #   version: origin/master
    print("- name: "+modulename, file=write_to)
    print("  src: "+url, file=write_to)
    if tag:
        print("  version: "+tag+"\n", file=write_to)
    else:
        print("", file=write_to)

def importRepo(username, reponame, url, version, current_version):
    global debug, GH_TOKEN, write_to
    if debug:
        eprint("repo: "+username+"/"+reponame)
        eprint(str(locals()))

    if not version and current_version and not url:
        # parse current version
        if GH_TOKEN:
            g = Github(GH_TOKEN)
        else:
            g = Github()
        repo = g.get_repo(username+"/"+reponame)

        # TODO: get latest version
        # try:
        #     metadata_json = repo.get_contents("metadata.json").decoded_content
        #     if type(metadata_json) is bytes:
        #         metadata_json_str = metadata_json.decode("utf-8")
        #     elif type(metadata_json) is str:
        #         metadata_json_str = metadata_json

        #     metadata = json.loads(metadata_json_str)

        #     version = metadata['version']
        #     url = repo.clone_url

        # except Exception as e:
        #     eprint("ERROR: retrieving metadata for {}: {}".format(repo.name,str(e)))

    if url:
        printPuppetfileItem(reponame, url, version)
    else:
        try:
            if GH_TOKEN:
                g = Github(GH_TOKEN)
            else:
                g = Github()
            repo = g.get_repo(username+"/"+reponame)
            printPuppetfileItem(reponame, repo.clone_url, version)
        except Exception as e:
            eprint("ERROR: retrieving metadata for {}: {}".format(username+"/"+reponame,str(e)))


def importUser(username, repos, repo_pattern, skip_forked_repos, current_version):
    global debug, GH_TOKEN, write_to
    if debug:
        eprint("user: "+username)
        eprint(str(locals()))

    if GH_TOKEN:
        g = Github(GH_TOKEN)
    else:
        g = Github()

    for repo in g.get_user(username).get_repos():
        if repo_pattern in repo.name:

            if debug:
                eprint("considering: "+repo.name+" - is fork? "+str(repo.fork))

            if skip_forked_repos and repo.fork:
                if debug:
                    eprint("skipping forked repo: {}".format(repo.name))
                continue

            # TODO: get latest version
            # if current_version:
            #     try:
            #         metadata_json = repo.get_contents("metadata.json").decoded_content
            #         if type(metadata_json) is bytes:
            #             metadata_json_str = metadata_json.decode("utf-8")
            #         elif type(metadata_json) is str:
            #             metadata_json_str = metadata_json

            #         metadata = json.loads(metadata_json_str)

            #         printPuppetfileItem(repo.name, repo.clone_url, metadata['version'])
            #     except Exception as e:
            #         eprint("ERROR: retrieving metadata for {}: {}".format(repo.name,str(e)))
            # else:
            #     printPuppetfileItem(repo.name, repo.clone_url, "")

def generatePuppetfile(config_file, write_puppetfile_to=sys.stdout):
    global debug, GH_TOKEN, write_to

    write_to=write_puppetfile_to

    config = SafeConfigParser()
    config.read(config_file)

    try:
        GH_TOKEN = config.get('github', 'token').strip('"').strip("'").strip()
    except:
        GH_TOKEN = ""

    try:
        debug = config.getboolean('github', 'debug')
    except:
        debug = False

    for section in config.sections():
        if section!="github":
            try:
                version = config.get(section, 'version').strip('"').strip("'").strip()
            except:
                version = ""

            try:
                current_version = config.getboolean(section, 'current-version')
            except:
                current_version = False

            if "/" in section:
                section_parts = section.split('/')
                username = section_parts[0]
                reponame = section_parts[1]
                try:
                    url = config.get(section, 'url').strip('"').strip("'").strip()
                except:
                    url = ""

                importRepo(username, reponame, url, version, current_version)
            else:
                username = section
                repos = []
                try:
                    repo_pattern = config.get(section, 'repo-pattern').strip('"').strip("'").strip()
                except:
                    repo_pattern = ""
                try:
                    skip_forked_repos = config.getboolean(section, 'skip-forked-repos')
                except:
                    skip_forked_repos = False

                importUser(username, repos, repo_pattern, skip_forked_repos, current_version)


if __name__ == '__main__':
    try:
        config_file = sys.argv[1]
    except IndexError:
        config_file = './aroman.config'
    generatePuppetfile(config_file=config_file)
