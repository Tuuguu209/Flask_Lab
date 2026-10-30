# Flask_Lab

## Google Sheets signup sync

New registrations are saved in the app's local database and appended to the
first tab of the configured Google spreadsheet. Existing registrations are not
backfilled. The admin submissions page links directly to the sheet.

1. Enable the Google Sheets API in Google Cloud and create a service account.
   Download its JSON key and store it outside this project.
2. Share the spreadsheet with the service account's email address and grant
   Editor access.
3. Install the project dependencies with `pip install -r requirements.txt`.
4. Set `GOOGLE_APPLICATION_CREDENTIALS` to the JSON key's absolute path before
   starting the Flask app. For PowerShell:

   ```powershell
   $env:GOOGLE_APPLICATION_CREDENTIALS = "C:\secure\service-account.json"
   ```

The spreadsheet ID defaults to the sheet linked for this project. To use a
different spreadsheet, set `GOOGLE_SHEETS_SPREADSHEET_ID`. If the first tab is
empty, the app adds column headings when the first signup is submitted.

If Google Sheets is unavailable or not configured, the registration is still
saved locally and the signup page displays a warning.
