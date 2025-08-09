## Requirements (knowledge):
- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Git](https://git-scm.com/)

## Initial Setup:
1. **Clone the Repositories**  
Clone the main server repository and the maps repository:
```bash
git clone https://github.com/savage-drx/savage-drx-server-public.git
git clone https://github.com/savage-drx/savage-drx-maps.git
```
Rename `savage-drx-server-public` to `savage-drx-server`

Ensure that both `savage-drx-server` and `savage-drx-maps` are located at the same directory level.  
Verify that the `world` symlink in the server project correctly points to the `maps` repository:
```bash
world -> ../../savage-drx-maps/
```

2. **Register Your Server**  
Go to https://savagedrx.com/user/servers and register your server.  
> Note: This functionality is available only for users in the `USER_REGULAR` group. New users are assigned to the `USER_NEWCOMER` group by default.

3. **Configure Your Server**  
Update `config.ini` with your credentials
- `sv_authid` your server ID from the registration step
- `sv_authtoken` your server token
- `svr_hostname` your public IP address or hostname  

4. **Optional settings**:  
- `svr_broadcast` set to `1` to make your server visible in the global server list. This is optional for local or testing servers.  
- `svr_name` set your server name.  
- `sv_motd1` to `sv_motd6` set your message of the day lines.  
-  any other additional configuration values as needed.

5. **Start the Server**  
Use the provided `start_server.sh` script to launch your server.  
You can leave or remove the detached mode with a `-d` flag for `docker compose`:
```bash
docker compose -f ${DOCKER_PATH}/docker-compose-main.yml --env-file ${DOCKER_PATH}/.env-main up -d
```

6. **Running Alternative Game Modes**  
   Edit `start_server.sh` and swap `docker-compose-main.yml` with `docker-compose-duels.yml` or `docker-compose-instagib.yml` if you want to run different mods.  


7. **Accessing Logs and Config Files**  
Server logs and temporary configuration files will be available in the `/drx` directory (by default).

