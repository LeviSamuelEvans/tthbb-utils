## Download Level-2 Productions

### Overview
`Sync.py` is a python script that facilitates the parallel downloading of an L2 production from a remote server using rsync. It provides a convenient way to synchronise specific directories and subdirectories between the source and destination locations.

#### Features:
- Utilises rsync for efficient and incremental file synchronization.
- Supports parallel downloading of directories using multithreading.
- Allows specifying bandwidth limit, exclude patterns, and retry options.
- Provides logging functionality to track the progress and status of the downloads.

#### Usage:
Run the script like this:

```
python3 Sync.py --source <source_directory> --destination <destination_directory> [--bwlimit <bandwidth_limit>] [--exclude <exclude_pattern>] [--retry] [--filename <log_filename>]
```
where the run options include:

| Argument        | Description                                                                   |
| --------------- | ----------------------------------------------------------------------------- |
| `--source`      | The source directory on the remote server.                                    |
| `--destination` | The destination directory on the local machine.                               |
| `--bwlimit`     | (Optional) The bandwidth limit for `rsync` in KB/s. Default is 50000.         |
| `--exclude`     | (Optional) The pattern to exclude from `rsync`.                               |
| `--retry`       | (Optional) Flag to enable retrying failed downloads.                          |
| `--filename`    | (Optional) The name of the log file. Default is 'L2_Discriminant_070124.log'. |



#### Extra Information:
##### Making an SSH key
To prevent needing to input your password for every rsync job, you can generate an SSH key. The instruction for doing
this are as follows:

- Generate an SSH key pair on your local machine using the `ssh-keygen` command. This will create a public key and a
  private key, which will be used for authentication.
- Copy your public key to lxplus using the `ssh-copy-id` command. This will add your public key to the `authorized_keys`
  file on the remote server, which will allow you to authenticate using your private key.
  ```
  ssh-copy-id <name_of_key>.pub username@lxplus.cern.ch
  ```
- Test your SSH connection to lxplus using the ssh command. If everything is set up correctly, you should be able to
  connect without entering a password.
  ```
  ssh <username>@lxplus.cern.ch
  ```
- **NOTE**: This can be quite temperamental in my experience. I have found though that first setting up a kerberbos token
  seems to make the behaviour of using the SSH key much more stable. You can do this by:
  ```
  kinit username@CERN.CH
  ```
  - use `klist` to make sure this has worked.