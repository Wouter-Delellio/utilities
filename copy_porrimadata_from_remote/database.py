import sqlite3
import os
from pathlib import Path
import subprocess
import sys


"""
Gets a collection of message ids that are related to the given issue

Args:
    issueid: isue id to get the messages for

Returns:
    A list of message ids
"""
def get_messageids_of_issue(issueid):
    con = sqlite3.connect(os.environ['DB_NAME'])
    cursor = con.cursor()
    result = cursor.execute("""SELECT
                                _msg.id as message_id
                                FROM _issue
                                JOIN issue_messages
                                ON _issue.id = issue_messages.nodeid
                                JOIN _msg
                                ON _msg.id = issue_messages.linkid
                                JOIN __textids
                                ON __textids._class = "msg" AND __textids._itemid = _msg.id
                                WHERE _issue.id = "{}"
                                ORDER by _msg._creation DESC""".format(issueid)
                            )
    
    allresultrows = result.fetchall()
    messageids = [messageid[0] for messageid in allresultrows]
    return messageids


"""
Gets a collection of attachments related to the issue

Args:
    issueid: isue id to get the messages for

Returns:
    A list of file ids
"""
def get_issue_files(issueid):
    con = sqlite3.connect(os.environ['DB_NAME'])
    cursor = con.cursor()
    queryresult = cursor.execute('''SELECT 
                                        _file.id,
                                        _file._name
                                        FROM _issue
                                        JOIN issue_files
                                        ON issue_files.nodeid = _issue.id
                                        JOIN _file
                                        ON _file.id = issue_files.linkid
                                        JOIN _user
                                        ON _user.id = _file._creator
                                        WHERE _issue.id = "{}"'''.format(issueid)
                                )
    result = queryresult.fetchall()
    filelist = [fileid[0] for fileid in result]
    return filelist


# """
# Gets the message file(s) related to the message id

# Args:
#     messageid: message id to get the files for

# Returns:
#     A list of message file ids
# """
# def get_message_files(messageid):
#     con = sqlite3.connect(os.environ['DB_NAME'])
#     cursor = con.cursor()
#     querystring = '''SELECT 
#                     _file.id,
#                     _file._creation as created_at,
#                     _user._realname as created_by
#                     FROM msg_files
#                     JOIN _file
#                     ON _file.id = msg_files.linkid
#                     JOIN _user
#                     ON _user.id = _file._creator
#                     WHERE msg_files.nodeid = "{}"'''.format(messageid)
#     result = cursor.execute(querystring)
#     allresultrows = result.fetchall()
#     messagefiles = [messagefile[0] for messagefile in allresultrows]
#     return messagefiles


# def get_fileids_of_messages(messageids):
#     fileDictionary = {}
#     for messageid in messageids:
#         fileDictionary[messageid] = get_message_files(messageid)
#     return fileDictionary


def copy_messagefiles_with_ids(fileids):
    for fileid in fileids:
        ensuremessagefolder(fileid)
        copymessagefilefromremote(fileid)


def getfoldernamefromid(id):
    if len(str(id)) > 3:
        return str(id)[:-3]
    else:
        return "0"


"""
Copies message file from the remote

Args:
    messageid: message id to get the file for
"""
def copymessagefilefromremote(messageid):
    basepath = os.environ['REMOTE_BASEPATH'] + "/msg/" + getfoldernamefromid(messageid) + "/msg" + str(messageid)
    p = subprocess.Popen(["scp", f"{os.environ['REMOTE_USER']}@{os.environ['REMOTE_SERVER']}:{basepath}", "./brocade/db/files/msg/"+getfoldernamefromid(messageid)])
    sts = os.waitpid(p.pid, 0)


"""
Copies issue file from the remote

Args:
    issueid: issue id to copy attachment for
"""
def copyissuefilefromremote(issueid):
    basepath = os.environ['REMOTE_BASEPATH'] + "/file" + getfoldernamefromid(issueid) + "/file" + str(issueid)
    p = subprocess.Popen(["scp", f"{os.environ['REMOTE_USER']}@{os.environ['REMOTE_SERVER']}:{basepath}", "./brocade/db/files/file/"+getfoldernamefromid(issueid)])
    sts = os.waitpid(p.pid, 0)


"""
Makes sure the destination folder for each attachment file exists and creates it if necessary.
Copies the file from the remote to the destination server

Args:
    ids: issue id to which the attachment is related
"""
def copyattachmentfiles_with_ids(ids):
    for id in ids:
        ensurefilefolder(id)
        copyissuefilefromremote(id)


"""
creates a folder for the messageid in case the folder doesn't yet exist

Args:
    messageid: messageid for folder existance check
"""
def ensuremessagefolder(messageid):
    cwd = Path.cwd()
    if not os.path.exists("./brocade/db/files/msg/"+getfoldernamefromid(messageid)):
        (cwd / "brocade" / "db" / "files" / "msg" / getfoldernamefromid(messageid)).mkdir(parents=True)


"""
creates a folder for the fileid in case the folder doesn't yet exist

Args:
    messageid: messageid for folder existance check
"""
def ensurefilefolder(fileid):
    cwd = Path.cwd()
    if not os.path.exists("./brocade/db/files/file/"+getfoldernamefromid(fileid)):
        (cwd / "brocade" / "db" / "files" / "file" / getfoldernamefromid(fileid)).mkdir(parents=True)


if __name__ == "__main__":
    issueid = sys.argv[1]
    messageids = get_messageids_of_issue(issueid)
    files = get_issue_files(issueid)
    # messagefiles = get_fileids_of_messages(messageids)

    print(f"### found {len(messageids)} messages linked to issue {issueid}")
    print(f"### found {len(files)} attachments linked to issue {issueid}")
    # print("")
    if len(messageids) > 0:
        print("\n### starting download of messages")
        copy_messagefiles_with_ids(messageids)

    if len(files) > 0:
        print("\n### starting download of attachments")
        copyattachmentfiles_with_ids(files)
