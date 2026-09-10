# Sunday 7pm Backup + Review — Setup

CLI here can't push phone notifications, but I can leave you a local cron that logs every Sunday 7pm.

Run this once in git-bash:
```
hermes cron create --name humber-sunday-review --schedule "0 19 * * 0" --prompt "Log Humber weekly review: check Humber_FinalYear_Prep/Humber_FinalYear_Tracker.xlsx Deadlines + backup to external drive" 
```

Or just set a phone alarm: **Sundays 19:00 — 30 min: backup drive + fill tracker + pick 3 MUSTS for Monday**

Checklist for that slot:
- [ ] External drive + Drive sync green?
- [ ] Tracker Deadlines filled?
- [ ] 3 MUSTS for Monday picked?
- [ ] 3 screen caps for dailies saved?
