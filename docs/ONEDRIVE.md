# Copying activity scans to OneDrive

The bench copies every project's activity-scan results (MaxWell pages, pictures,
summaries) to a OneDrive folder, and keeps them in the results folder as well.

- It copies after every finished activity scan, and every half hour to catch up
  (older dates, or anything a failed copy missed).
- Only new or changed files are sent.
- Nothing is ever deleted or moved, on either side. A file removed from the
  results folder stays on OneDrive, and files people add on OneDrive stay.
- Logs are not copied.

On OneDrive the layout mirrors the results folder:

    <OneDrive folder>/<project>/ActivityScan/<date>/<chip>/<run>/...

The copy is made with [rclone](https://rclone.org/onedrive/). The OneDrive
login is kept in rclone's own settings file, not by the bench.

## One-time setup

Do this on the computer that runs the bench, logged in as the account that runs
it (on labtower1: `s-user-b`).

### 1. Sign rclone in to OneDrive

Run `rclone config` and answer:

| Question | Answer |
|---|---|
| New remote | `n` |
| name | `onedrive` |
| Storage | `onedrive` |
| client_id, client_secret | press Enter (leave blank) |
| region | `1` (Microsoft Cloud Global) |
| Edit advanced config | `n` |
| Use web browser to automatically authenticate | see below |

**At the computer's own screen:** answer `y`. A browser opens. Sign in with your
UC Davis account.

**Over SSH:** first connect with a tunnel, so the sign-in page opens on your own
computer:

    ssh -L 53682:localhost:53682 s-user-b@10.157.209.11

Then run `rclone config`, answer `y`, and open the `http://127.0.0.1:53682/auth?...`
link it prints in your own browser.

After you sign in, rclone asks which drive to use. Choose
`OneDrive Personal or Business`, pick your OneDrive, confirm with `y`, and quit
with `q`.

If Microsoft says the app **needs admin approval**, UC Davis IT has to approve
"rclone" for the campus account first.

Check that it works:

    rclone lsd onedrive:

This lists the folders in your OneDrive.

### 2. Make the lab folder reachable

If the lab folder was shared with you, open OneDrive in the browser, find the
folder under **Shared**, and choose **Add shortcut to My files**. It then shows up
in `rclone lsd onedrive:`.

If the lab folder is a SharePoint or Teams library instead, run `rclone config`
again and make a second remote (for example `labsite`). At the drive question,
choose the SharePoint site, then use `labsite:` below.

### 3. Point the bench at it

In the bench, go to **Settings → Copy to OneDrive**.

1. Type the folder, for example `onedrive:Ben-Shalom Lab/MEA activity scans`.
2. Press **Check**.
3. Press **Use this folder**.

The first copy starts right away and sends everything there already. After that,
only new results are sent.

## Notes

- The login is stored in `~/.config/rclone/rclone.conf`. Never paste it into
  chat or email.
- Microsoft keeps the login alive while it is used. The half-hourly copy uses it,
  so the login only expires if the bench is off for about three months. If that
  happens, the bench shows the error under **Needs attention**; run
  `rclone config reconnect onedrive:` to sign in again.
- If a copy fails, it is shown under **Needs attention** on the Dashboard and in
  Settings, and it is tried again within half an hour.
