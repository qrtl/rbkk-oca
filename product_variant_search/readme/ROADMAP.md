On installation, post_init_hook assigns search_name for up to 20,000 products (hard cap) to avoid
performance issues in huge DBs. The remaining products are processed by a cron job starting
5 minutes later. You need to disable the cron after all of your products are assigned search_name.
