# Database

The schema follows the supplied data definition for `USER`, `File_Metadata`, `USER_SETTINGS`, `MESSAGES`, `TEMP_MESSAGES`, and `BLACKLIST`.

`MESSAGES` includes `subject` and `folder` as implementation fields required by the mail UI. `TEMP_MESSAGES` includes `subject` and `created_at` for draft listing.

Initialize the local development database with:

```bash
python3 -m mail_client.database.init_db
```
